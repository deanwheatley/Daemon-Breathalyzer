# Daemon Breathalyzer Package Installer

## 📦 Complete Distribution Package

This directory contains the complete package installer for **Daemon Breathalyzer** - a modern GUI application for ASUS laptop fan curve configuration with system monitoring and log analysis.

## 🚀 Quick Installation

### For End Users:
```bash
# Download and run the installer
./daemon-breathalyzer-installer-v1.0.0.sh
```

### For Developers:
```bash
# Rebuild the package
./create-package.sh
```

## 📁 Files

- **`daemon-breathalyzer-installer-v1.0.0.sh`** - Complete self-extracting installer (1.1M)
- **`create-package.sh`** - Package builder script
- **`daemon-breathalyzer-installer.sh`** - Base installer template

## ✨ What the Installer Does

1. **System Requirements Check**
   - Verifies Python 3, pip, and sudo availability
   - Checks system compatibility

2. **Application Installation**
   - Extracts embedded application files
   - Installs to `~/daemon-breathalyzer/`
   - Sets up virtual environment

3. **Dependency Management**
   - Installs PyQt6, PyQtGraph, and all Python dependencies
   - Installs system packages (Qt6 libraries, hardware tools)
   - Detects and installs hardware-specific drivers

4. **System Integration**
   - Creates desktop entry for application menu
   - Installs application icon
   - Sets up launcher scripts

## 🎯 Features Included

- ✅ **Complete Dependency Management** - All Python and system packages
- ✅ **Hardware Detection** - Automatic driver installation for NVIDIA/AMD/Intel
- ✅ **Fan Control** - Full asusctl integration with preset curves
- ✅ **System Monitoring** - Real-time CPU/GPU/memory/temperature monitoring
- ✅ **Gaming Integration** - MangoHud FPS monitoring
- ✅ **Modern UI** - PyQt6-based interface with real-time graphs

## 🖥️ System Requirements

- **OS**: Linux (Ubuntu/Debian/Mint recommended)
- **Python**: 3.10+
- **Memory**: 512MB RAM minimum
- **Storage**: 100MB free space
- **Hardware**: ASUS laptop (for fan control features)

## 📋 Installation Process

```bash
# 1. Make executable (if needed)
chmod +x daemon-breathalyzer-installer-v1.0.0.sh

# 2. Run installer
./daemon-breathalyzer-installer-v1.0.0.sh

# 3. Launch application
# From menu: Search "Daemon Breathalyzer"
# From terminal: ~/daemon-breathalyzer/asus-control-launcher.sh
```

## 🔧 Package Contents

The installer contains:
- Complete source code (`src/`)
- All configuration files
- Installation scripts
- Hardware detection tools
- Documentation and README
- Requirements and dependencies

## 📊 Package Statistics

- **Size**: 1.1MB compressed
- **Files**: ~50 application files
- **Dependencies**: 15+ Python packages, 20+ system packages
- **Supported Hardware**: ASUS, MSI, Gigabyte motherboards
- **GPU Support**: NVIDIA, AMD, Intel

## 🎉 Ready for Distribution

This package is ready for:
- ✅ End-user distribution
- ✅ GitHub releases
- ✅ Package repositories
- ✅ Corporate deployment
- ✅ Offline installation