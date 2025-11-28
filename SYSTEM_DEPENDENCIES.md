# System Dependencies

This document lists all system packages (apt packages) required for the Daemon Breathalyzer application.

## Required System Packages

### Python Environment
- `python3` - Python 3.10 or higher
- `python3-venv` - Virtual environment support (version-specific: python3.12-venv for Python 3.12)

### Qt6 Dependencies (for PyQt6)
- `libxcb-cursor0` - XCB cursor support (required for Qt 6.5+)
- `libxcb-xinerama0` - XCB Xinerama extension (for multi-monitor support)
- `libxcb-xinput0` - XCB XInput extension (for input handling)
- `libxcb-icccm4` - XCB ICCCM support
- `libxcb-image0` - XCB image support
- `libxcb-keysyms1` - XCB keysym support
- `libxcb-randr0` - XCB RandR extension (for display configuration)
- `libxcb-render0` - XCB render extension
- `libxcb-render-util0` - XCB render utilities
- `libxcb-shape0` - XCB shape extension
- `libxcb-sync1` - XCB sync extension
- `libxcb-xfixes0` - XCB XFixes extension
- `libxcb-xkb1` - XCB XKB support

### Graphics and Display
- `libegl1` - EGL library (for hardware acceleration)
- `libgl1` - OpenGL library
- `libxkbcommon-x11-0` - XKB common library for X11

### Optional but Recommended
- `lm-sensors` - Hardware sensor monitoring (for better temperature readings)
- `nvidia-utils` - NVIDIA utilities (if you have NVIDIA GPU)

## Automatic Installation

The `install.sh` script now automatically checks for and installs these dependencies.

## Manual Installation

If you prefer to install manually:

```bash
# Python venv (adjust version for your Python version)
sudo apt install python3.12-venv

# Qt6 XCB dependencies
sudo apt install libxcb-cursor0 libxcb-xinerama0 libxcb-xinput0 \
                 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
                 libxcb-randr0 libxcb-render0 libxcb-render-util0 \
                 libxcb-shape0 libxcb-sync1 libxcb-xfixes0 libxcb-xkb1 \
                 libegl1 libgl1 libxkbcommon-x11-0

# Optional
sudo apt install lm-sensors
```


