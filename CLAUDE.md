# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

mini_muse is an AI-powered image generation and feedback application using Stable Diffusion 3.5 Large and ollama-powered local LLM with a Terminal User Interface (TUI) built with Textual.

## Development Commands

### Installation and Setup

#### Quick Start with Mounts
```bash
# Setup project with Windows D: drive mount (recommended)
./scripts/start_with_mounts.sh

# Or setup mounts manually
./scripts/setup_mounts.sh
```

#### Standard Installation
```bash
# Install the package in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev,test]"
```

### Running the Application
```bash
# Run the main TUI application
mini-muse run

# Run with debug mode
mini-muse run --debug

# Show current configuration
mini-muse config --show

# Reset configuration to defaults
mini-muse config --reset
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=mini_muse
```

### Code Quality
```bash
# Format code
black mini_muse tests
isort mini_muse tests

# Type checking
mypy mini_muse

# Linting
flake8 mini_muse
```

## Architecture

### Core Structure
- `mini_muse/main.py`: CLI entry point using Typer, handles configuration management and app startup
- `mini_muse/config/`: Configuration management with Pydantic models and YAML/TOML support
  - `config.py`: Configuration loading/saving utilities
  - `models.py`: Pydantic models for configuration validation
- `mini_muse/core/`: Core application logic (placeholder for TUI and business logic)
- `mini_muse/services/`: External service integrations (Stable Diffusion, Ollama)
- `mini_muse/models/`: Data models and schemas
- `mini_muse/ui/`: Textual TUI components
- `mini_muse/utils/`: Utility functions and helpers

### Configuration System
Configuration is managed through:
- Default location: `~/.config/mini_muse/config.yaml`
- Supports both YAML and TOML formats
- Uses Pydantic for validation and type safety
- Can be reset to defaults via CLI command

### Key Dependencies
- **TUI Framework**: Textual for the terminal interface
- **Image Generation**: diffusers, torch, transformers for Stable Diffusion
- **LLM Integration**: ollama for local LLM interaction
- **Configuration**: Pydantic for validation, PyYAML/toml for file formats
- **CLI**: Typer for command-line interface

### Test Structure
Tests are organized in `tests/` with subdirectories:
- `unit/`: Unit tests for individual components
- `integration/`: Integration tests for component interaction
- `e2e/`: End-to-end tests for full application workflow

## Stable Diffusion Data Storage

The application uses symbolic links to Windows D: drive for Stable Diffusion models and outputs:

### Storage Configuration
- **Windows Path**: `D:\python\stablediffusion`
- **Symbolic Link**: `./stable_diffusion_data -> /mnt/d/python/stablediffusion`
- **Subdirectories**:
  - `models/` - Stable Diffusion model files
  - `outputs/` - Generated images and outputs
  - `cache/` - HuggingFace cache files

### Setup Options

1. **Dev Container** (VS Code): Symbolic link is automatically configured in `.devcontainer/devcontainer.json`

2. **Docker Compose**: Use `docker-compose up` with the provided configuration

3. **Manual Setup**: Symbolic link is created automatically during setup

4. **Full Project Setup**: Run `./scripts/start_with_mounts.sh` for complete environment setup

### Usage
After setup, the stable diffusion data is available at:
```bash
ls ./stable_diffusion_data/stablediffusion/models    # Model files
ls ./stable_diffusion_data/stablediffusion/outputs   # Generated images
ls ./stable_diffusion_data/stablediffusion/cache     # Cache files
```

## Notes
- The TUI implementation is not yet complete (see TODO in main.py:62)
- Application requires Python 3.9+ and CUDA-compatible GPU recommended
- Windows D: drive mount requires WSL2 with properly mounted Windows drives
- Uses MIT license