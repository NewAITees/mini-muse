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
