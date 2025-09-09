"""NVIDIA TensorRT optimized Stable Diffusion 3.5 implementation wrapper."""

import os
import sys
import subprocess
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Literal, Union, Tuple
import time
import json

try:
    import torch
    import numpy as np
    from PIL import Image
    import tensorrt as trt
    import onnx
    from polygraphy import cuda
    NVIDIA_TENSORRT_AVAILABLE = True
except ImportError:
    NVIDIA_TENSORRT_AVAILABLE = False

from ..config import AppConfig

logger = logging.getLogger(__name__)

PrecisionType = Literal["fp16", "bf16", "fp8", "int8"]
SchedulerType = Literal["dpm", "euler", "euler_a", "ddim"]


class NVIDIAStableDiffusion35:
    """NVIDIA TensorRT optimized Stable Diffusion 3.5 Large implementation."""
    
    def __init__(self, config: AppConfig):
        """Initialize NVIDIA SD3.5 pipeline.
        
        Args:
            config: Application configuration
        """
        if not NVIDIA_TENSORRT_AVAILABLE:
            raise ImportError(
                "NVIDIA TensorRT dependencies not available. "
                "Please install tensorrt, polygraphy, and cuda-python"
            )
        
        self.config = config
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        if self.device == "cpu":
            logger.warning("CUDA not available, falling back to CPU (not recommended)")
        
        # Paths and directories
        self.workspace_dir = Path.cwd()
        self.tensorrt_repo_dir = self.workspace_dir / "TensorRT"
        self.demo_dir = self.tensorrt_repo_dir / "demo" / "Diffusion"
        self.models_cache_dir = Path.home() / ".cache" / "mini_muse" / "tensorrt_models"
        self.engines_dir = self.models_cache_dir / "engines"
        self.onnx_dir = self.models_cache_dir / "onnx"
        
        # Create directories
        self.models_cache_dir.mkdir(parents=True, exist_ok=True)
        self.engines_dir.mkdir(exist_ok=True)
        self.onnx_dir.mkdir(exist_ok=True)
        
        # Model configuration
        self.model_config = {
            "version": "3.5-large",
            "height": config.models.default_height,
            "width": config.models.default_width,
            "batch_size": 1,
            "num_inference_steps": config.video_generation.sd35_steps,
            "guidance_scale": config.video_generation.sd35_guidance_scale,
        }
        
        # TensorRT optimization settings
        self.tensorrt_config = {
            "precision": config.video_generation.default_precision,
            "use_cuda_graph": config.video_generation.use_cuda_graph,
            "static_batch": True,
            "static_shape": True,
            "enable_all_tactics": True,
            "workspace_size": 8 * (1024 ** 3),  # 8GB
        }
        
        # Environment setup
        self._setup_environment()
        
        logger.info(f"NVIDIA SD3.5 initialized - Device: {self.device}, Precision: {self.tensorrt_config['precision']}")
    
    def _setup_environment(self):
        """Setup environment variables for TensorRT."""
        os.environ.update({
            "CUDA_VISIBLE_DEVICES": "0",
            "TRT_LOGGER_VERBOSITY": "2",  # WARNING level
            "TOKENIZERS_PARALLELISM": "false",
            "CUDA_LAUNCH_BLOCKING": "0",
        })
        
        if self.config.video_generation.hf_token:
            os.environ["HF_TOKEN"] = self.config.video_generation.hf_token
    
    def clone_tensorrt_repo(self) -> bool:
        """Clone NVIDIA TensorRT repository if not exists.
        
        Returns:
            True if repository is available, False otherwise
        """
        if self.tensorrt_repo_dir.exists() and (self.tensorrt_repo_dir / "demo" / "Diffusion").exists():
            logger.info("TensorRT repository already exists")
            return True
        
        try:
            logger.info("Cloning NVIDIA TensorRT repository...")
            cmd = [
                "git", "clone", 
                "https://github.com/NVIDIA/TensorRT.git",
                str(self.tensorrt_repo_dir)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.workspace_dir)
            if result.returncode != 0:
                logger.error(f"Failed to clone TensorRT repo: {result.stderr}")
                return False
            
            # Checkout specific branch for SD3.5 support
            checkout_cmd = ["git", "checkout", "release/sd35"]
            result = subprocess.run(checkout_cmd, capture_output=True, text=True, cwd=self.tensorrt_repo_dir)
            
            if result.returncode != 0:
                logger.warning(f"Failed to checkout sd35 branch: {result.stderr}")
                # Continue with main branch
            
            logger.info("TensorRT repository cloned successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error cloning TensorRT repository: {e}")
            return False
    
    def install_demo_dependencies(self) -> bool:
        """Install TensorRT demo dependencies.
        
        Returns:
            True if installation successful, False otherwise
        """
        if not self.demo_dir.exists():
            logger.error("TensorRT demo directory not found")
            return False
        
        try:
            logger.info("Installing TensorRT demo dependencies...")
            requirements_file = self.demo_dir / "requirements.txt"
            
            if requirements_file.exists():
                cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Failed to install demo dependencies: {result.stderr}")
                    return False
            
            # Install additional TensorRT packages
            tensorrt_cmd = [
                sys.executable, "-m", "pip", "install",
                "--pre", "--upgrade",
                "--extra-index-url", "https://pypi.nvidia.com",
                "tensorrt-cu12"
            ]
            
            result = subprocess.run(tensorrt_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning(f"TensorRT installation warning: {result.stderr}")
            
            logger.info("Demo dependencies installed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error installing demo dependencies: {e}")
            return False
    
    def build_tensorrt_engines(self, 
                              force_rebuild: bool = False,
                              precision: Optional[PrecisionType] = None) -> bool:
        """Build TensorRT engines for SD3.5 models.
        
        Args:
            force_rebuild: Force rebuild even if engines exist
            precision: Override precision setting
            
        Returns:
            True if engines built successfully, False otherwise
        """
        precision = precision or self.tensorrt_config["precision"]
        
        # Check if engines already exist
        engine_pattern = f"sd35_*_{precision}.engine"
        existing_engines = list(self.engines_dir.glob(engine_pattern))
        
        if existing_engines and not force_rebuild:
            logger.info(f"TensorRT engines already exist: {len(existing_engines)} found")
            return True
        
        if not self.demo_dir.exists():
            logger.error("TensorRT demo directory not found. Run clone_tensorrt_repo() first.")
            return False
        
        try:
            logger.info(f"Building TensorRT engines with {precision} precision...")
            
            # Build command for SD3.5
            cmd = [
                sys.executable, "demo_txt2img_sd35.py",
                "A test prompt for engine building",
                f"--version={self.model_config['version']}",
                f"--height={self.model_config['height']}",
                f"--width={self.model_config['width']}",
                f"--denoising-steps={self.model_config['num_inference_steps']}",
                f"--guidance-scale={self.model_config['guidance_scale']}",
                "--build-static-batch",
                "--build-dynamic-batch",
                "--build-all-tactics",
                f"--engine-dir={self.engines_dir}",
                f"--onnx-dir={self.onnx_dir}",
                "--download-onnx-models",
            ]
            
            # Add precision-specific flags
            if precision == "fp8":
                cmd.extend(["--fp8"])
            elif precision == "bf16":
                cmd.extend(["--bf16"])
            elif precision == "fp16":
                cmd.extend(["--fp16"])
            elif precision == "int8":
                cmd.extend(["--int8"])
            
            # Add CUDA graph if enabled
            if self.tensorrt_config["use_cuda_graph"]:
                cmd.extend(["--use-cuda-graph"])
            
            # Set HuggingFace token if available
            if self.config.video_generation.hf_token:
                cmd.extend([f"--hf-token={self.config.video_generation.hf_token}"])
            
            logger.info(f"Executing build command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=self.demo_dir,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Engine build failed: {result.stderr}")
                logger.error(f"Stdout: {result.stdout}")
                return False
            
            logger.info("TensorRT engines built successfully")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Engine build timed out (1 hour limit)")
            return False
        except Exception as e:
            logger.error(f"Error building TensorRT engines: {e}")
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
                           output_path: Optional[Path] = None) -> Path:
        """Generate image using NVIDIA TensorRT optimized SD3.5.
        
        Args:
            prompt: Text prompt for generation
            negative_prompt: Negative prompt
            seed: Random seed
            num_inference_steps: Number of denoising steps
            guidance_scale: Guidance scale
            height: Image height
            width: Image width
            scheduler: Scheduler type
            output_path: Output path for generated image
            
        Returns:
            Path to generated image
        """
        if not self.demo_dir.exists():
            raise RuntimeError("TensorRT demo not available. Run setup() first.")
        
        # Use config defaults if not specified
        num_inference_steps = num_inference_steps or self.model_config["num_inference_steps"]
        guidance_scale = guidance_scale or self.model_config["guidance_scale"]
        height = height or self.model_config["height"]
        width = width or self.model_config["width"]
        
        # Generate output path if not provided
        if output_path is None:
            timestamp = int(time.time())
            output_path = Path(tempfile.gettempdir()) / f"nvidia_sd35_{timestamp}.png"
        
        # Build generation command
        cmd = [
            sys.executable, "demo_txt2img_sd35.py",
            prompt,
            f"--version={self.model_config['version']}",
            f"--height={height}",
            f"--width={width}",
            f"--denoising-steps={num_inference_steps}",
            f"--guidance-scale={guidance_scale}",
            f"--engine-dir={self.engines_dir}",
            f"--onnx-dir={self.onnx_dir}",
            f"--scheduler={scheduler}",
            f"--output={output_path}",
        ]
        
        # Add optional parameters
        if negative_prompt:
            cmd.extend([f"--negative-prompt={negative_prompt}"])
        
        if seed is not None:
            cmd.extend([f"--seed={seed}"])
        
        # Add precision flag
        precision = self.tensorrt_config["precision"]
        if precision == "fp8":
            cmd.extend(["--fp8"])
        elif precision == "bf16":
            cmd.extend(["--bf16"])
        elif precision == "fp16":
            cmd.extend(["--fp16"])
        
        # Add CUDA graph if enabled
        if self.tensorrt_config["use_cuda_graph"]:
            cmd.extend(["--use-cuda-graph"])
        
        try:
            logger.info(f"Generating image with NVIDIA SD3.5: {prompt[:50]}...")
            start_time = time.time()
            
            # Execute generation command
            result = subprocess.run(
                cmd,
                cwd=self.demo_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            generation_time = time.time() - start_time
            
            if result.returncode != 0:
                logger.error(f"Generation failed: {result.stderr}")
                raise RuntimeError(f"Image generation failed: {result.stderr}")
            
            if not output_path.exists():
                raise RuntimeError("Generated image file not found")
            
            logger.info(f"Image generated successfully in {generation_time:.2f}s: {output_path}")
            return output_path
            
        except subprocess.TimeoutExpired:
            logger.error("Image generation timed out")
            raise RuntimeError("Image generation timed out")
        except Exception as e:
            logger.error(f"Error during image generation: {e}")
            raise RuntimeError(f"Image generation failed: {e}") from e
    
    def generate_controlnet_image(self,
                                 prompt: str,
                                 control_image_path: Path,
                                 controlnet_type: Literal["canny", "depth", "blur"],
                                 **kwargs) -> Path:
        """Generate image with ControlNet guidance.
        
        Args:
            prompt: Text prompt
            control_image_path: Path to control image
            controlnet_type: Type of ControlNet
            **kwargs: Additional generation parameters
            
        Returns:
            Path to generated image
        """
        if not self.demo_dir.exists():
            raise RuntimeError("TensorRT demo not available")
        
        # Extract parameters
        output_path = kwargs.get('output_path')
        if output_path is None:
            timestamp = int(time.time())
            output_path = Path(tempfile.gettempdir()) / f"nvidia_controlnet_{timestamp}.png"
        
        num_inference_steps = kwargs.get('num_inference_steps', self.model_config["num_inference_steps"])
        guidance_scale = kwargs.get('guidance_scale', self.model_config["guidance_scale"])
        
        # Build ControlNet command
        cmd = [
            sys.executable, "demo_controlnet_sd35.py",
            prompt,
            f"--version={self.model_config['version']}",
            f"--controlnet-type={controlnet_type}",
            f"--input-image={control_image_path}",
            f"--denoising-steps={num_inference_steps}",
            f"--guidance-scale={guidance_scale}",
            f"--engine-dir={self.engines_dir}",
            f"--onnx-dir={self.onnx_dir}",
            f"--output={output_path}",
        ]
        
        # Add precision and optimization flags
        precision = self.tensorrt_config["precision"]
        if precision == "fp8":
            cmd.extend(["--fp8"])
        elif precision == "bf16":
            cmd.extend(["--bf16"])
        
        if self.tensorrt_config["use_cuda_graph"]:
            cmd.extend(["--use-cuda-graph"])
        
        try:
            logger.info(f"Generating ControlNet image: {controlnet_type}")
            
            result = subprocess.run(
                cmd,
                cwd=self.demo_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"ControlNet generation failed: {result.stderr}")
            
            if not output_path.exists():
                raise RuntimeError("Generated ControlNet image not found")
            
            logger.info(f"ControlNet image generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"ControlNet generation error: {e}")
            raise RuntimeError(f"ControlNet generation failed: {e}") from e
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about built TensorRT engines.
        
        Returns:
            Dictionary with engine information
        """
        engines = list(self.engines_dir.glob("*.engine"))
        
        engine_info = {
            "engines_dir": str(self.engines_dir),
            "total_engines": len(engines),
            "engines": [],
            "total_size_mb": 0,
        }
        
        for engine_path in engines:
            size_mb = engine_path.stat().st_size / (1024 * 1024)
            engine_info["engines"].append({
                "name": engine_path.name,
                "size_mb": round(size_mb, 2),
                "modified": engine_path.stat().st_mtime,
            })
            engine_info["total_size_mb"] += size_mb
        
        engine_info["total_size_mb"] = round(engine_info["total_size_mb"], 2)
        return engine_info
    
    def cleanup_cache(self):
        """Clean up model cache and temporary files."""
        try:
            logger.info("Cleaning up NVIDIA SD3.5 cache...")
            
            # Clean temporary files
            temp_files = list(Path(tempfile.gettempdir()).glob("nvidia_sd35_*.png"))
            temp_files.extend(list(Path(tempfile.gettempdir()).glob("nvidia_controlnet_*.png")))
            
            for temp_file in temp_files:
                temp_file.unlink(missing_ok=True)
            
            # Optionally clean ONNX cache (if requested)
            # This is commented out as ONNX models are expensive to re-download
            # if cleanup_onnx:
            #     shutil.rmtree(self.onnx_dir, ignore_errors=True)
            #     self.onnx_dir.mkdir(exist_ok=True)
            
            logger.info("Cache cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
    
    async def setup(self, force_rebuild: bool = False) -> bool:
        """Complete setup of NVIDIA SD3.5 pipeline.
        
        Args:
            force_rebuild: Force rebuild of TensorRT engines
            
        Returns:
            True if setup successful, False otherwise
        """
        try:
            # Step 1: Clone TensorRT repository
            if not self.clone_tensorrt_repo():
                logger.error("Failed to clone TensorRT repository")
                return False
            
            # Step 2: Install demo dependencies
            if not self.install_demo_dependencies():
                logger.error("Failed to install demo dependencies")
                return False
            
            # Step 3: Build TensorRT engines
            if not self.build_tensorrt_engines(force_rebuild=force_rebuild):
                logger.error("Failed to build TensorRT engines")
                return False
            
            logger.info("NVIDIA SD3.5 setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current GPU memory usage.
        
        Returns:
            Dictionary with memory usage information
        """
        if not torch.cuda.is_available():
            return {"error": "CUDA not available"}
        
        try:
            memory_allocated = torch.cuda.memory_allocated() / (1024**3)  # GB
            memory_reserved = torch.cuda.memory_reserved() / (1024**3)   # GB
            memory_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
            
            return {
                "allocated_gb": round(memory_allocated, 2),
                "reserved_gb": round(memory_reserved, 2),
                "total_gb": round(memory_total, 2),
                "utilization_percent": round((memory_allocated / memory_total) * 100, 1),
            }
        except Exception as e:
            return {"error": str(e)}


def create_nvidia_sd35(config: AppConfig) -> Optional[NVIDIAStableDiffusion35]:
    """Factory function to create NVIDIA SD3.5 instance.
    
    Args:
        config: Application configuration
        
    Returns:
        NVIDIAStableDiffusion35 instance if available, None otherwise
    """
    try:
        return NVIDIAStableDiffusion35(config)
    except ImportError as e:
        logger.warning(f"NVIDIA SD3.5 not available: {e}")
        return None