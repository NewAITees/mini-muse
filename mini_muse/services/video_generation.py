"""Stable Diffusion 3.5 + SVD 1.1 video generation service with TensorRT optimization."""

import os
import subprocess
import time
import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Literal, Tuple
from PIL import Image
import numpy as np
import cv2

try:
    import torch
    import tensorrt as trt
    import onnx
    import imageio
    import ffmpeg
    VIDEO_GENERATION_AVAILABLE = True
except ImportError:
    VIDEO_GENERATION_AVAILABLE = False

from ..config import AppConfig
from .image_generation import create_image_generation_service, ImageGenerationService

logger = logging.getLogger(__name__)

PrecisionType = Literal["bf16", "fp8"]
ControlNetType = Literal["canny", "depth", "blur"]
VideoModel = Literal["svd-xt-1.1", "svd-1.1"]


class SD35VideoPipeline:
    """Stable Diffusion 3.5 + SVD 1.1 統合パイプライン"""
    
    def __init__(self, config: AppConfig):
        """Initialize the video generation pipeline.
        
        Args:
            config: Application configuration
        """
        if not VIDEO_GENERATION_AVAILABLE:
            raise ImportError(
                "Video generation dependencies not available. "
                "Install with: pip install tensorrt onnx onnxruntime-gpu ffmpeg-python imageio"
            )
        
        self.config = config
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Initialize image generation service (NVIDIA SD3.5)
        self.image_service = create_image_generation_service(config)
        if not self.image_service:
            raise RuntimeError("Image generation service not available")
        
        # Paths
        self.workspace_dir = Path.cwd()
        self.models_dir = Path.home() / ".cache" / "mini_muse" / "video_models"
        self.output_dir = Path(config.user.output_directory).expanduser()
        self.tensorrt_repo_dir = self.workspace_dir / "TensorRT"
        self.demo_dir = self.tensorrt_repo_dir / "demo" / "Diffusion"
        
        # Create directories
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "images").mkdir(exist_ok=True)
        (self.output_dir / "videos").mkdir(exist_ok=True)
        
        logger.info(f"SD35VideoPipeline initialized with NVIDIA SD3.5 + SVD - Device: {self.device}")
    
    def _check_tensorrt_models(self) -> bool:
        """Check if TensorRT models are available."""
        sd35_engine = self.models_dir / "sd35_engine"
        svd_engine = self.models_dir / "svd_engine"
        
        return sd35_engine.exists() and svd_engine.exists()
    
    def _setup_tensorrt_environment(self) -> Dict[str, str]:
        """Setup TensorRT environment variables."""
        env = os.environ.copy()
        env.update({
            "CUDA_VISIBLE_DEVICES": "0",
            "TRT_LOGGER_VERBOSITY": "WARNING",
            "TOKENIZERS_PARALLELISM": "false"
        })
        
        if self.config.video_generation.hf_token:
            env["HF_TOKEN"] = self.config.video_generation.hf_token
        
        return env
    
    async def generate_image(self,
                           prompt: str,
                           precision: PrecisionType = "fp8",
                           controlnet_type: Optional[ControlNetType] = None,
                           control_image: Optional[Path] = None,
                           seed: Optional[int] = None,
                           guidance_scale: Optional[float] = None,
                           num_steps: Optional[int] = None) -> Path:
        """Generate image using NVIDIA optimized Stable Diffusion 3.5.
        
        Args:
            prompt: Generation prompt
            precision: Precision setting ("bf16" or "fp8")
            controlnet_type: ControlNet type ("canny", "depth", "blur")
            control_image: Control image path for ControlNet
            seed: Random seed
            guidance_scale: Guidance scale override
            num_steps: Number of denoising steps override
            
        Returns:
            Path to generated image
        """
        try:
            logger.info(f"Generating image with NVIDIA SD3.5: {prompt[:50]}...")
            
            # Use ControlNet if specified
            if controlnet_type and control_image:
                result = await self.image_service.generate_controlnet_image(
                    prompt=prompt,
                    control_image_path=control_image,
                    controlnet_type=controlnet_type,
                    seed=seed,
                    num_inference_steps=num_steps,
                    guidance_scale=guidance_scale,
                    save_to_outputs=True
                )
            else:
                result = await self.image_service.generate_image(
                    prompt=prompt,
                    seed=seed,
                    num_inference_steps=num_steps,
                    guidance_scale=guidance_scale,
                    save_to_outputs=True
                )
            
            image_path = Path(result["image_path"])
            logger.info(f"Image generated successfully: {image_path}")
            return image_path
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise RuntimeError(f"Image generation failed: {e}") from e
    
    async def setup(self, force_rebuild: bool = False) -> bool:
        """Setup the complete pipeline.
        
        Args:
            force_rebuild: Force rebuild of TensorRT models
            
        Returns:
            True if setup successful, False otherwise
        """
        try:
            # Setup image generation service (NVIDIA SD3.5)
            logger.info("Setting up NVIDIA SD3.5 image generation...")
            image_setup = await self.image_service.setup(force_rebuild=force_rebuild)
            
            if not image_setup:
                logger.error("Failed to setup image generation service")
                return False
            
            # Check if TensorRT demo is available for SVD
            if not self.demo_dir.exists():
                logger.warning("TensorRT demo directory not found. SVD video generation may not be available.")
            
            logger.info("Pipeline setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Pipeline setup failed: {e}")
            return False
    
    async def generate_video(self,
                           input_image: Path,
                           output_name: Optional[str] = None,
                           model_version: VideoModel = "svd-xt-1.1",
                           num_frames: Optional[int] = None,
                           num_steps: Optional[int] = None) -> Path:
        """Generate video using Stable Video Diffusion.
        
        Args:
            input_image: Input image path
            output_name: Output filename
            model_version: SVD model version
            num_frames: Number of frames to generate
            num_steps: Number of denoising steps
            
        Returns:
            Path to generated video
        """
        timestamp = int(time.time())
        if not output_name:
            output_name = f"svd_generated_{timestamp}.mp4"
        
        output_path = self.output_dir / "videos" / output_name
        
        # Use configuration defaults if not specified
        num_frames = num_frames or self.config.video_generation.svd_frames
        num_steps = num_steps or self.config.video_generation.svd_steps
        
        cmd = [
            "python3", "demo_img2vid.py",
            f"--version={model_version}",
            f"--input-image={input_image}",
            f"--num-frames={num_frames}",
            f"--num-steps={num_steps}",
            "--onnx-dir=stable-video-diffusion-img2vid-xt-1-1-tensorrt",
            "--engine-dir=engine-svd-xt-1-1",
            "--build-static-batch",
            "--use-cuda-graph",
            f"--output={output_path}"
        ]
        
        env = self._setup_tensorrt_environment()
        
        try:
            logger.info(f"Generating video from image: {input_image}")
            result = await self._run_subprocess(cmd, env)
            
            if not output_path.exists():
                raise RuntimeError("Video generation failed - output file not created")
            
            logger.info(f"Video generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            raise RuntimeError(f"Video generation failed: {e}") from e
    
    async def text_to_video(self,
                          prompt: str,
                          precision: PrecisionType = "fp8",
                          seed: Optional[int] = None,
                          controlnet_type: Optional[ControlNetType] = None,
                          control_image: Optional[Path] = None) -> Dict[str, Any]:
        """Complete text-to-video pipeline.
        
        Args:
            prompt: Generation prompt
            precision: Precision setting
            seed: Random seed
            controlnet_type: ControlNet type for controlled generation
            control_image: Control image for ControlNet
            
        Returns:
            Dictionary with generated paths and timing information
        """
        start_time = time.time()
        
        try:
            # Step 1: Generate image with SD3.5
            logger.info("🎨 Starting image generation...")
            image_start = time.time()
            
            image_path = await self.generate_image(
                prompt=prompt,
                precision=precision,
                seed=seed,
                controlnet_type=controlnet_type,
                control_image=control_image
            )
            
            image_time = time.time() - image_start
            logger.info(f"✅ Image generation completed in {image_time:.2f}s")
            
            # Step 2: Generate video with SVD
            logger.info("🎬 Starting video generation...")
            video_start = time.time()
            
            video_path = await self.generate_video(image_path)
            
            video_time = time.time() - video_start
            logger.info(f"✅ Video generation completed in {video_time:.2f}s")
            
            total_time = time.time() - start_time
            logger.info(f"🏁 Total pipeline time: {total_time:.2f}s")
            
            return {
                "image": str(image_path),
                "video": str(video_path),
                "prompt": prompt,
                "timings": {
                    "image_generation": image_time,
                    "video_generation": video_time,
                    "total": total_time
                },
                "metadata": {
                    "precision": precision,
                    "seed": seed,
                    "controlnet_type": controlnet_type,
                    "control_image": str(control_image) if control_image else None
                }
            }
            
        except Exception as e:
            logger.error(f"Text-to-video pipeline failed: {e}")
            raise RuntimeError(f"Text-to-video pipeline failed: {e}") from e
    
    async def batch_generate(self,
                           prompts: List[str],
                           precision: PrecisionType = "fp8",
                           max_concurrent: int = 1) -> List[Dict[str, Any]]:
        """Batch process multiple prompts.
        
        Args:
            prompts: List of prompts to process
            precision: Precision setting
            max_concurrent: Maximum concurrent generations
            
        Returns:
            List of generation results
        """
        import asyncio
        
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_single(prompt: str, index: int) -> Dict[str, Any]:
            async with semaphore:
                try:
                    logger.info(f"Processing {index + 1}/{len(prompts)}: {prompt[:50]}...")
                    result = await self.text_to_video(prompt, precision)
                    result["index"] = index
                    return result
                except Exception as e:
                    logger.error(f"Failed to process prompt {index + 1}: {e}")
                    return {
                        "index": index,
                        "prompt": prompt,
                        "error": str(e),
                        "image": None,
                        "video": None
                    }
        
        # Execute batch
        tasks = [generate_single(prompt, i) for i, prompt in enumerate(prompts)]
        results = await asyncio.gather(*tasks)
        
        # Sort by index to maintain order
        results.sort(key=lambda x: x["index"])
        
        return results
    
    async def _run_subprocess(self, cmd: List[str], env: Dict[str, str]) -> subprocess.CompletedProcess:
        """Run subprocess asynchronously."""
        import asyncio
        
        # Create subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=self.workspace_dir
        )
        
        # Wait for completion
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"Command failed: {stderr.decode()}")
        
        return subprocess.CompletedProcess(
            cmd, process.returncode, stdout, stderr
        )
    
    def optimize_for_memory(self):
        """Optimize memory usage."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.backends.cudnn.benchmark = True
            torch.backends.cuda.matmul.allow_tf32 = True
    
    def get_resource_usage(self) -> Dict[str, float]:
        """Get current resource usage."""
        import psutil
        
        resources = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent
        }
        
        if torch.cuda.is_available():
            resources.update({
                "gpu_memory_used_gb": torch.cuda.memory_allocated() / (1024**3),
                "gpu_memory_total_gb": torch.cuda.get_device_properties(0).total_memory / (1024**3),
                "gpu_memory_percent": (torch.cuda.memory_allocated() / torch.cuda.get_device_properties(0).total_memory) * 100
            })
        
        return resources


def create_video_pipeline(config: AppConfig) -> Optional[SD35VideoPipeline]:
    """Factory function to create video generation pipeline.
    
    Args:
        config: Application configuration
        
    Returns:
        SD35VideoPipeline instance if dependencies are available, None otherwise
    """
    try:
        return SD35VideoPipeline(config)
    except ImportError as e:
        logger.warning(f"Video generation pipeline not available: {e}")
        return None


class ProcessingQueue:
    """Asynchronous processing queue for video generation."""
    
    def __init__(self, pipeline: SD35VideoPipeline, max_workers: int = 1):
        """Initialize processing queue.
        
        Args:
            pipeline: Video generation pipeline
            max_workers: Maximum concurrent workers
        """
        self.pipeline = pipeline
        self.max_workers = max_workers
        self.jobs = {}
        self._job_counter = 0
    
    def add_job(self, prompt: str, **kwargs) -> str:
        """Add job to queue.
        
        Args:
            prompt: Generation prompt
            **kwargs: Additional arguments for text_to_video
            
        Returns:
            Job ID
        """
        import uuid
        
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            "id": job_id,
            "prompt": prompt,
            "kwargs": kwargs,
            "status": "queued",
            "created_at": time.time(),
            "result": None,
            "error": None
        }
        
        return job_id
    
    async def process_job(self, job_id: str) -> Dict[str, Any]:
        """Process a specific job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job result
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")
        
        job = self.jobs[job_id]
        
        try:
            job["status"] = "processing"
            job["started_at"] = time.time()
            
            result = await self.pipeline.text_to_video(
                job["prompt"],
                **job["kwargs"]
            )
            
            job["status"] = "completed"
            job["result"] = result
            job["completed_at"] = time.time()
            
        except Exception as e:
            job["status"] = "failed"
            job["error"] = str(e)
            job["completed_at"] = time.time()
        
        return job
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status information
        """
        if job_id not in self.jobs:
            return {"error": "Job not found"}
        
        job = self.jobs[job_id]
        
        return {
            "id": job["id"],
            "status": job["status"],
            "prompt": job["prompt"][:50] + "..." if len(job["prompt"]) > 50 else job["prompt"],
            "created_at": job["created_at"],
            "started_at": job.get("started_at"),
            "completed_at": job.get("completed_at"),
            "error": job.get("error")
        }
    
    def get_job_result(self, job_id: str) -> Dict[str, Any]:
        """Get job result.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Complete job information including result
        """
        if job_id not in self.jobs:
            return {"error": "Job not found"}
        
        return self.jobs[job_id]