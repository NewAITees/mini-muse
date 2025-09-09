"""Configuration management utilities."""

import os
import yaml
import toml
from pathlib import Path
from typing import Dict, Any, Optional
from .models import AppConfig


class Config:
    """Configuration manager for mini_muse application."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path or self._get_default_config_path()
        self._config: Optional[AppConfig] = None
    
    def _get_default_config_path(self) -> Path:
        """Get default configuration file path."""
        config_dir = Path.home() / ".config" / "mini_muse"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.yaml"
    
    def load(self) -> AppConfig:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    if self.config_path.suffix.lower() == '.toml':
                        data = toml.load(f)
                    else:
                        data = yaml.safe_load(f)
                
                self._config = AppConfig(**data)
            except Exception as e:
                print(f"Warning: Failed to load config from {self.config_path}: {e}")
                print("Using default configuration.")
                self._config = AppConfig()
        else:
            self._config = AppConfig()
            # Save default configuration
            self.save()
        
        return self._config
    
    def save(self, config: Optional[AppConfig] = None) -> None:
        """Save configuration to file.
        
        Args:
            config: Configuration to save. If None, saves current config.
        """
        if config is not None:
            self._config = config
        
        if self._config is None:
            raise ValueError("No configuration to save")
        
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dictionary
        config_dict = self._config.dict()
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.suffix.lower() == '.toml':
                    toml.dump(config_dict, f)
                else:
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        except Exception as e:
            raise RuntimeError(f"Failed to save config to {self.config_path}: {e}")
    
    def get(self) -> AppConfig:
        """Get current configuration."""
        if self._config is None:
            return self.load()
        return self._config
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates
        """
        if self._config is None:
            self.load()
        
        # Create new config with updates
        current_dict = self._config.dict()
        self._merge_dict(current_dict, updates)
        
        self._config = AppConfig(**current_dict)
    
    def _merge_dict(self, base: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """Recursively merge dictionaries."""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_dict(base[key], value)
            else:
                base[key] = value
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        self._config = AppConfig()
        self.save()


# Global configuration instance
_global_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """Load configuration from file.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Loaded configuration
    """
    if config_path:
        config = Config(config_path)
    else:
        config = get_config()
    
    return config.load()


def save_config(app_config: AppConfig, config_path: Optional[Path] = None) -> None:
    """Save configuration to file.
    
    Args:
        app_config: Configuration to save
        config_path: Optional path to configuration file
    """
    if config_path:
        config = Config(config_path)
    else:
        config = get_config()
    
    config.save(app_config)


def update_config(updates: Dict[str, Any], config_path: Optional[Path] = None) -> None:
    """Update configuration with new values.
    
    Args:
        updates: Dictionary of configuration updates
        config_path: Optional path to configuration file
    """
    if config_path:
        config = Config(config_path)
    else:
        config = get_config()
    
    config.update(updates)
    config.save()