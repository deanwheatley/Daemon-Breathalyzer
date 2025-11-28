#!/bin/bash
#
# Build Package Script
#
# This script creates a distribution package in the package/ folder
# containing everything needed for a new user to install and run the app.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$SCRIPT_DIR/package"
PACKAGE_NAME="daemon-breathalyzer"
VERSION=$(date +%Y%m%d)

echo "============================================================"
echo "Building Distribution Package"
echo "============================================================"
echo ""

# Clean package directory
echo "🧹 Cleaning package directory..."
rm -rf "$PACKAGE_DIR"/*
mkdir -p "$PACKAGE_DIR"

# Copy source code
echo "📦 Copying source code..."
mkdir -p "$PACKAGE_DIR/src"
cp -r "$SCRIPT_DIR/src"/* "$PACKAGE_DIR/src/"

# Remove __pycache__ directories from package
find "$PACKAGE_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PACKAGE_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$PACKAGE_DIR" -type f -name "*.pyo" -delete 2>/dev/null || true

# Copy essential files
echo "📄 Copying essential files..."
cp "$SCRIPT_DIR/requirements.txt" "$PACKAGE_DIR/"
cp "$SCRIPT_DIR/install.sh" "$PACKAGE_DIR/"
cp "$SCRIPT_DIR/run.py" "$PACKAGE_DIR/"
cp "$SCRIPT_DIR/setup_venv.py" "$PACKAGE_DIR/"
cp "$SCRIPT_DIR/daemon-breathalyzer-launcher.sh" "$PACKAGE_DIR/"
cp "$SCRIPT_DIR/daemon-breathalyzer.desktop" "$PACKAGE_DIR/"

# Copy driver installation script
echo "🔧 Copying driver installation scripts..."
cp "$SCRIPT_DIR/check_and_install_drivers.py" "$PACKAGE_DIR/"
cp "$SCRIPT_DIR/fix_system_log_errors.sh" "$PACKAGE_DIR/"

# Copy images
echo "🖼️  Copying images..."
mkdir -p "$PACKAGE_DIR/img"
cp -r "$SCRIPT_DIR/img"/* "$PACKAGE_DIR/img/" 2>/dev/null || true
# Also copy any splash images in root if they exist
if [ -f "$SCRIPT_DIR/installer_splash.png" ]; then
    cp "$SCRIPT_DIR/installer_splash.png" "$PACKAGE_DIR/img/" 2>/dev/null || true
fi
if [ -f "$SCRIPT_DIR/splash.png" ]; then
    cp "$SCRIPT_DIR/splash.png" "$PACKAGE_DIR/img/" 2>/dev/null || true
fi

# Copy essential documentation
echo "📚 Copying documentation..."
cp "$SCRIPT_DIR/README.md" "$PACKAGE_DIR/"
cp "$SCRIPT_DIR/FIX_SYSTEM_LOG_ERRORS.md" "$PACKAGE_DIR/" 2>/dev/null || true

# Create package README
echo "📝 Creating package README..."
cat > "$PACKAGE_DIR/PACKAGE_README.md" << 'EOF'
# Daemon Breathalyzer - Distribution Package

This package contains everything you need to install and run Daemon Breathalyzer on your Linux system.

## 📦 Package Contents

- `src/` - Application source code
- `install.sh` - Main installation script
- `requirements.txt` - Python dependencies
- `README.md` - Full documentation
- `img/` - Application icons
- `daemon-breathalyzer-launcher.sh` - Launcher script
- `daemon-breathalyzer.desktop` - Desktop entry file
- `check_and_install_drivers.py` - Driver installation helper
- `fix_system_log_errors.sh` - System error fixer

## 🚀 Quick Installation

1. **Extract the package** (if downloaded as archive)

2. **Run the installer:**
   ```bash
   cd daemon-breathalyzer
   chmod +x install.sh
   ./install.sh
   ```

3. **Launch the app:**
   - From Application Menu: Search for "Daemon Breathalyzer"
   - Or run: `./daemon-breathalyzer-launcher.sh`

## 📋 Requirements

- Linux Mint or compatible Linux distribution
- Python 3.10+
- Internet connection (for downloading dependencies)

## 🔧 Troubleshooting

See `README.md` for detailed troubleshooting information.

## 📝 License

Copyright © 2024

## 🆘 Support

For issues or questions, refer to the main README.md file.
EOF

# Make scripts executable
echo "🔨 Making scripts executable..."
chmod +x "$PACKAGE_DIR/install.sh"
chmod +x "$PACKAGE_DIR/daemon-breathalyzer-launcher.sh"
chmod +x "$PACKAGE_DIR/fix_system_log_errors.sh"

# Create version file
echo "$VERSION" > "$PACKAGE_DIR/VERSION"

# Create installation instructions
cat > "$PACKAGE_DIR/INSTALL.txt" << 'EOF'
============================================================
Daemon Breathalyzer - Installation Instructions
============================================================

QUICK START:
------------

1. Open terminal in this directory

2. Run the installer:
   ./install.sh

3. The installer will:
   - Check system requirements
   - Create virtual environment
   - Install all dependencies
   - Add app to application menu
   - Install desktop launcher

4. Launch from Application Menu or run:
   ./daemon-breathalyzer-launcher.sh

DETAILED INSTRUCTIONS:
----------------------

See README.md for complete documentation.

TROUBLESHOOTING:
----------------

If installation fails:
- Check that Python 3.10+ is installed: python3 --version
- Install python3-venv: sudo apt install python3-venv
- Check README.md for detailed troubleshooting

============================================================
EOF

# Package size
PACKAGE_SIZE=$(du -sh "$PACKAGE_DIR" | cut -f1)
FILE_COUNT=$(find "$PACKAGE_DIR" -type f | wc -l)

echo ""
echo "============================================================"
echo "✅ Package built successfully!"
echo "============================================================"
echo ""
echo "📦 Package location: $PACKAGE_DIR"
echo "📊 Package size: $PACKAGE_SIZE"
echo "📄 Files: $FILE_COUNT"
echo "🏷️  Version: $VERSION"
echo ""
echo "📋 Package contents:"
ls -lh "$PACKAGE_DIR" | grep -v "^d" | grep -v "^total"
echo ""
echo "💡 To create a distribution archive:"
echo "   cd package"
echo "   tar -czf ../daemon-breathalyzer-$VERSION.tar.gz ."
echo ""
echo "✅ Done!"

