#!/bin/bash
# TensorRT Setup Script for mini_muse
# Automates the setup of NVIDIA TensorRT environment for SD3.5 + SVD

set -e

echo "🚀 Setting up NVIDIA TensorRT environment for mini_muse..."

# Setup mount first (if not already mounted)
if mountpoint -q ./stable_diffusion_data 2>/dev/null; then
    echo "✅ stable_diffusion_data already mounted"
else
    echo "📁 Setting up stable_diffusion_data mount..."
    ./scripts/setup_mounts.sh
fi

# Create model and output directories
echo "📂 Creating model and output directories..."
mkdir -p ./stable_diffusion_data/stablediffusion/models
mkdir -p ./stable_diffusion_data/stablediffusion/outputs
mkdir -p ./stable_diffusion_data/stablediffusion/cache

# Check if CUDA is available
echo "🔍 Testing NVIDIA GPU detection..."
if nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU drivers detected"
else
    echo "❌ NVIDIA GPU drivers not found. Please install NVIDIA drivers and CUDA."
    echo "Debug: Checking nvidia-smi path and execution..."
    which nvidia-smi || echo "nvidia-smi not in PATH"
    ls -la /usr/lib/wsl/lib/nvidia-smi || echo "WSL nvidia-smi not found"
    exit 1
fi

echo "✅ NVIDIA GPU detected:"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker with GPU support."
    exit 1
fi

# Check if nvidia-container-toolkit is available (skip if already tested)
if [ ! -f ".docker_gpu_tested" ]; then
    echo "🧪 Testing Docker GPU support..."
    if docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu20.04 nvidia-smi &> /dev/null; then
        echo "✅ Docker with GPU support detected"
        touch .docker_gpu_tested
    else
        echo "❌ NVIDIA Container Toolkit not found. Please install nvidia-container-toolkit."
        exit 1
    fi
else
    echo "✅ Docker GPU support already verified"
fi

# Clone TensorRT repository if not exists
TENSORRT_DIR="./TensorRT"
if [ ! -d "$TENSORRT_DIR" ]; then
    echo "📥 Cloning NVIDIA TensorRT repository..."
    git clone https://github.com/NVIDIA/TensorRT.git
    cd TensorRT
    git checkout release/sd35
    cd ..
else
    echo "✅ TensorRT repository already exists"
    # Check if it's on the right branch
    cd TensorRT
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "release/sd35" ]; then
        echo "📝 Switching to release/sd35 branch..."
        git checkout release/sd35
    fi
    cd ..
fi

# Create .env file for HuggingFace token
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo "📝 Creating environment configuration..."
    cat > $ENV_FILE << EOF
# HuggingFace Token for model downloads
# Get your token from: https://huggingface.co/settings/tokens
HF_TOKEN=your_token_here

# TensorRT Configuration
CUDA_VISIBLE_DEVICES=0
TRT_LOGGER_VERBOSITY=WARNING
TOKENIZERS_PARALLELISM=false
EOF
    echo "⚠️  Please edit .env and add your HuggingFace token"
else
    echo "✅ Environment file already exists"
    # Check if HF_TOKEN is set
    if grep -q "HF_TOKEN=your_token_here" $ENV_FILE; then
        echo "⚠️  Please update your HuggingFace token in .env file"
    else
        echo "✅ HuggingFace token appears to be configured"
    fi
fi

# Create Docker setup script
DOCKER_SCRIPT="scripts/run_tensorrt_container.sh"
mkdir -p scripts
cat > $DOCKER_SCRIPT << 'EOF'
#!/bin/bash
# Run TensorRT container with GPU support

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Check if HF_TOKEN is set
if [ -z "$HF_TOKEN" ] || [ "$HF_TOKEN" = "your_token_here" ]; then
    echo "❌ Please set your HuggingFace token in .env file"
    exit 1
fi

echo "🐳 Starting TensorRT container..."

docker run --rm -it --gpus all \
    --env-file .env \
    -v $PWD:/workspace \
    -v $PWD/stable_diffusion_data/stablediffusion/models:/models \
    -v $PWD/stable_diffusion_data/stablediffusion/outputs:/output \
    -v $PWD/stable_diffusion_data/stablediffusion/cache:/cache \
    -w /workspace \
    nvcr.io/nvidia/pytorch:25.01-py3 \
    /bin/bash -c "
        echo '📦 Installing dependencies...'
        cd TensorRT/demo/Diffusion
        pip install -r requirements.txt
        pip install --pre --upgrade --extra-index-url https://pypi.nvidia.com tensorrt-cu12
        echo '✅ Environment ready! You can now run mini-muse commands.'
        /bin/bash
    "
EOF

chmod +x $DOCKER_SCRIPT

# Create model setup script
MODEL_SCRIPT="scripts/setup_models.sh"
cat > $MODEL_SCRIPT << 'EOF'
#!/bin/bash
# Setup and build TensorRT engines for SD3.5 and SVD

set -e

echo "🔧 Setting up TensorRT models..."

# Check if HF_TOKEN is set
if [ -z "$HF_TOKEN" ] || [ "$HF_TOKEN" = "your_token_here" ]; then
    echo "❌ Please set your HuggingFace token in .env file"
    exit 1
fi

# Check if models already exist
if [ -d "/models/stable-diffusion-3.5-large" ] && [ -d "/models/stable-video-diffusion-img2vid-xt-1-1" ]; then
    echo "✅ Models already downloaded, skipping download"
else
    # Download models first
    echo "📥 Downloading Stable Diffusion 3.5 models..."
python -c "
import torch
from huggingface_hub import hf_hub_download
from diffusers import StableDiffusion3Pipeline
import os

# Set cache directory
os.environ['HF_HOME'] = '/cache'
os.environ['TRANSFORMERS_CACHE'] = '/cache/transformers'
os.environ['DIFFUSERS_CACHE'] = '/cache/diffusers'

print('Downloading SD3.5 Large...')
pipeline = StableDiffusion3Pipeline.from_pretrained(
    'stabilityai/stable-diffusion-3.5-large',
    torch_dtype=torch.float16,
    cache_dir='/cache'
)
pipeline.save_pretrained('/models/stable-diffusion-3.5-large')
print('✅ SD3.5 Large downloaded')

print('Downloading SVD-XT 1.1...')
from diffusers import StableVideoDiffusionPipeline
svd_pipeline = StableVideoDiffusionPipeline.from_pretrained(
    'stabilityai/stable-video-diffusion-img2vid-xt-1-1',
    torch_dtype=torch.float16,
    cache_dir='/cache'
)
svd_pipeline.save_pretrained('/models/stable-video-diffusion-img2vid-xt-1-1')
print('✅ SVD-XT 1.1 downloaded')
"
fi

cd TensorRT/demo/Diffusion

# Build SD3.5 engines
echo "🎨 Building Stable Diffusion 3.5 TensorRT engines..."
python demo_txt2img_sd35.py \
    "A test prompt for engine building" \
    --version=3.5-large \
    --height=1048 \
    --width=1048 \
    --denoising-steps=30 \
    --guidance-scale=3.5 \
    --build-static-batch \
    --fp8 \
    --use-cuda-graph \
    --download-onnx-models \
    --hf-token=$HF_TOKEN \
    --models-dir=/models \
    --output-dir=/output

# Build ControlNet engines
echo "🎯 Building ControlNet TensorRT engines..."
python demo_controlnet_sd35.py \
    "A test prompt" \
    --version=3.5-large \
    --controlnet-type=canny \
    --build-static-batch \
    --fp8 \
    --use-cuda-graph \
    --download-onnx-models \
    --hf-token=$HF_TOKEN \
    --models-dir=/models \
    --output-dir=/output

# Build SVD engines
echo "🎬 Building Stable Video Diffusion TensorRT engines..."
python demo_img2vid.py \
    --version=svd-xt-1.1 \
    --build-static-batch \
    --use-cuda-graph \
    --download-onnx-models \
    --hf-token=$HF_TOKEN \
    --models-dir=/models \
    --output-dir=/output

echo "✅ All TensorRT engines built successfully!"
EOF

chmod +x $MODEL_SCRIPT

# Create quick start script
QUICKSTART_SCRIPT="scripts/quickstart.sh"
cat > $QUICKSTART_SCRIPT << 'EOF'
#!/bin/bash
# Quick start script for mini_muse with TensorRT

set -e

echo "🚀 Quick start mini_muse with TensorRT..."

# Check if models are built
if [ ! -d "./stable_diffusion_data/stablediffusion/models" ] || [ -z "$(ls -A ./stable_diffusion_data/stablediffusion/models 2>/dev/null)" ]; then
    echo "🔧 Models not found in ./stable_diffusion_data/stablediffusion/models. Building them first..."
    ./scripts/setup_models.sh
fi

echo "📂 Available models:"
ls -la ./stable_diffusion_data/stablediffusion/models/ || echo "No models found"
echo "📂 Sample outputs:"
ls -la ./stable_diffusion_data/stablediffusion/outputs/ || echo "No outputs yet"

echo "✅ Starting mini_muse..."

# Example commands
echo "📋 Example commands:"
echo "  # Generate image:"
echo "  mini-muse generate-image 'A beautiful landscape'"
echo ""
echo "  # Generate video:"
echo "  mini-muse generate-video 'A dragon flying over mountains'"
echo ""
echo "  # Enhance prompt:"
echo "  mini-muse enhance-prompt 'a cat' --style photorealistic"

EOF

chmod +x $QUICKSTART_SCRIPT

# Create development setup script
DEV_SCRIPT="scripts/dev_setup.sh"
cat > $DEV_SCRIPT << 'EOF'
#!/bin/bash
# Development environment setup

set -e

echo "🛠️  Setting up development environment..."

# Install mini_muse in development mode
pip install -e ".[dev,test]"

# Install additional TensorRT dependencies
pip install nvidia-modelopt polygraphy cuda-python

echo "✅ Development environment ready!"
echo ""
echo "🧪 Run tests:"
echo "  pytest"
echo ""
echo "🎨 Format code:"
echo "  black mini_muse tests"
echo "  isort mini_muse tests"
EOF

chmod +x $DEV_SCRIPT

echo ""
echo "✅ TensorRT setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file and add your HuggingFace token"
echo "2. Run: ./scripts/run_tensorrt_container.sh"
echo "3. Inside container, run: ./scripts/setup_models.sh"
echo "4. Start using: mini-muse generate-image 'your prompt'"
echo ""
echo "📂 Model and output directories:"
echo "  ./stable_diffusion_data/stablediffusion/models/  - Downloaded models"
echo "  ./stable_diffusion_data/stablediffusion/outputs/ - Generated images/videos"
echo "  ./stable_diffusion_data/stablediffusion/cache/   - HuggingFace cache"
echo ""
echo "🔗 Useful scripts created:"
echo "  ./scripts/run_tensorrt_container.sh  - Start TensorRT container"
echo "  ./scripts/setup_models.sh           - Download models & build TensorRT engines"
echo "  ./scripts/quickstart.sh             - Quick start guide"
echo "  ./scripts/dev_setup.sh              - Development setup"
echo ""
echo "📖 For more information, see the README.md file"