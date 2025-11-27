#!/bin/bash
set -e

VERSION="1.0.8"

# Create clean payload
cd /home/dean/projects/asus-control
tar czf /tmp/clean-payload.tar.gz src requirements.txt install.sh asus-control-launcher.sh run.py check_and_install_drivers.py README.md

# Create installer script with correct version
cat > /tmp/installer-head.sh << 'EOF'
#!/bin/bash
# Daemon Breathalyzer Complete Package Installer
# Self-extracting installer with embedded application

set -e

INSTALLER_VERSION="1.2.0"
APP_NAME="Daemon Breathalyzer"
INSTALL_DIR="$HOME/daemon-breathalyzer"
TEMP_DIR="/tmp/daemon-breathalyzer-install-$$"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  $APP_NAME Installer v$INSTALLER_VERSION${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
}

trap cleanup EXIT

check_requirements() {
    print_info "Checking system requirements..."
    
    if ! command -v python3 >/dev/null 2>&1; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Install pip if not available
    if ! python3 -m pip --version >/dev/null 2>&1; then
        print_warning "pip not found, installing..."
        if command -v apt >/dev/null 2>&1; then
            sudo apt update && sudo apt install -y python3-pip
        elif command -v yum >/dev/null 2>&1; then
            sudo yum install -y python3-pip
        else
            print_error "Cannot install pip automatically. Please install python3-pip manually."
            exit 1
        fi
        
        if ! python3 -m pip --version >/dev/null 2>&1; then
            print_error "Failed to install pip"
            exit 1
        fi
        print_success "pip installed"
    fi
    
    if ! command -v sudo >/dev/null 2>&1; then
        print_error "sudo is required for system package installation"
        exit 1
    fi
    
    print_success "System requirements met"
}

extract_package() {
    print_info "Extracting application package..."
    
    mkdir -p "$TEMP_DIR"
    
    # Find the start of the embedded tar.gz
    ARCHIVE_LINE=$(awk '/^__ARCHIVE_BELOW__/ {print NR + 1; exit 0; }' "$0")
    
    if [ -z "$ARCHIVE_LINE" ]; then
        print_error "Archive marker not found in installer"
        exit 1
    fi
    
    # Extract the embedded archive
    if ! tail -n +$ARCHIVE_LINE "$0" | tar -xzf - -C "$TEMP_DIR" 2>/dev/null; then
        print_error "Failed to extract package. Installer may be corrupted."
        exit 1
    fi
    
    print_success "Package extracted"
}

install_application() {
    print_info "Installing application to $INSTALL_DIR..."
    
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "Removing existing installation..."
        rm -rf "$INSTALL_DIR"
    fi
    
    mkdir -p "$INSTALL_DIR"
    cp -r "$TEMP_DIR"/* "$INSTALL_DIR"
    chmod +x "$INSTALL_DIR/install.sh"
    chmod +x "$INSTALL_DIR/asus-control-launcher.sh"
    
    print_success "Application files installed"
}

run_installer() {
    print_info "Running application installer..."
    
    cd "$INSTALL_DIR"
    
    if ./install.sh; then
        print_success "Application installed successfully"
    else
        print_error "Installation failed"
        exit 1
    fi
}

main() {
    print_header
    
    check_requirements
    extract_package
    install_application
    run_installer
    
    echo ""
    print_success "Installation completed successfully!"
    echo ""
    print_info "Launch the application from:"
    echo "  • Application Menu: Search for 'Daemon Breathalyzer'"
    echo "  • Command line: $INSTALL_DIR/asus-control-launcher.sh"
    echo ""
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

exit 0

__ARCHIVE_BELOW__
EOF

# Combine script and payload
cat /tmp/installer-head.sh /tmp/clean-payload.tar.gz > bin/daemon-breathalyzer-installer-v1.2.0.sh
chmod +x bin/daemon-breathalyzer-installer-v1.2.0.sh

# Cleanup
rm /tmp/installer-head.sh /tmp/clean-payload.tar.gz

echo "✅ Fixed installer created: daemon-breathalyzer-installer-v1.2.0.sh"