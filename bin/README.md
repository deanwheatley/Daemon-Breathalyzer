# Install Packages

This directory contains ready-to-install packages for Daemon Breathalyzer.

## 📦 Available Packages

### Archive Package
- **`daemon-breathalyzer-20251125.tar.gz`** - Complete distribution package (384K)
  - Contains all source code, scripts, and documentation
  - Extract with: `tar -xzf daemon-breathalyzer-20251125.tar.gz`
  - Then run: `cd daemon-breathalyzer-20251125 && ./install.sh`

### Quick Install Script
- **`quick-install.sh`** - One-command installer
  - Extracts archive and runs installation automatically
  - Run with: `./quick-install.sh`

### Standalone Installer
- **`install-daemon-breathalyzer.sh`** - Installer script wrapper
  - For use with extracted packages

## 🚀 Installation Methods

### Method 1: Quick Install (Recommended)
```bash
cd bin
./quick-install.sh
```

### Method 2: Manual Install
```bash
cd bin
tar -xzf daemon-breathalyzer-20251125.tar.gz
cd daemon-breathalyzer-20251125
./install.sh
```

### Method 3: Extract and Install Separately
```bash
# Extract to desired location
tar -xzf bin/daemon-breathalyzer-20251125.tar.gz -C ~/software/

# Install from extracted location
cd ~/software/daemon-breathalyzer-20251125
./install.sh
```

## 📋 Package Contents

The archive contains:
- Complete source code (`src/`)
- Installation scripts (`install.sh`)
- Launcher scripts (`asus-control-launcher.sh`)
- Desktop entry (`asus-control.desktop`)
- Documentation (`README.md`)
- Application icons (`img/`)
- Driver installation tools
- All dependencies list (`requirements.txt`)

## 🔧 System Requirements

- Linux Mint or compatible Linux distribution
- Python 3.10 or higher
- Internet connection (for downloading dependencies)
- sudo access (for installing system packages)

## 📝 Version

Package Version: 20251125
Build Date: Tue Nov 25 07:38:19 PM PST 2025

## 🆘 Support

For issues or questions:
- GitHub: https://github.com/deanwheatley/Daemon-Breathalyzer
- Email: deanwheatley@hotmail.com
- Documentation: See README.md in the package
