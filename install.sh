#!/bin/bash
# Daemon Breathalyzer Installer
# Sets up the application and creates desktop entry
# Automatically installs all required system dependencies

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Display installer splash image if available
show_splash_image() {
    # Try multiple possible image locations
    local image_file=""
    for possible_path in \
        "$SCRIPT_DIR/img/installer_splash.png" \
        "$SCRIPT_DIR/img/splash.png" \
        "$SCRIPT_DIR/img/icon.png" \
        "$SCRIPT_DIR/installer_splash.png" \
        "$SCRIPT_DIR/splash.png"; do
        if [ -f "$possible_path" ]; then
            image_file="$possible_path"
            break
        fi
    done
    
    if [ -z "$image_file" ] || [ ! -f "$image_file" ]; then
        return 0  # No image found, silently continue
    fi
    
    local splash_pid=""
    
    # Try to display image in a window
    if command -v feh > /dev/null 2>&1; then
        # feh - lightweight image viewer
        feh --title "Daemon Breathalyzer - Installing..." \
            --geometry 400x400+100+100 \
            --borderless \
            --no-menus \
            --keep-above \
            "$image_file" 2>/dev/null &
        splash_pid=$!
    elif command -v eog > /dev/null 2>&1; then
        # Eye of GNOME
        eog --new-instance "$image_file" 2>/dev/null &
        splash_pid=$!
    elif command -v zenity > /dev/null 2>&1; then
        # zenity info dialog with icon
        zenity --info \
               --title="Daemon Breathalyzer" \
               --text="Installing...\n\nPlease wait while the installation completes." \
               --window-icon="$image_file" \
               --no-wrap 2>/dev/null &
        splash_pid=$!
    fi
    
    # Store PID to close later
    if [ ! -z "$splash_pid" ]; then
        echo "$splash_pid" > /tmp/daemon-breathalyzer-installer-splash.pid
        # Small delay to let window appear
        sleep 0.5
    fi
}

# Clean up splash image on exit
cleanup_splash() {
    if [ -f /tmp/daemon-breathalyzer-installer-splash.pid ]; then
        local pid=$(cat /tmp/daemon-breathalyzer-installer-splash.pid 2>/dev/null)
        if [ ! -z "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            # Wait a moment for the process to terminate
            sleep 0.3
        fi
        rm -f /tmp/daemon-breathalyzer-installer-splash.pid 2>/dev/null || true
    fi
}

# Set trap to cleanup on exit
trap cleanup_splash EXIT

# Show splash image
show_splash_image

echo "=========================================="
echo "Daemon Breathalyzer - Installation"
echo "see https://github.com/deanwheatley/Daemon-Breathalyzer"
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
if ! pip install -q -r requirements.txt; then
    echo "❌ Error: Failed to install some dependencies."
    echo ""
    echo "Please check the error messages above and ensure:"
    echo "  1. You have internet connectivity"
    echo "  2. pip is up to date"
    echo ""
    echo "You can try installing manually:"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

echo "✅ Dependencies installed"
echo ""

# Verify critical Python libraries are installed
echo "🔍 Verifying critical libraries..."
MISSING_LIBS=()
CRITICAL_LIBS=(
    "PyQt6"
    "PyQtGraph"
    "psutil"
    "numpy"
)

# Map import names to package names (some differ)
LIB_PACKAGE_MAP=(
    "PyQt6:PyQt6"
    "PyQtGraph:pyqtgraph"
    "psutil:psutil"
    "numpy:numpy"
)

for lib in "${CRITICAL_LIBS[@]}"; do
    # Map import name to package name
    pkg_name="$lib"
    case "$lib" in
        "PyQtGraph")
            pkg_name="pyqtgraph"
            ;;
        *)
            pkg_name="$lib"
            ;;
    esac
    
    if ! python3 -c "import ${lib}" 2>/dev/null; then
        MISSING_LIBS+=("$pkg_name")
        echo "  ⚠️  $lib: NOT FOUND"
    else
        echo "  ✅ $lib: OK"
    fi
done

if [ ${#MISSING_LIBS[@]} -gt 0 ]; then
    echo ""
    echo "❌ Error: Critical libraries are missing: ${MISSING_LIBS[*]}"
    echo ""
    echo "Attempting to install missing libraries..."
    for pkg in "${MISSING_LIBS[@]}"; do
        echo "  Installing $pkg..."
        pip install -q "$pkg" || echo "    ⚠️  Failed to install $pkg"
    done
    
    # Re-check using import names
    STILL_MISSING=()
    for lib in "${CRITICAL_LIBS[@]}"; do
        if ! python3 -c "import ${lib}" 2>/dev/null; then
            # Map back to package name for installation command
            pkg_name="$lib"
            case "$lib" in
                "PyQtGraph")
                    pkg_name="pyqtgraph"
                    ;;
            esac
            STILL_MISSING+=("$pkg_name")
        fi
    done
    
    if [ ${#STILL_MISSING[@]} -gt 0 ]; then
        echo ""
        echo "❌ Warning: Some libraries could not be installed: ${STILL_MISSING[*]}"
        echo "   The application may not work correctly."
        echo "   Please install them manually:"
        echo "   source venv/bin/activate"
        echo "   pip install ${STILL_MISSING[*]}"
        echo ""
    else
        echo "✅ All critical libraries are now installed"
    fi
else
    echo "✅ All critical libraries verified"
fi
echo ""

# Check and install Qt/XCB system dependencies
echo "🔍 Checking Qt6 system dependencies..."
MISSING_PACKAGES=()

# Required Qt6 XCB libraries
QT_PACKAGES=(
    "libxcb-cursor0"
    "libxcb-xinerama0"
    "libxcb-xinput0"
    "libxcb-icccm4"
    "libxcb-image0"
    "libxcb-keysyms1"
    "libxcb-randr0"
    "libxcb-render0"
    "libxcb-render-util0"
    "libxcb-shape0"
    "libxcb-sync1"
    "libxcb-xfixes0"
    "libxcb-xkb1"
    "libegl1"
    "libgl1"
    "libxkbcommon-x11-0"
)

# Optional but recommended libraries
OPTIONAL_PACKAGES=(
    "lm-sensors"
    "sensors"
)

# Check which packages are missing
for package in "${QT_PACKAGES[@]}"; do
    if ! dpkg -l 2>/dev/null | grep -q "^ii.*${package}"; then
        MISSING_PACKAGES+=("$package")
    fi
done

# Check optional packages
MISSING_OPTIONAL=()
for package in "${OPTIONAL_PACKAGES[@]}"; do
    if ! dpkg -l 2>/dev/null | grep -q "^ii.*${package}"; then
        MISSING_OPTIONAL+=("$package")
    fi
done

# Install missing packages
if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo "📦 Installing missing Qt6 dependencies..."
    echo "   Packages to install: ${MISSING_PACKAGES[*]}"
    
    if sudo apt install -y "${MISSING_PACKAGES[@]}"; then
        echo "✅ All Qt6 dependencies installed successfully"
    else
        echo "⚠️  Warning: Failed to install some Qt6 dependencies."
        echo "   Missing packages: ${MISSING_PACKAGES[*]}"
        echo "   You may need to install them manually:"
        echo "   sudo apt install ${MISSING_PACKAGES[*]}"
    fi
    echo ""
else
    echo "✅ All Qt6 system dependencies are already installed"
    echo ""
fi

# Offer to install optional packages
if [ ${#MISSING_OPTIONAL[@]} -gt 0 ]; then
    echo "💡 Optional packages available:"
    echo "   Packages: ${MISSING_OPTIONAL[*]}"
    echo "   These can improve sensor readings and system monitoring."
    read -p "   Install optional packages? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if sudo apt install -y "${MISSING_OPTIONAL[@]}" 2>/dev/null; then
            echo "✅ Optional packages installed"
        else
            echo "⚠️  Could not install optional packages (non-critical)"
        fi
    fi
    echo ""
fi

# Hardware detection and driver installation
if [ -f "$SCRIPT_DIR/check_and_install_drivers.py" ]; then
    echo "🔍 Checking hardware and installing drivers if needed..."
    
    # Use venv Python if available, otherwise system Python
    if [ -f "$SCRIPT_DIR/venv/bin/python3" ]; then
        PYTHON_CMD="$SCRIPT_DIR/venv/bin/python3"
    else
        PYTHON_CMD="python3"
    fi
    
    # Run hardware detection and driver installation
    # This will detect hardware and offer to install drivers
    if $PYTHON_CMD "$SCRIPT_DIR/check_and_install_drivers.py"; then
        echo ""
    else
        echo "⚠️  Warning: Hardware detection had issues, but continuing installation..."
        echo "   You can run driver detection later with:"
        echo "   $PYTHON_CMD $SCRIPT_DIR/check_and_install_drivers.py"
        echo ""
    fi
else
    echo "⚠️  Note: Hardware detection script not found, skipping driver check."
    echo ""
fi

# Make launcher executable
chmod +x asus-control-launcher.sh

# Install desktop entry
DESKTOP_FILE="$HOME/.local/share/applications/asus-control.desktop"
DESKTOP_DIR="$(dirname "$DESKTOP_FILE")"
ICON_FILE="$SCRIPT_DIR/img/icon.png"
# Fallback to JPG if PNG doesn't exist
if [ ! -f "$ICON_FILE" ]; then
    ICON_FILE="$SCRIPT_DIR/img/icon.jpg"
fi
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
APP_ICON_PATH="$ICON_DIR/asus-control.png"

mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR"

# Copy icon to standard location with multiple sizes for icon theme
if [ -f "$ICON_FILE" ]; then
    # Create multiple icon sizes for proper Linux icon theme support
    ICON_NAME="asus-control"
    ICON_ROOT_DIR="$HOME/.local/share/icons/hicolor"
    
    # Icon sizes to create
    ICON_SIZES=(16 24 32 48 64 128 256 512)
    
    echo "📦 Installing icon in multiple sizes for icon theme..."
    
    # Use Python to create properly sized icons with transparency preserved
    python3 << PYTHON_EOF
from PIL import Image
from pathlib import Path
import sys

source_icon = Path("$ICON_FILE")
if not source_icon.exists():
    print(f"Error: Icon not found at {source_icon}", file=sys.stderr)
    sys.exit(1)

img = Image.open(source_icon)
base_dir = Path("$ICON_ROOT_DIR")

for size in [16, 24, 32, 48, 64, 128, 256, 512]:
    icon_dir = base_dir / f"{size}x{size}/apps"
    icon_dir.mkdir(parents=True, exist_ok=True)
    icon_path = icon_dir / "${ICON_NAME}.png"
    resized = img.resize((size, size), Image.Resampling.LANCZOS)
    resized.save(icon_path, "PNG")
    print(f"  ✅ Created {size}x{size} icon")

PYTHON_EOF
    
    # Update icon cache
    if command -v gtk-update-icon-cache > /dev/null 2>&1; then
        gtk-update-icon-cache -f -t "$ICON_ROOT_DIR" > /dev/null 2>&1
    fi
    
    # Use icon theme name (not path) for proper transparency support
    ICON_REF="$ICON_NAME"
else
    # Fallback to absolute path if icon not found
    echo "⚠️  Warning: Icon file not found at $ICON_FILE"
    ICON_REF="$ICON_FILE"
fi

# Create desktop entry with absolute path
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Daemon Breathalyzer
Comment=Modern GUI for ASUS laptop fan curve configuration with system monitoring and log analysis
Exec=$SCRIPT_DIR/asus-control-launcher.sh
Path=$SCRIPT_DIR
Icon=$ICON_REF
Terminal=false
Categories=System;Settings;HardwareSettings;
StartupNotify=true
Keywords=asus;fan;temperature;cooling;laptop;control;
EOF

chmod +x "$DESKTOP_FILE"

# Clean up splash image before completion message
cleanup_splash

echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "All dependencies have been installed:"
echo "  ✅ Python virtual environment"
echo "  ✅ Python packages (PyQt6, PyQtGraph, etc.)"
echo "  ✅ Qt6 system libraries (XCB, OpenGL, etc.)"
echo ""
echo "The application has been installed and added to your application menu."
echo ""
echo "You can now:"
echo "  1. Launch it from your application menu (search for 'Daemon Breathalyzer')"
echo "  2. Or run it directly: ./asus-control-launcher.sh"
echo "  3. Or run it from terminal: source venv/bin/activate && python3 run.py"
echo ""
echo "To uninstall, remove:"
echo "  - $DESKTOP_FILE"
echo "  - $SCRIPT_DIR/venv (optional)"
echo ""
echo "Note: System packages (Qt6 libraries) remain installed for other applications."
echo ""

