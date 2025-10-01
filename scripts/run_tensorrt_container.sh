#!/bin/bash
# Run TensorRT container with GPU support

set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
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
    -v $PWD/stable_diffusion_data/models:/models \
    -v $PWD/stable_diffusion_data/outputs:/output \
    -v $PWD/stable_diffusion_data/cache:/cache \
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
