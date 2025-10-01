#!/bin/bash
# Quick start script for mini_muse with TensorRT

set -e

echo "🚀 Quick start mini_muse with TensorRT..."

# Check if models are built
if [ ! -d "./stable_diffusion_data/models" ] || [ -z "$(ls -A ./stable_diffusion_data/models 2>/dev/null)" ]; then
    echo "🔧 Models not found in ./stable_diffusion_data/models. Building them first..."
    ./scripts/setup_models.sh
fi

echo "📂 Available models:"
ls -la ./stable_diffusion_data/models/ || echo "No models found"
echo "📂 Sample outputs:"
ls -la ./stable_diffusion_data/outputs/ || echo "No outputs yet"

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

