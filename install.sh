#!/bin/bash
# ASUS Fan Control Installer
# Sets up the application and creates desktop entry

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "ASUS Fan Control - Installation"
echo "see https://github.com/deanwheatley/asus-control"
echo "contact deanwheatley@hotmail.com for support"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 > /dev/null 2>&1; then
    echo "❌ Error: python3 is not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
PYTHON_FULL_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Found Python $PYTHON_FULL_VERSION"

# Check if venv module is actually available and functional
echo "🔍 Checking venv module..."
TEMP_VENV_TEST=$(mktemp -d)
VENV_AVAILABLE=true
if ! python3 -m venv "$TEMP_VENV_TEST" > /dev/null 2>&1; then
    rm -rf "$TEMP_VENV_TEST"
    VENV_AVAILABLE=false
    
    echo ""
    echo "⚠️  python3-venv is not properly installed."
    echo ""
    echo "The venv module cannot create virtual environments."
    echo ""
    
    # Check if we can install it automatically
    if command -v apt > /dev/null 2>&1; then
        echo "I can install it automatically for you."
        read -p "Install python${PYTHON_VERSION}-venv now? (Y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            echo "📦 Installing python${PYTHON_VERSION}-venv..."
            if sudo apt install -y python${PYTHON_VERSION}-venv; then
                echo "✅ python${PYTHON_VERSION}-venv installed successfully"
                VENV_AVAILABLE=true
            else
                echo ""
                echo "❌ Failed to install python${PYTHON_VERSION}-venv automatically."
                echo "Please install it manually:"
                echo "  sudo apt install python${PYTHON_VERSION}-venv"
                echo ""
                echo "Then run this installer again."
                exit 1
            fi
        else
            echo ""
            echo "Skipping automatic installation."
            echo "Please install it manually:"
            echo "  sudo apt install python${PYTHON_VERSION}-venv"
            echo ""
            echo "Then run this installer again."
            exit 1
        fi
    else
        echo "apt package manager not found. Please install it manually:"
        echo "  sudo apt install python${PYTHON_VERSION}-venv"
        echo ""
        echo "Then run this installer again."
        exit 1
    fi
fi

if [ "$VENV_AVAILABLE" = true ]; then
    # Verify venv works now (only if we just installed it)
    TEMP_VENV_TEST=$(mktemp -d)
    if ! python3 -m venv "$TEMP_VENV_TEST" > /dev/null 2>&1; then
        rm -rf "$TEMP_VENV_TEST"
        echo ""
        echo "❌ Error: venv still not working after installation."
        echo "You may need to restart your terminal or run:"
        echo "  hash -r"
        exit 1
    fi
    rm -rf "$TEMP_VENV_TEST"
fi

echo "✅ python3-venv is available and functional"
echo ""

# Create virtual environment
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists."
    read -p "Remove and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
    else
        echo "Using existing virtual environment."
    fi
fi

if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    if ! python3 -m venv venv; then
        echo ""
        echo "❌ Error: Failed to create virtual environment."
        echo ""
        echo "This usually means python3-venv is not installed."
        echo ""
        if command -v apt > /dev/null 2>&1; then
            echo "Attempting to install python${PYTHON_VERSION}-venv automatically..."
            if sudo apt install -y python${PYTHON_VERSION}-venv; then
                echo "✅ Installed successfully. Retrying venv creation..."
                if python3 -m venv venv; then
                    echo "✅ Virtual environment created"
                else
                    echo "❌ Still failed. Please install manually and try again."
                    exit 1
                fi
            else
                echo "❌ Failed to install. Please install manually:"
                echo "  sudo apt install python${PYTHON_VERSION}-venv"
                echo ""
                echo "Then run this installer again."
                exit 1
            fi
        else
            echo "Please install it manually:"
            echo "  sudo apt install python${PYTHON_VERSION}-venv"
            echo ""
            echo "Then run this installer again."
            exit 1
        fi
    fi
    echo "✅ Virtual environment created"
fi

# Activate venv
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "✅ Dependencies installed"
echo ""

# Make launcher executable
chmod +x asus-control-launcher.sh

# Install desktop entry
DESKTOP_FILE="$HOME/.local/share/applications/asus-control.desktop"
DESKTOP_DIR="$(dirname "$DESKTOP_FILE")"

mkdir -p "$DESKTOP_DIR"

# Create desktop entry with absolute path
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=ASUS Fan Control
Comment=Modern GUI for ASUS laptop fan curve configuration with system monitoring
Exec=$SCRIPT_DIR/asus-control-launcher.sh
Path=$SCRIPT_DIR
Icon=applications-system
Terminal=false
Categories=System;Settings;HardwareSettings;
StartupNotify=true
Keywords=asus;fan;temperature;cooling;laptop;control;
EOF

chmod +x "$DESKTOP_FILE"

echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "The application has been installed and added to your application menu."
echo ""
echo "You can now:"
echo "  1. Launch it from your application menu (search for 'ASUS Fan Control')"
echo "  2. Or run it directly: ./asus-control-launcher.sh"
echo "  3. Or run it from terminal: source venv/bin/activate && python3 run.py"
echo ""
echo "To uninstall, remove:"
echo "  - $DESKTOP_FILE"
echo "  - $SCRIPT_DIR/venv (optional)"
echo ""

