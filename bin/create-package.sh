#!/bin/bash
# Create Daemon Breathalyzer complete package installer

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PACKAGE_DIR="$SCRIPT_DIR/package-build"

echo "🏗️  Creating Daemon Breathalyzer Package Installer"
echo "=============================================="

# Clean previous build
rm -rf "$PACKAGE_DIR" "$SCRIPT_DIR"/*.tar.gz "$SCRIPT_DIR"/daemon-breathalyzer-installer-*.sh
mkdir -p "$PACKAGE_DIR"

echo "📦 Copying application files..."

# Copy essential files
cp -r "$PROJECT_DIR/src" "$PACKAGE_DIR/"
[ -d "$PROJECT_DIR/data" ] && cp -r "$PROJECT_DIR/data" "$PACKAGE_DIR/"
[ -d "$PROJECT_DIR/img" ] && cp -r "$PROJECT_DIR/img" "$PACKAGE_DIR/"
cp "$PROJECT_DIR/requirements.txt" "$PACKAGE_DIR/"
cp "$PROJECT_DIR/install.sh" "$PACKAGE_DIR/"
cp "$PROJECT_DIR/asus-control-launcher.sh" "$PACKAGE_DIR/"
cp "$PROJECT_DIR/run.py" "$PACKAGE_DIR/"
cp "$PROJECT_DIR/check_and_install_drivers.py" "$PACKAGE_DIR/"
cp "$PROJECT_DIR/README.md" "$PACKAGE_DIR/"

echo "📦 Creating package archive..."
cd "$PACKAGE_DIR"
tar -czf "../package.tar.gz" .
cd "$SCRIPT_DIR"

echo "🔧 Creating self-extracting installer..."
cp "daemon-breathalyzer-installer.sh" "daemon-breathalyzer-installer-v1.0.2.sh"
cat "package.tar.gz" >> "daemon-breathalyzer-installer-v1.0.2.sh"
chmod +x "daemon-breathalyzer-installer-v1.0.2.sh"

# Cleanup
rm -rf "$PACKAGE_DIR" "package.tar.gz"

echo "✅ Package created: daemon-breathalyzer-installer-v1.0.2.sh"
echo ""
echo "📋 Usage:"
echo "  1. Copy daemon-breathalyzer-installer-v1.0.2.sh to target system"
echo "  2. Run: ./daemon-breathalyzer-installer-v1.0.2.sh"
echo "  3. Application will be installed and ready to use"
echo ""
echo "📊 Package size: $(du -h daemon-breathalyzer-installer-v1.0.2.sh | cut -f1)"