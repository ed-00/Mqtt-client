#!/bin/bash

# Build script for internal package distribution
# Usage: ./scripts/build_package.sh [version]

set -e

echo "🏗️  Building MQTT Event Listener Package"
echo "========================================"

# Check if build module is installed
if ! python -c "import build" 2>/dev/null; then
    echo "Installing build module..."
    pip install build
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Build the package
echo "📦 Building package..."
python -m build

# Show what was built
echo ""
echo "✅ Build completed! Generated files:"
ls -la dist/

echo ""
echo "📋 Installation instructions for users:"
echo "--------------------------------------"
echo "1. Install from wheel file:"
echo "   pip install dist/mqtt_event_listener-*.whl"
echo ""
echo "2. Install directly from git:"
echo "   pip install git+https://github.com/ed-00/Mqtt-client.git"
echo ""
echo "3. Install specific version from git:"
echo "   pip install git+https://github.com/ed-00/Mqtt-client.git@v1.0.3"
echo ""
echo "🎉 Package ready for internal distribution!" 