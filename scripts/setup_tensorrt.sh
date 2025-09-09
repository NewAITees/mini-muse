#!/bin/bash
# TensorRT Setup Script for mini_muse
# Automates the setup of NVIDIA TensorRT environment for SD3.5 + SVD

set -e

echo "🚀 Setting up NVIDIA TensorRT environment for mini_muse..."

# Check if CUDA is available
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ NVIDIA GPU drivers not found. Please install NVIDIA drivers and CUDA."
    exit 1
fi

echo "✅ NVIDIA GPU detected:"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker with GPU support."
    exit 1
fi

# Check if nvidia-container-toolkit is available
if ! docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi &> /dev/null; then
    echo "❌ NVIDIA Container Toolkit not found. Please install nvidia-container-toolkit."
    exit 1
fi

echo "✅ Docker with GPU support detected"

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
    -v $PWD/models:/models \
    -v $PWD/outputs:/output \
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
    --hf-token=$HF_TOKEN

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
    --hf-token=$HF_TOKEN

# Build SVD engines
echo "🎬 Building Stable Video Diffusion TensorRT engines..."
python demo_img2vid.py \
    --version=svd-xt-1.1 \
    --build-static-batch \
    --use-cuda-graph \
    --download-onnx-models \
    --hf-token=$HF_TOKEN

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
if [ ! -d "TensorRT/demo/Diffusion/engine" ] || [ -z "$(ls -A TensorRT/demo/Diffusion/engine)" ]; then
    echo "🔧 TensorRT engines not found. Building them first..."
    ./scripts/setup_models.sh
fi

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
echo "🔗 Useful scripts created:"
echo "  ./scripts/run_tensorrt_container.sh  - Start TensorRT container"
echo "  ./scripts/setup_models.sh           - Build TensorRT engines"
echo "  ./scripts/quickstart.sh             - Quick start guide"
echo "  ./scripts/dev_setup.sh              - Development setup"
echo ""
echo "📖 For more information, see the README.md file"