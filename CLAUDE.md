# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

mini_muse is an AI-powered image generation and feedback application using Stable Diffusion 3.5 Large and ollama-powered local LLM with a Terminal User Interface (TUI) built with Textual.

## Development Commands

### Installation and Setup
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

## Notes
- The TUI implementation is not yet complete (see TODO in main.py:62)
- Application requires Python 3.9+ and CUDA-compatible GPU recommended
- Uses MIT license