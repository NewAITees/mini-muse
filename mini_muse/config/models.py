"""Configuration data models using Pydantic."""

from typing import Dict, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field, validator


class ModelConfig(BaseModel):
    """Configuration for AI models."""
    
    # Ollama Configuration
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama server host")
    ollama_model: str = Field(default="llama3.1", description="Default Ollama model for prompt enhancement")
    ollama_timeout: int = Field(default=30, description="Ollama request timeout in seconds")
    
    # Stable Diffusion Configuration
    sd_model_id: str = Field(
        default="stabilityai/stable-diffusion-3.5-large",
        description="Stable Diffusion model identifier"
    )
    sd_cache_dir: Optional[str] = Field(default=None, description="Custom cache directory for SD models")
    sd_device: str = Field(default="auto", description="Device for SD inference (auto, cpu, cuda)")
    sd_dtype: str = Field(default="float16", description="Data type for SD inference")
    
    # Generation Parameters
    default_width: int = Field(default=1048, ge=512, le=2048, description="Default image width")
    default_height: int = Field(default=1048, ge=512, le=2048, description="Default image height")
    default_steps: int = Field(default=28, ge=10, le=100, description="Default inference steps")
    default_guidance: float = Field(default=7.0, ge=1.0, le=20.0, description="Default guidance scale")
    
    @validator('sd_device')
    def validate_device(cls, v):
        valid_devices = ['auto', 'cpu', 'cuda', 'mps']
        if v not in valid_devices:
            raise ValueError(f"Device must be one of {valid_devices}")
        return v
    
    @validator('sd_dtype')
    def validate_dtype(cls, v):
        valid_dtypes = ['float16', 'float32', 'bfloat16']
        if v not in valid_dtypes:
            raise ValueError(f"Data type must be one of {valid_dtypes}")
        return v


class UIConfig(BaseModel):
    """Configuration for TUI interface."""
    
    # Display Settings
    image_display_mode: str = Field(
        default="ascii", 
        description="Image display mode (ascii, sixel, external)"
    )
    ascii_width: int = Field(default=80, ge=40, le=200, description="ASCII art width")
    ascii_height: int = Field(default=40, ge=20, le=100, description="ASCII art height")
    
    # Interface Settings
    theme: str = Field(default="dark", description="UI theme (dark, light)")
    show_help: bool = Field(default=True, description="Show help panel by default")
    auto_scroll: bool = Field(default=True, description="Auto-scroll to new content")
    
    # Keyboard Shortcuts
    shortcuts: Dict[str, str] = Field(
        default_factory=lambda: {
            "generate": "ctrl+g",
            "enhance": "ctrl+e", 
            "feedback": "ctrl+f",
            "history": "ctrl+h",
            "settings": "ctrl+s",
            "quit": "ctrl+q",
            "help": "f1"
        },
        description="Keyboard shortcuts mapping"
    )
    
    @validator('image_display_mode')
    def validate_display_mode(cls, v):
        valid_modes = ['ascii', 'sixel', 'external']
        if v not in valid_modes:
            raise ValueError(f"Display mode must be one of {valid_modes}")
        return v
    
    @validator('theme')
    def validate_theme(cls, v):
        valid_themes = ['dark', 'light']
        if v not in valid_themes:
            raise ValueError(f"Theme must be one of {valid_themes}")
        return v


class VideoGenerationConfig(BaseModel):
    """Configuration for video generation pipeline."""
    
    # HuggingFace Settings
    hf_token: Optional[str] = Field(
        default=None,
        description="HuggingFace access token for model downloads"
    )
    
    # Stable Diffusion 3.5 Settings
    sd35_version: str = Field(
        default="3.5-large",
        description="SD3.5 model version"
    )
    sd35_steps: int = Field(
        default=30,
        ge=10,
        le=100,
        description="SD3.5 denoising steps"
    )
    sd35_guidance_scale: float = Field(
        default=3.5,
        ge=1.0,
        le=20.0,
        description="SD3.5 guidance scale"
    )
    
    # Stable Video Diffusion Settings
    svd_version: str = Field(
        default="svd-xt-1.1",
        description="SVD model version"
    )
    svd_frames: int = Field(
        default=25,
        ge=8,
        le=50,
        description="Number of video frames to generate"
    )
    svd_steps: int = Field(
        default=25,
        ge=10,
        le=50,
        description="SVD denoising steps"
    )
    
    # Performance Settings
    use_tensorrt: bool = Field(
        default=True,
        description="Use TensorRT optimization"
    )
    use_cuda_graph: bool = Field(
        default=True,
        description="Use CUDA graph optimization"
    )
    default_precision: str = Field(
        default="fp8",
        description="Default precision (bf16, fp8)"
    )
    
    # Memory Settings
    max_batch_size: int = Field(
        default=1,
        ge=1,
        le=8,
        description="Maximum batch size for generation"
    )
    offload_to_cpu: bool = Field(
        default=False,
        description="Offload models to CPU when not in use"
    )
    
    # Output Settings
    video_format: str = Field(
        default="mp4",
        description="Output video format"
    )
    video_quality: str = Field(
        default="high",
        description="Video quality setting (low, medium, high)"
    )
    
    @validator('default_precision')
    def validate_precision(cls, v):
        valid_precisions = ['bf16', 'fp8']
        if v not in valid_precisions:
            raise ValueError(f"Precision must be one of {valid_precisions}")
        return v
    
    @validator('video_format')
    def validate_video_format(cls, v):
        valid_formats = ['mp4', 'webm', 'gif']
        if v not in valid_formats:
            raise ValueError(f"Video format must be one of {valid_formats}")
        return v


class UpscalingConfig(BaseModel):
    """Configuration for image upscaling."""
    
    # Model Settings
    default_model: str = Field(
        default="realesrgan-x4plus", 
        description="Default upscaling model"
    )
    default_scale_factor: int = Field(
        default=4, 
        ge=2, 
        le=4, 
        description="Default upscaling factor"
    )
    
    # Performance Settings
    tile_size: int = Field(
        default=400, 
        ge=100, 
        le=800, 
        description="Tile size for processing large images"
    )
    tile_padding: int = Field(
        default=32, 
        ge=10, 
        le=100, 
        description="Padding around tiles"
    )
    pre_padding: int = Field(
        default=10, 
        ge=0, 
        le=50, 
        description="Pre-padding for input images"
    )
    use_half_precision: bool = Field(
        default=True, 
        description="Use half precision (float16) for faster inference"
    )
    
    # Feature Settings
    enable_face_enhancement: bool = Field(
        default=False, 
        description="Enable face enhancement using GFPGAN"
    )
    auto_face_enhance: bool = Field(
        default=False, 
        description="Automatically apply face enhancement to portraits"
    )
    
    # Memory Management
    max_memory_usage_mb: int = Field(
        default=4096, 
        ge=1024, 
        le=16384, 
        description="Maximum memory usage in MB"
    )
    clear_cache_after_use: bool = Field(
        default=True, 
        description="Clear model cache after upscaling"
    )
    
    @validator('default_model')
    def validate_default_model(cls, v):
        valid_models = ['realesrgan-x2plus', 'realesrgan-x4plus', 'realesrgan-x4plus-anime']
        if v not in valid_models:
            raise ValueError(f"Default model must be one of {valid_models}")
        return v


class UserPreferences(BaseModel):
    """User preferences and settings."""
    
    # Generation Preferences
    auto_enhance_prompts: bool = Field(default=True, description="Automatically enhance user prompts")
    save_generation_history: bool = Field(default=True, description="Save generation history")
    max_history_items: int = Field(default=100, ge=10, le=1000, description="Maximum history items to keep")
    
    # Style Preferences
    preferred_styles: List[str] = Field(
        default_factory=lambda: ["photorealistic", "artistic"],
        description="Preferred image styles"
    )
    default_negative_prompt: str = Field(
        default="blurry, low quality, distorted, ugly, bad anatomy",
        description="Default negative prompt"
    )
    
    # File Management
    output_directory: str = Field(default="./outputs", description="Directory for saving generated images")
    image_format: str = Field(default="png", description="Default image format")
    compress_history: bool = Field(default=True, description="Compress stored images in history")
    
    # Upscaling Preferences
    auto_upscale: bool = Field(default=False, description="Automatically upscale generated images")
    upscale_only_favorites: bool = Field(default=True, description="Only upscale images marked as favorites")
    
    @validator('image_format')
    def validate_image_format(cls, v):
        valid_formats = ['png', 'jpg', 'jpeg', 'webp']
        if v.lower() not in valid_formats:
            raise ValueError(f"Image format must be one of {valid_formats}")
        return v.lower()
    
    @validator('output_directory')
    def validate_output_directory(cls, v):
        # Ensure the directory path is valid
        try:
            Path(v).expanduser().resolve()
        except Exception as e:
            raise ValueError(f"Invalid output directory path: {e}")
        return v


class AppConfig(BaseModel):
    """Main application configuration."""
    
    # Application Metadata
    app_name: str = Field(default="mini_muse", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    
    # Configuration Sections
    models: ModelConfig = Field(default_factory=ModelConfig, description="Model configuration")
    ui: UIConfig = Field(default_factory=UIConfig, description="UI configuration")
    user: UserPreferences = Field(default_factory=UserPreferences, description="User preferences")
    upscaling: UpscalingConfig = Field(default_factory=UpscalingConfig, description="Upscaling configuration")
    video_generation: VideoGenerationConfig = Field(default_factory=VideoGenerationConfig, description="Video generation configuration")
    
    # System Settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    config_dir: str = Field(default="~/.config/mini_muse", description="Configuration directory")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = "forbid"
        use_enum_values = True