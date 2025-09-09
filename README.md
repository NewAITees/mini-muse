# mini_muse

AI-powered image generation and feedback application using Stable Diffusion 3.5 Large and ollama-powered local LLM.

## Features

- **Local AI Integration**: Uses Stable Diffusion 3.5 Large for image generation and ollama for prompt enhancement
- **TUI Interface**: Terminal-based user interface built with Textual
- **AI Feedback**: Get intelligent feedback on generated images to improve your prompts
- **Iterative Improvement**: Refine images through AI-guided iterations
- **Session Management**: Track generation history and compare iterations

## Requirements

- Python 3.9+
- CUDA-compatible GPU (recommended for Stable Diffusion)
- Ollama installed and running locally

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mini_muse
```

2. Install the package:
```bash
pip install -e .
```

3. Install development dependencies (optional):
```bash
pip install -e ".[dev]"
```

## Configuration

The application uses a YAML configuration file located at `~/.config/mini_muse/config.yaml`. 

To view current configuration:
```bash
mini-muse config --show
```

To reset configuration to defaults:
```bash
mini-muse config --reset
```

## Usage

Run the application:
```bash
mini-muse run
```

For debug mode:
```bash
mini-muse run --debug
```

## Development

Install development dependencies:
```bash
pip install -e ".[dev,test]"
```

Run tests:
```bash
pytest
```

Format code:
```bash
black mini_muse tests
isort mini_muse tests
```

## License

MIT License