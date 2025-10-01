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
