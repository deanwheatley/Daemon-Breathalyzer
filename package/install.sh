#!/bin/bash
# Daemon Breathalyzer Installer
# Sets up the application and creates desktop entry
# Automatically installs all required system dependencies

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

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
echo "📥 Installing Python dependencies..."
pip install -q --upgrade pip

# Install critical packages first
echo "  Installing critical packages..."
CRITICAL_PACKAGES=("PyQt6" "PyQtGraph" "psutil" "numpy" "PyYAML")
for pkg in "${CRITICAL_PACKAGES[@]}"; do
    echo "    Installing $pkg..."
    if ! pip install -q "$pkg"; then
        echo "    ⚠️  Failed to install $pkg, trying with --user flag..."
        if ! pip install -q --user "$pkg"; then
            echo "    ❌ Failed to install $pkg with both methods"
        else
            echo "    ✅ Installed $pkg with --user flag"
        fi
    else
        echo "    ✅ Installed $pkg"
    fi
done

# Install remaining dependencies from requirements.txt
echo "  Installing remaining dependencies from requirements.txt..."
if ! pip install -q -r requirements.txt; then
    echo "⚠️  Some dependencies from requirements.txt failed to install."
    echo "   Trying individual installation..."
    
    # Try installing each line individually
    while IFS= read -r line; do
        # Skip empty lines and comments
        if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
            pkg_name=$(echo "$line" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1 | cut -d'!' -f1)
            echo "    Installing $pkg_name..."
            if ! pip install -q "$line"; then
                echo "    ⚠️  Failed to install $pkg_name"
            fi
        fi
    done < requirements.txt
fi

echo "✅ Python dependencies installation completed"
echo ""

# Verify critical Python libraries are installed
echo "🔍 Verifying critical libraries..."
MISSING_LIBS=()

# Define libraries with their display name, import name, and package name
# Format: "display_name:import_name:package_name"
CRITICAL_LIBS=(
    "PyQt6:PyQt6:PyQt6"
    "PyQtGraph:pyqtgraph:pyqtgraph"
    "psutil:psutil:psutil"
    "numpy:numpy:numpy"
    "PyYAML:yaml:PyYAML"
)

# Use venv Python and pip if available, otherwise system Python
if [ -f "$SCRIPT_DIR/venv/bin/python3" ]; then
    PYTHON_CMD="$SCRIPT_DIR/venv/bin/python3"
    PIP_CMD="$SCRIPT_DIR/venv/bin/pip"
else
    PYTHON_CMD="python3"
    PIP_CMD="pip"
fi

for lib_entry in "${CRITICAL_LIBS[@]}"; do
    # Parse the entry: display_name:import_name:package_name
    IFS=':' read -r display_name import_name pkg_name <<< "$lib_entry"
    
    # Check if library is importable using the correct Python interpreter
    if ! "$PYTHON_CMD" -c "import ${import_name}" 2>/dev/null; then
        MISSING_LIBS+=("$pkg_name")
        echo "  ⚠️  $display_name: NOT FOUND"
    else
        echo "  ✅ $display_name: OK"
    fi
done

if [ ${#MISSING_LIBS[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  Some critical libraries are missing: ${MISSING_LIBS[*]}"
    echo ""
    echo "Attempting to install missing libraries with multiple methods..."
    for pkg in "${MISSING_LIBS[@]}"; do
        echo "  Installing $pkg..."
        
        # Try multiple installation methods
        if "$PIP_CMD" install -q "$pkg" 2>/dev/null; then
            echo "    ✅ Successfully installed $pkg"
        elif "$PIP_CMD" install -q --user "$pkg" 2>/dev/null; then
            echo "    ✅ Successfully installed $pkg with --user flag"
        elif "$PIP_CMD" install -q --force-reinstall "$pkg" 2>/dev/null; then
            echo "    ✅ Successfully reinstalled $pkg"
        else
            echo "    ⚠️  Failed to install $pkg with all methods"
            
            # For PyQt6, try alternative installation
            if [[ "$pkg" == "PyQt6" ]]; then
                echo "    🔄 Trying PyQt6 alternative installation..."
                if "$PIP_CMD" install -q --index-url https://pypi.org/simple/ PyQt6 2>/dev/null; then
                    echo "    ✅ PyQt6 installed via alternative method"
                fi
            fi
        fi
    done
    
    # Re-check using import names with venv Python
    echo "  🔍 Re-verifying installations..."
    STILL_MISSING=()
    for lib_entry in "${CRITICAL_LIBS[@]}"; do
        IFS=':' read -r display_name import_name pkg_name <<< "$lib_entry"
        if ! "$PYTHON_CMD" -c "import ${import_name}" 2>/dev/null; then
            STILL_MISSING+=("$pkg_name")
            echo "    ❌ $display_name: Still missing"
        else
            echo "    ✅ $display_name: Now available"
        fi
    done
    
    if [ ${#STILL_MISSING[@]} -gt 0 ]; then
        echo ""
        echo "❌ Warning: Some critical libraries could not be installed: ${STILL_MISSING[*]}"
        echo "   The application may not work correctly."
        echo "   Manual installation commands:"
        echo "   source venv/bin/activate"
        for pkg in "${STILL_MISSING[@]}"; do
            echo "   pip install $pkg"
        done
        echo ""
        echo "   If PyQt6 fails, try:"
        echo "   sudo apt install python3-pyqt6 python3-pyqt6-dev"
        echo ""
    else
        echo "✅ All critical libraries are now installed and verified"
    fi
else
    echo "✅ All critical libraries verified"
fi
echo ""

# Check and install Qt/XCB system dependencies
echo "🔍 Checking Qt6 system dependencies..."
MISSING_PACKAGES=()

# Required Qt6 XCB libraries and Python packages
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
    "libxcb1"
    "libxcb-glx0"
    "libxcb-shm0"
    "python3-pyqt6"
    "python3-pyqt6-dev"
    "python3-numpy"
    "python3-yaml"
)

# Generic fan control packages for non-ASUS laptops
FAN_CONTROL_PACKAGES=(
    "lm-sensors"
    "fancontrol"
    "i8kutils"
)

# Gaming and monitoring packages
GAMING_PACKAGES=(
    "mangohud"
)

# Optional but recommended libraries
OPTIONAL_PACKAGES=(
    "lm-sensors"
    "sensors"
)

# Check which packages are missing
for package in "${QT_PACKAGES[@]}"; do
    if ! dpkg -l 2>/dev/null | grep -q "^ii.*${package}" && ! dpkg -l 2>/dev/null | grep -q "^ii  ${package}"; then
        MISSING_PACKAGES+=("$package")
    fi
done

# Check fan control packages
for package in "${FAN_CONTROL_PACKAGES[@]}"; do
    if ! dpkg -l 2>/dev/null | grep -q "^ii.*${package}" && ! dpkg -l 2>/dev/null | grep -q "^ii  ${package}"; then
        MISSING_PACKAGES+=("$package")
    fi
done

# Check gaming packages
MISSING_GAMING=()
for package in "${GAMING_PACKAGES[@]}"; do
    if ! dpkg -l 2>/dev/null | grep -q "^ii.*${package}"; then
        MISSING_GAMING+=("$package")
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
    echo "📦 Installing system dependencies..."
    echo "   Packages: ${MISSING_PACKAGES[*]}"
    echo ""
    echo "   ⚠️  This requires sudo access. Please enter your password when prompted."
    echo ""
    
    # Update package list first
    echo "   Updating package list..."
    sudo apt update -qq || echo "   ⚠️  Update had issues (continuing)"
    
    echo "   Installing packages..."
    if sudo apt install -y "${MISSING_PACKAGES[@]}"; then
        echo "✅ All system dependencies installed successfully"
        
        # Setup sensors for Dell/generic laptops
        if ! command -v asusctl >/dev/null 2>&1; then
            echo ""
            echo "🔧 Setting up fan control for non-ASUS laptop..."
            if command -v sensors-detect >/dev/null 2>&1; then
                echo "   Running sensors-detect (answer YES to all)..."
                echo "   This detects your hardware sensors."
                sudo sensors-detect --auto || echo "   ⚠️  Sensor detection had issues"
            fi
            
            if command -v pwmconfig >/dev/null 2>&1; then
                echo ""
                echo "   💡 To configure fan control, run: sudo pwmconfig"
                echo "   Then enable the service: sudo systemctl enable fancontrol"
            fi
        fi
        
        # If we installed system PyQt6, we may need to ensure it's accessible in venv
        if [[ " ${MISSING_PACKAGES[*]} " =~ " python3-pyqt6 " ]]; then
            echo "   🔗 Linking system PyQt6 to virtual environment..."
            SITE_PACKAGES_DIR="$SCRIPT_DIR/venv/lib/python*/site-packages"
            SYSTEM_PYQT6="/usr/lib/python3/dist-packages/PyQt6"
            
            if [ -d "$SYSTEM_PYQT6" ] && [ -d $SITE_PACKAGES_DIR ]; then
                for site_dir in $SITE_PACKAGES_DIR; do
                    if [ ! -e "$site_dir/PyQt6" ]; then
                        ln -sf "$SYSTEM_PYQT6" "$site_dir/PyQt6" 2>/dev/null || true
                        echo "     ✅ Linked PyQt6 to $site_dir"
                    fi
                done
            fi
        fi
    else
        echo "⚠️  Warning: Failed to install some system dependencies."
        echo "   Missing packages: ${MISSING_PACKAGES[*]}"
        echo "   You may need to install them manually:"
        echo "   sudo apt install ${MISSING_PACKAGES[*]}"
    fi
    echo ""
else
    echo "✅ All system dependencies are already installed"
    
    # Still setup sensors if needed
    if ! command -v asusctl >/dev/null 2>&1 && command -v sensors-detect >/dev/null 2>&1; then
        echo ""
        echo "🔧 Configuring sensors for fan monitoring..."
        sudo sensors-detect --auto 2>/dev/null || true
    fi
    echo ""
fi

# Install gaming packages (MangoHud for FPS monitoring)
if [ ${#MISSING_GAMING[@]} -gt 0 ]; then
    echo "🎮 Installing gaming monitoring packages..."
    echo "   Packages: ${MISSING_GAMING[*]}"
    echo "   - mangohud: Accurate FPS monitoring for games"
    
    if sudo apt install -y "${MISSING_GAMING[@]}"; then
        echo "✅ Gaming packages installed successfully"
    else
        echo "⚠️  Warning: Failed to install gaming packages."
        echo "   FPS monitoring will use estimation instead of accurate readings."
        echo "   You can install manually: sudo apt install ${MISSING_GAMING[*]}"
    fi
    echo ""
else
    echo "✅ Gaming monitoring packages already installed"
    echo ""
fi

# Offer to install optional packages
if [ ${#MISSING_OPTIONAL[@]} -gt 0 ]; then
    echo "💡 Optional packages available:"
    echo "   Packages: ${MISSING_OPTIONAL[*]}"
    echo "   These can improve sensor readings and system monitoring."
    echo "   - lm-sensors: Better temperature monitoring"
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
chmod +x daemon-breathalyzer-launcher.sh

# Install desktop entry
DESKTOP_FILE="$HOME/.local/share/applications/daemon-breathalyzer.desktop"
DESKTOP_DIR="$(dirname "$DESKTOP_FILE")"
ICON_FILE="$SCRIPT_DIR/img/icon.png"
# Fallback to JPG if PNG doesn't exist
if [ ! -f "$ICON_FILE" ]; then
    ICON_FILE="$SCRIPT_DIR/img/icon.jpg"
fi
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
APP_ICON_PATH="$ICON_DIR/daemon-breathalyzer.png"

mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR"

# Copy icon to standard location with multiple sizes for icon theme
if [ -f "$ICON_FILE" ]; then
    # Create multiple icon sizes for proper Linux icon theme support
    ICON_NAME="daemon-breathalyzer"
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
Comment=Modern GUI for laptop fan curve configuration with system monitoring and log analysis
Exec=$SCRIPT_DIR/daemon-breathalyzer-launcher.sh
Path=$SCRIPT_DIR
Icon=$ICON_REF
Terminal=false
Categories=System;Settings;HardwareSettings;
StartupNotify=true
Keywords=fan;temperature;cooling;laptop;control;daemon;breathalyzer;
EOF

chmod +x "$DESKTOP_FILE"

echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "All dependencies have been installed:"
echo "  ✅ Python virtual environment"
echo "  ✅ Python packages (PyQt6, PyQtGraph, etc.)"
echo "  ✅ Qt6 system libraries (XCB, OpenGL, etc.)"
echo "  ✅ MangoHud for accurate FPS monitoring"
echo ""
echo "The application has been installed and added to your application menu."
echo ""
echo "You can now:"
echo "  1. Launch it from your application menu (search for 'Daemon Breathalyzer')"
echo "  2. Or run it directly: ./daemon-breathalyzer-launcher.sh"
echo "  3. Or run it from terminal: source venv/bin/activate && python3 run.py"
echo ""
echo "To uninstall, remove:"
echo "  - $DESKTOP_FILE"
echo "  - $SCRIPT_DIR/venv (optional)"
echo ""
echo "Note: System packages (Qt6 libraries) remain installed for other applications."
echo ""

