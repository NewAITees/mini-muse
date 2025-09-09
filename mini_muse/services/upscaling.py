"""Image upscaling service using Real-ESRGAN and other SR models."""

import os
import logging
from pathlib import Path
from typing import Optional, Literal, Tuple
from PIL import Image
import numpy as np
import torch
import cv2

try:
    from realesrgan import RealESRGANer
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from gfpgan import GFPGANer
    UPSCALING_AVAILABLE = True
except ImportError:
    UPSCALING_AVAILABLE = False

from ..config import AppConfig

logger = logging.getLogger(__name__)

UpscaleModel = Literal["realesrgan-x2plus", "realesrgan-x4plus", "realesrgan-x4plus-anime"]
UpscaleFactor = Literal[2, 4]


class UpscalingService:
    """Service for upscaling images using various super-resolution models."""
    
    def __init__(self, config: AppConfig):
        """Initialize the upscaling service.
        
        Args:
            config: Application configuration
        """
        if not UPSCALING_AVAILABLE:
            raise ImportError(
                "Upscaling dependencies not available. "
                "Install with: pip install basicsr realesrgan gfpgan"
            )
        
        self.config = config
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.models = {}
        self._model_cache_dir = Path.home() / ".cache" / "mini_muse" / "upscaling_models"
        self._model_cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"UpscalingService initialized with device: {self.device}")
    
    def _get_model_path(self, model_name: str) -> Path:
        """Get the path for a model file.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Path to the model file
        """
        model_files = {
            "realesrgan-x2plus": "RealESRGAN_x2plus.pth",
            "realesrgan-x4plus": "RealESRGAN_x4plus.pth",
            "realesrgan-x4plus-anime": "RealESRGAN_x4plus_anime_6B.pth",
        }
        
        if model_name not in model_files:
            raise ValueError(f"Unknown model: {model_name}")
        
        return self._model_cache_dir / model_files[model_name]
    
    def _load_model(self, model_name: UpscaleModel, scale: UpscaleFactor) -> RealESRGANer:
        """Load a Real-ESRGAN model.
        
        Args:
            model_name: Name of the model to load
            scale: Upscaling factor
            
        Returns:
            Loaded RealESRGANer instance
        """
        if model_name in self.models:
            return self.models[model_name]
        
        model_path = self._get_model_path(model_name)
        
        # Model configurations
        model_configs = {
            "realesrgan-x2plus": {
                "num_in_ch": 3,
                "num_out_ch": 3,
                "num_feat": 64,
                "num_block": 23,
                "num_grow_ch": 32,
                "scale": 2,
            },
            "realesrgan-x4plus": {
                "num_in_ch": 3,
                "num_out_ch": 3,
                "num_feat": 64,
                "num_block": 23,
                "num_grow_ch": 32,
                "scale": 4,
            },
            "realesrgan-x4plus-anime": {
                "num_in_ch": 3,
                "num_out_ch": 3,
                "num_feat": 64,
                "num_block": 6,
                "num_grow_ch": 32,
                "scale": 4,
            },
        }
        
        config = model_configs[model_name]
        
        # Create the network
        model = RRDBNet(
            num_in_ch=config["num_in_ch"],
            num_out_ch=config["num_out_ch"],
            num_feat=config["num_feat"],
            num_block=config["num_block"],
            num_grow_ch=config["num_grow_ch"],
            scale=config["scale"],
        )
        
        # Create the upsampler
        upsampler = RealESRGANer(
            scale=scale,
            model_path=str(model_path) if model_path.exists() else None,
            model=model,
            tile=self.config.upscaling.tile_size,
            tile_pad=self.config.upscaling.tile_padding,
            pre_pad=self.config.upscaling.pre_padding,
            half=self.device == "cuda" and self.config.upscaling.use_half_precision,
            device=self.device,
        )
        
        self.models[model_name] = upsampler
        logger.info(f"Loaded model: {model_name} with scale {scale}x")
        
        return upsampler
    
    async def upscale_image(
        self,
        image: Image.Image,
        scale_factor: UpscaleFactor = 4,
        model_name: Optional[UpscaleModel] = None,
        face_enhance: bool = False,
    ) -> Image.Image:
        """Upscale an image using Real-ESRGAN.
        
        Args:
            image: Input PIL image
            scale_factor: Upscaling factor (2 or 4)
            model_name: Specific model to use, auto-detected if None
            face_enhance: Whether to apply face enhancement using GFPGAN
            
        Returns:
            Upscaled PIL image
            
        Raises:
            ValueError: If invalid parameters are provided
            RuntimeError: If upscaling fails
        """
        if not UPSCALING_AVAILABLE:
            raise RuntimeError("Upscaling dependencies not installed")
        
        # Auto-select model if not specified
        if model_name is None:
            if scale_factor == 2:
                model_name = "realesrgan-x2plus"
            else:  # scale_factor == 4
                # Use anime model for images that might be illustrations
                model_name = "realesrgan-x4plus"
        
        logger.info(f"Upscaling image with {model_name} (scale: {scale_factor}x)")
        
        try:
            # Load the model
            upsampler = self._load_model(model_name, scale_factor)
            
            # Convert PIL image to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Perform upscaling
            output, _ = upsampler.enhance(cv_image, outscale=scale_factor)
            
            # Apply face enhancement if requested
            if face_enhance and self.config.upscaling.enable_face_enhancement:
                output = await self._enhance_faces(output)
            
            # Convert back to PIL image
            output_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
            result_image = Image.fromarray(output_rgb)
            
            logger.info(f"Successfully upscaled image from {image.size} to {result_image.size}")
            return result_image
            
        except Exception as e:
            logger.error(f"Failed to upscale image: {e}")
            raise RuntimeError(f"Upscaling failed: {e}") from e
    
    async def _enhance_faces(self, image: np.ndarray) -> np.ndarray:
        """Enhance faces in the image using GFPGAN.
        
        Args:
            image: Input image as numpy array (BGR format)
            
        Returns:
            Face-enhanced image as numpy array
        """
        try:
            # Initialize GFPGAN if not already done
            if not hasattr(self, '_face_enhancer'):
                model_path = self._model_cache_dir / "GFPGANv1.4.pth"
                self._face_enhancer = GFPGANer(
                    model_path=str(model_path) if model_path.exists() else None,
                    upscale=1,  # Don't upscale, just enhance
                    arch='clean',
                    channel_multiplier=2,
                    bg_upsampler=None,
                    device=self.device
                )
            
            # Enhance faces
            _, _, enhanced_image = self._face_enhancer.enhance(
                image,
                has_aligned=False,
                only_center_face=False,
                paste_back=True
            )
            
            return enhanced_image if enhanced_image is not None else image
            
        except Exception as e:
            logger.warning(f"Face enhancement failed: {e}")
            return image
    
    async def batch_upscale(
        self,
        images: list[Image.Image],
        scale_factor: UpscaleFactor = 4,
        model_name: Optional[UpscaleModel] = None,
        face_enhance: bool = False,
    ) -> list[Image.Image]:
        """Upscale multiple images in batch.
        
        Args:
            images: List of input PIL images
            scale_factor: Upscaling factor (2 or 4)
            model_name: Specific model to use, auto-detected if None
            face_enhance: Whether to apply face enhancement
            
        Returns:
            List of upscaled PIL images
        """
        results = []
        for i, image in enumerate(images):
            logger.info(f"Processing image {i + 1}/{len(images)}")
            upscaled = await self.upscale_image(
                image, scale_factor, model_name, face_enhance
            )
            results.append(upscaled)
        
        return results
    
    def get_available_models(self) -> list[str]:
        """Get list of available upscaling models.
        
        Returns:
            List of model names
        """
        return ["realesrgan-x2plus", "realesrgan-x4plus", "realesrgan-x4plus-anime"]
    
    def estimate_output_size(
        self, input_size: Tuple[int, int], scale_factor: UpscaleFactor
    ) -> Tuple[int, int]:
        """Estimate the output size after upscaling.
        
        Args:
            input_size: Input image size (width, height)
            scale_factor: Upscaling factor
            
        Returns:
            Estimated output size (width, height)
        """
        width, height = input_size
        return (width * scale_factor, height * scale_factor)
    
    def estimate_memory_usage(
        self, input_size: Tuple[int, int], scale_factor: UpscaleFactor
    ) -> float:
        """Estimate memory usage in MB for upscaling.
        
        Args:
            input_size: Input image size (width, height)
            scale_factor: Upscaling factor
            
        Returns:
            Estimated memory usage in MB
        """
        width, height = input_size
        input_pixels = width * height
        output_pixels = input_pixels * (scale_factor ** 2)
        
        # Rough estimate: input + output + model overhead
        # 3 channels, float32 (4 bytes), plus model overhead
        memory_mb = (input_pixels + output_pixels) * 3 * 4 / (1024 * 1024)
        memory_mb += 500  # Model overhead
        
        return memory_mb


def create_upscaling_service(config: AppConfig) -> Optional[UpscalingService]:
    """Factory function to create an upscaling service.
    
    Args:
        config: Application configuration
        
    Returns:
        UpscalingService instance if dependencies are available, None otherwise
    """
    try:
        return UpscalingService(config)
    except ImportError as e:
        logger.warning(f"Upscaling service not available: {e}")
        return None