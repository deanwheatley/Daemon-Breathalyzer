# Dependency Management System

The Daemon Breathalyzer application includes a comprehensive dependency management system that helps users install all required dependencies automatically or with clear step-by-step instructions.

## Features

### ✅ Automatic Dependency Checking

On startup, the application automatically checks for all required dependencies:
- **Python packages** (PyQt6, PyQtGraph, psutil, etc.)
- **System commands** (nvidia-smi, sensors, asusctl)
- **Optional dependencies** (clearly marked)

### 🚀 Automatic Installation

The dependency dialog provides:
- **One-click installation** for pip-installable packages
- **Background installation** with progress indication
- **Success/failure notifications**

### 📖 Step-by-Step Instructions

For dependencies that cannot be installed automatically, the app provides:
- **Clear, detailed instructions** for manual installation
- **Copy-paste ready commands** for terminal
- **Links to official documentation** where applicable
- **Distribution-specific instructions** when needed

## How It Works

### On Startup

1. The app checks all dependencies before launching the main UI
2. If required dependencies are missing:
   - A dependency dialog appears automatically
   - Shows status of all dependencies (installed/missing)
   - Provides installation options

### Dependency Categories

#### Required Dependencies
- **PyQt6**: Main UI framework
- **PyQtGraph**: Real-time plotting
- **psutil**: System monitoring
- **PyYAML**: Configuration parsing
- **asusctl**: ASUS laptop control (if fan control features are needed)

#### Optional Dependencies
- **py3nvml**: NVIDIA GPU monitoring (falls back to nvidia-smi)
- **nvidia-smi**: NVIDIA GPU monitoring (system command)
- **sensors**: Hardware sensor monitoring (improves temperature readings)

### Installation Methods

1. **Automatic (pip)**: Click "Install via pip" button
   - Runs: `pip install <package-name>`
   - Shows progress
   - Notifies on completion

2. **Manual (System Commands)**:
   - Provides exact commands to run
   - Includes distribution-specific instructions
   - Links to official documentation

## User Experience

### Dependency Dialog Features

- **Status Icons**: ✅ Installed | ❌ Missing | ⚪ Optional
- **Color-coded Status Bar**: 
  - Green: All dependencies installed
  - Yellow: Required installed, optional missing
  - Red: Required dependencies missing
- **Expandable Instructions**: Each dependency shows detailed instructions when missing
- **Refresh Button**: Re-check dependencies after installation

### Accessing Dependency Check

- **On Startup**: Automatically shown if dependencies are missing
- **From Menu**: Help → Check Dependencies
- **Always Available**: Can be accessed anytime during use

## Example Instructions

### For PyQt6 (Automatic)
```
Automated installation:
pip install PyQt6
```

### For asusctl (Manual)
```
Manual installation:
See: https://asus-linux.org/asusctl/

Detailed instructions:
1. Visit: https://asus-linux.org/asusctl/
2. Follow the installation guide for your distribution
3. Ensure the asusd service is running:
   sudo systemctl enable --now asusd
```

### For nvidia-smi (Manual)
```
Note:
- Install NVIDIA drivers from: https://www.nvidia.com/drivers
- Or use your distribution's package manager:
  - Ubuntu/Debian: sudo apt install nvidia-driver-<version>
  - Arch: sudo pacman -S nvidia
```

## Implementation Details

### Files

- **`src/utils/dependency_checker.py`**: Core dependency checking logic
- **`src/ui/dependency_dialog.py`**: Modern dialog UI for dependency management
- **`src/main.py`**: Startup dependency check integration

### Dependency Checker Class

The `DependencyChecker` class:
- Maintains a list of all dependencies with metadata
- Checks each dependency (Python import, system command, custom function)
- Provides installation instructions
- Handles pip installation

### Status Flow

1. **Check**: Verify if dependency is available
2. **Report**: Show status to user
3. **Install**: Offer automatic installation if possible
4. **Verify**: Re-check after installation attempt
5. **Instruct**: Provide manual instructions if needed

## Benefits

✅ **User-Friendly**: No need to read documentation or figure out dependencies manually
✅ **Time-Saving**: Automatic installation for most dependencies
✅ **Clear Guidance**: Step-by-step instructions for complex installations
✅ **Always Current**: Dependency check is always up-to-date with requirements
✅ **Non-Blocking**: Can proceed with missing optional dependencies

## Future Enhancements

- [ ] Batch installation of multiple dependencies
- [ ] Dependency version checking
- [ ] Update notifications for outdated dependencies
- [ ] System package manager integration (apt, pacman, etc.)
- [ ] Dependency conflict detection


