# mini_muse

AI-powered image generation and feedback application using Stable Diffusion 3.5 Large and ollama-powered local LLM.

## Features

- **🎬 Text-to-Video Pipeline**: Complete pipeline using Stable Diffusion 3.5 Large + Stable Video Diffusion 1.1
- **🚀 TensorRT Optimization**: High-speed inference with NVIDIA TensorRT and CUDA graph optimization
- **🎨 ControlNet Support**: Precise control over image generation with Canny/Depth/Blur conditioning
- **✨ AI Prompt Enhancement**: Intelligent prompt enhancement using Ollama-powered LLM
- **📈 Image Upscaling**: AI-powered upscaling using Real-ESRGAN (2x/4x) with optional face enhancement
- **🖥️ TUI Interface**: Terminal-based user interface built with Textual
- **🤖 AI Feedback**: Get intelligent feedback on generated images to improve your prompts
- **🔄 Iterative Improvement**: Refine images through AI-guided iterations
- **📊 Session Management**: Track generation history and compare iterations
- **⚡ Batch Processing**: Process multiple prompts and images simultaneously

## Requirements

### Hardware Requirements
- **GPU**: NVIDIA RTX 4090+ (H100/A100 optimal)
- **VRAM**: Minimum 16GB, recommended 24GB+
- **RAM**: 32GB+ recommended
- **Storage**: 50GB+ free space for models

### Software Requirements
- Python 3.9+
- CUDA 12.0+ compatible GPU drivers
- Docker with GPU support (for TensorRT)
- NVIDIA Container Toolkit
- Ollama installed and running locally
- HuggingFace account with access token

## Installation

1. Clone the repository:
```bash
git clone https://github.com/NewAITees/mini-muse.git
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

4. Set up HuggingFace token:
```bash
export HF_TOKEN=your_huggingface_token_here
# Or add to your configuration file
```

5. Setup NVIDIA TensorRT (recommended for optimal performance):
```bash
# Automated setup script
./scripts/setup_tensorrt.sh

# Or manual setup - see Advanced Setup section
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

### Key Configuration Options

```yaml
# Video Generation Settings
video_generation:
  hf_token: "your_token_here"
  sd35_steps: 30
  sd35_guidance_scale: 3.5
  svd_frames: 25
  default_precision: "fp8"  # or "bf16"
  use_tensorrt: true

# Upscaling Settings  
upscaling:
  default_model: "realesrgan-x4plus"
  default_scale_factor: 4
  enable_face_enhancement: false

# Model Settings
models:
  default_width: 1048
  default_height: 1048
  ollama_model: "llama3.1"
```

## Usage

### Main Application

Run the application:
```bash
mini-muse run
```

For debug mode:
```bash
mini-muse run --debug
```

### Image Generation

Generate high-quality images using NVIDIA optimized SD3.5:

```bash
# Basic image generation
mini-muse generate-image "A beautiful landscape"

# With specific parameters
mini-muse generate-image "A portrait of a cat" \
  --style photorealistic \
  --seed 42 \
  --steps 30 \
  --guidance 7.5

# ControlNet guided generation
mini-muse generate-image "A futuristic city" \
  --controlnet canny \
  --control-image edges.png \
  --enhance
```

### Image Upscaling

Upscale a single image:
```bash
# Basic upscaling (4x by default)
mini-muse upscale input.png

# Specify scale factor and output
mini-muse upscale input.png --scale 2 --output upscaled.png

# Use specific model and face enhancement
mini-muse upscale input.png --model realesrgan-x4plus-anime --face-enhance
```

Batch upscale multiple images:
```bash
# Upscale all images in a directory
mini-muse batch-upscale ./images/

# With custom output directory and scale
mini-muse batch-upscale ./images/ --output-dir ./upscaled/ --scale 4
```

### Text-to-Video Generation

Generate videos using the complete SD3.5 + SVD pipeline:

```bash
# Basic video generation
mini-muse generate-video "A serene Japanese garden with cherry blossoms"

# Enhanced video generation with specific style
mini-muse generate-video "A dragon flying over mountains" --style cinematic --enhance

# ControlNet-guided video generation
mini-muse generate-video "Futuristic cityscape" --controlnet canny --control-image edges.png

# Batch video generation from prompts file
mini-muse batch-video prompts.json --output-dir ./videos/
```

### Prompt Enhancement

Enhance your prompts using AI:

```bash
# Enhance a single prompt
mini-muse enhance-prompt "a cat in a garden" --style photorealistic

# Generate prompt variations
mini-muse enhance-prompt "sunset landscape" --variations 5 --style artistic

# Analyze prompt quality
mini-muse analyze-prompt "professional photo of a mountain landscape"
```

### Available Upscaling Models

- `realesrgan-x2plus`: General purpose 2x upscaling
- `realesrgan-x4plus`: General purpose 4x upscaling (default)
- `realesrgan-x4plus-anime`: Optimized for anime/cartoon images (4x)

### Enhancement Styles

- `photorealistic`: Professional photography style
- `artistic`: Digital art and illustration style
- `cinematic`: Cinematic lighting and composition
- `fantasy`: Fantasy and magical themes
- `anime`: Anime and manga style
- `portrait`: Portrait photography style

## Advanced Setup

### Docker with TensorRT

For optimal performance, use the provided Docker setup:

```bash
# Run setup script
./scripts/setup_tensorrt.sh

# Start TensorRT container
./scripts/run_tensorrt_container.sh

# Inside container, build models
./scripts/setup_models.sh
```

### Manual TensorRT Setup

```bash
# Clone TensorRT repository
git clone https://github.com/NVIDIA/TensorRT.git
cd TensorRT
git checkout release/sd35

# Install dependencies
cd demo/Diffusion
pip install -r requirements.txt
pip install --pre --upgrade --extra-index-url https://pypi.nvidia.com tensorrt-cu12

# Build engines (inside container or with proper CUDA setup)
python demo_txt2img_sd35.py "test" --build-static-batch --fp8 --use-cuda-graph
```

## Development

Install development dependencies:
```bash
pip install -e ".[dev,test]"

# Or use automated development setup
./scripts/dev_setup.sh
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

### Architecture Overview

- **`image_generation.py`**: NVIDIA optimized SD3.5 (default image generation)
- **`video_generation.py`**: Complete text-to-video pipeline (SD3.5 + SVD)
- **`upscaling.py`**: Real-ESRGAN image upscaling
- **`prompt_enhancement.py`**: AI-powered prompt optimization

## License

MIT License
