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
    default_width: int = Field(default=1024, ge=512, le=2048, description="Default image width")
    default_height: int = Field(default=1024, ge=512, le=2048, description="Default image height")
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