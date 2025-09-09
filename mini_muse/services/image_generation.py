"""Image generation service using NVIDIA optimized Stable Diffusion 3.5."""

import os
import logging
import time
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Literal, Union
from PIL import Image

from ..config import AppConfig
from .nvidia_sd35 import create_nvidia_sd35, NVIDIAStableDiffusion35

logger = logging.getLogger(__name__)

ControlNetType = Literal["canny", "depth", "blur"]
SchedulerType = Literal["dpm", "euler", "euler_a", "ddim"]


class ImageGenerationService:
    """Primary image generation service using NVIDIA optimized SD3.5."""
    
    def __init__(self, config: AppConfig):
        """Initialize image generation service.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.output_dir = Path(config.user.output_directory).expanduser()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "images").mkdir(exist_ok=True)
        
        # Initialize NVIDIA SD3.5 as primary generator
        self.nvidia_sd35 = create_nvidia_sd35(config)
        self.is_nvidia_available = self.nvidia_sd35 is not None
        
        if not self.is_nvidia_available:
            logger.warning("NVIDIA SD3.5 not available, falling back to alternative implementation")
            # TODO: Add fallback to standard diffusers implementation
        
        logger.info(f"ImageGenerationService initialized - NVIDIA: {'✓' if self.is_nvidia_available else '✗'}")
    
    async def setup(self, force_rebuild: bool = False) -> bool:
        """Setup the image generation service.
        
        Args:
            force_rebuild: Force rebuild of optimized models
            
        Returns:
            True if setup successful, False otherwise
        """
        if self.nvidia_sd35:
            logger.info("Setting up NVIDIA SD3.5 pipeline...")
            success = await self.nvidia_sd35.setup(force_rebuild=force_rebuild)
            if success:
                logger.info("NVIDIA SD3.5 setup completed successfully")
            else:
                logger.error("NVIDIA SD3.5 setup failed")
            return success
        
        logger.warning("No image generation backend available")
        return False
    
    async def generate_image(self,
                           prompt: str,
                           negative_prompt: Optional[str] = None,
                           seed: Optional[int] = None,
                           num_inference_steps: Optional[int] = None,
                           guidance_scale: Optional[float] = None,
                           height: Optional[int] = None,
                           width: Optional[int] = None,
                           scheduler: SchedulerType = "dpm",
                           save_to_outputs: bool = True) -> Dict[str, Any]:
        """Generate image from text prompt.
        
        Args:
            prompt: Text prompt for generation
            negative_prompt: Negative prompt
            seed: Random seed
            num_inference_steps: Number of denoising steps
            guidance_scale: Guidance scale
            height: Image height
            width: Image width
            scheduler: Scheduler type
            save_to_outputs: Save to outputs directory
            
        Returns:
            Dictionary with generation results
        """
        if not self.nvidia_sd35:
            raise RuntimeError("No image generation backend available")
        
        start_time = time.time()
        
        try:
            # Determine output path
            if save_to_outputs:
                timestamp = int(time.time())
                output_path = self.output_dir / "images" / f"generated_{timestamp}.png"
            else:
                output_path = None
            
            # Generate image using NVIDIA SD3.5
            logger.info(f"Generating image: {prompt[:50]}...")
            
            result_path = await self.nvidia_sd35.generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                seed=seed,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                height=height,
                width=width,
                scheduler=scheduler,
                output_path=output_path
            )
            
            # Copy to outputs if needed
            if save_to_outputs and result_path != output_path:
                import shutil
                shutil.copy2(result_path, output_path)
                result_path = output_path
            
            generation_time = time.time() - start_time
            
            # Load image to get dimensions
            image = Image.open(result_path)
            
            result = {
                "image_path": str(result_path),
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "seed": seed,
                "generation_time": generation_time,
                "dimensions": image.size,
                "parameters": {
                    "num_inference_steps": num_inference_steps or self.config.video_generation.sd35_steps,
                    "guidance_scale": guidance_scale or self.config.video_generation.sd35_guidance_scale,
                    "height": height or self.config.models.default_height,
                    "width": width or self.config.models.default_width,
                    "scheduler": scheduler,
                },
                "backend": "nvidia_sd35",
                "precision": self.config.video_generation.default_precision,
            }
            
            logger.info(f"Image generated successfully in {generation_time:.2f}s: {result_path}")
            return result
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise RuntimeError(f"Image generation failed: {e}") from e
    
    async def generate_controlnet_image(self,
                                      prompt: str,
                                      control_image_path: Path,
                                      controlnet_type: ControlNetType,
                                      negative_prompt: Optional[str] = None,
                                      seed: Optional[int] = None,
                                      num_inference_steps: Optional[int] = None,
                                      guidance_scale: Optional[float] = None,
                                      save_to_outputs: bool = True) -> Dict[str, Any]:
        """Generate image with ControlNet guidance.
        
        Args:
            prompt: Text prompt
            control_image_path: Path to control image
            controlnet_type: Type of ControlNet
            negative_prompt: Negative prompt
            seed: Random seed
            num_inference_steps: Number of denoising steps
            guidance_scale: Guidance scale
            save_to_outputs: Save to outputs directory
            
        Returns:
            Dictionary with generation results
        """
        if not self.nvidia_sd35:
            raise RuntimeError("NVIDIA SD3.5 backend not available")
        
        start_time = time.time()
        
        try:
            # Determine output path
            if save_to_outputs:
                timestamp = int(time.time())
                output_path = self.output_dir / "images" / f"controlnet_{controlnet_type}_{timestamp}.png"
            else:
                output_path = None
            
            logger.info(f"Generating ControlNet image ({controlnet_type}): {prompt[:50]}...")
            
            result_path = self.nvidia_sd35.generate_controlnet_image(
                prompt=prompt,
                control_image_path=control_image_path,
                controlnet_type=controlnet_type,
                output_path=output_path,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
            )
            
            # Copy to outputs if needed
            if save_to_outputs and result_path != output_path:
                import shutil
                shutil.copy2(result_path, output_path)
                result_path = output_path
            
            generation_time = time.time() - start_time
            
            # Load image to get dimensions
            image = Image.open(result_path)
            
            result = {
                "image_path": str(result_path),
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "controlnet_type": controlnet_type,
                "control_image_path": str(control_image_path),
                "seed": seed,
                "generation_time": generation_time,
                "dimensions": image.size,
                "parameters": {
                    "num_inference_steps": num_inference_steps or self.config.video_generation.sd35_steps,
                    "guidance_scale": guidance_scale or self.config.video_generation.sd35_guidance_scale,
                },
                "backend": "nvidia_sd35_controlnet",
                "precision": self.config.video_generation.default_precision,
            }
            
            logger.info(f"ControlNet image generated in {generation_time:.2f}s: {result_path}")
            return result
            
        except Exception as e:
            logger.error(f"ControlNet image generation failed: {e}")
            raise RuntimeError(f"ControlNet generation failed: {e}") from e
    
    async def batch_generate(self,
                           prompts: List[str],
                           negative_prompts: Optional[List[str]] = None,
                           seeds: Optional[List[int]] = None,
                           **kwargs) -> List[Dict[str, Any]]:
        """Batch generate multiple images.
        
        Args:
            prompts: List of prompts
            negative_prompts: List of negative prompts
            seeds: List of seeds
            **kwargs: Additional parameters for generation
            
        Returns:
            List of generation results
        """
        results = []
        
        for i, prompt in enumerate(prompts):
            try:
                # Get corresponding parameters for this prompt
                negative_prompt = negative_prompts[i] if negative_prompts and i < len(negative_prompts) else None
                seed = seeds[i] if seeds and i < len(seeds) else None
                
                logger.info(f"Batch generating {i+1}/{len(prompts)}: {prompt[:30]}...")
                
                result = await self.generate_image(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    seed=seed,
                    **kwargs
                )
                
                result["batch_index"] = i
                results.append(result)
                
            except Exception as e:
                logger.error(f"Batch generation failed for prompt {i+1}: {e}")
                results.append({
                    "batch_index": i,
                    "prompt": prompt,
                    "error": str(e),
                    "image_path": None,
                })
        
        successful = sum(1 for r in results if "error" not in r)
        logger.info(f"Batch generation completed: {successful}/{len(results)} successful")
        
        return results
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about TensorRT engines.
        
        Returns:
            Dictionary with engine information
        """
        if self.nvidia_sd35:
            return self.nvidia_sd35.get_engine_info()
        
        return {"error": "NVIDIA SD3.5 not available"}
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current GPU memory usage.
        
        Returns:
            Dictionary with memory usage information
        """
        if self.nvidia_sd35:
            return self.nvidia_sd35.get_memory_usage()
        
        return {"error": "NVIDIA SD3.5 not available"}
    
    def get_supported_features(self) -> Dict[str, bool]:
        """Get supported features.
        
        Returns:
            Dictionary of supported features
        """
        return {
            "text_to_image": self.is_nvidia_available,
            "controlnet_canny": self.is_nvidia_available,
            "controlnet_depth": self.is_nvidia_available,
            "controlnet_blur": self.is_nvidia_available,
            "tensorrt_optimization": self.is_nvidia_available,
            "fp8_precision": self.is_nvidia_available,
            "cuda_graph": self.is_nvidia_available,
            "batch_generation": True,
        }
    
    def cleanup_cache(self):
        """Clean up temporary files and cache."""
        if self.nvidia_sd35:
            self.nvidia_sd35.cleanup_cache()
        
        # Clean temporary image files
        temp_files = list(Path(tempfile.gettempdir()).glob("generated_*.png"))
        for temp_file in temp_files:
            temp_file.unlink(missing_ok=True)
        
        logger.info("Image generation cache cleanup completed")


def create_image_generation_service(config: AppConfig) -> Optional[ImageGenerationService]:
    """Factory function to create image generation service.
    
    Args:
        config: Application configuration
        
    Returns:
        ImageGenerationService instance
    """
    try:
        return ImageGenerationService(config)
    except Exception as e:
        logger.error(f"Failed to create image generation service: {e}")
        return None