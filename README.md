# Daemon Breathalyzer

A modern, minimalist GUI application for Linux Mint that allows easy fan curve configuration with live system monitoring, log analysis, and error tracking.

## ✨ Features

- **🔍 Automatic Dependency Management**: The app checks for all required dependencies on startup and provides step-by-step installation instructions
- **📊 Live System Monitoring**: Real-time CPU, GPU, memory usage, temperatures, and fan speeds
- **📈 Real-time Graphs**: Historical data visualization with beautiful charts
- **🌡️ Fan Curve Editor**: Interactive graph-based fan curve configuration with presets
- **⚙️ asusctl Integration**: Seamless integration with ASUS laptop control
- **📋 System Log Monitoring**: Real-time log viewing with journalctl integration, filtering, search, and error tracking
- **🎯 Error Tracking**: Automatic error detection and summary statistics with color-coded priority levels
- **🎨 Modern Minimalist UI**: Clean, informative, and simple to use
- **📦 Preset Curves**: Quick apply Quiet, Balanced, or Performance fan curves
- **🚀 Standalone Application**: Install once, launch from application menu - no terminal needed!

## 🎨 Modern & Minimalist Design

The application features a clean, modern UI with:
- Minimalist card-based layout
- Smooth, informative graphs
- Clear, readable metrics
- Intuitive navigation

## 🚀 Getting Started

### Prerequisites

- Linux Mint (or compatible Linux distribution)
- Python 3.10+
- `python3-venv` package (for Debian/Ubuntu: `sudo apt install python3-venv`)

### 📦 Distribution Package

For distributing the app to new users, see the `package/` folder which contains everything needed for installation. The package is automatically kept up-to-date via a Makefile rule. See `PACKAGE.md` for details.

### Installation (Standalone App) ⭐ Recommended

**One-Click Installation:**

```bash
cd ~/projects/asus-control
./install.sh
```

This will automatically:
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Add the app to your application menu
- ✅ Create a desktop launcher

**After Installation:**

Launch the app from your **Application Menu**:
- Search for "ASUS Fan Control"
- Or find it in: System → Settings → Hardware Settings
- **No terminal needed!**

### How to Launch the Application

After running the installer (`./install.sh`), you can launch the app in several ways:

**🚀 Method 1: From Application Menu (Easiest - Recommended)**
1. Open your application menu (press `Super` key or click the menu icon)
2. Search for **"ASUS Fan Control"**
3. Click the application icon to launch
4. **No terminal needed!**

The app will appear in: **System → Settings → Hardware Settings**

**🚀 Method 2: Double-Click Launcher**
1. Open your file manager
2. Navigate to: `~/projects/asus-control`
3. Double-click `asus-control-launcher.sh`
4. The app will launch automatically

**🚀 Method 3: From Terminal**
```bash
cd ~/projects/asus-control
./asus-control-launcher.sh
```

**🚀 Method 4: Manual Setup (Advanced Users Only)**
If you prefer to run manually from terminal:
```bash
cd ~/projects/asus-control
source venv/bin/activate
python3 run.py
```

**💡 Tip:** After installation, Method 1 (Application Menu) is the easiest - just search and click!

### 📖 In-App Help Documentation

The application includes comprehensive help documentation accessible from within the app:

- **Access Help:** Press `F1` or go to **Help → Help Documentation**
- **Topics Covered:**
  - Getting Started guide
  - Dashboard usage and metrics explanation
  - Fan Curve Editor tutorial
  - Profile Management guide
  - Troubleshooting common issues

All help is available offline - no internet connection required!

### What Happens When You Run It

The app will automatically:
- ✅ Check for all required dependencies
- ✅ Show a helpful dialog if anything is missing
- ✅ Provide step-by-step installation instructions
- ✅ Offer automatic pip installation where possible

**If dependencies are missing:**
- The dependency dialog appears automatically on first run
- Click "Install via pip" buttons for automatic installation
- Follow the provided instructions for manual installation when needed

## 🧪 Testing

### Running Tests

**Quick Test Run:**
```bash
cd ~/projects/asus-control
source venv/bin/activate
./run_tests.sh
```

**Manual Test Run:**
```bash
# Install test dependencies (first time)
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# View coverage report
# Open htmlcov/index.html in your browser
```

**Test Categories:**
- Unit tests: Core functionality
- Integration tests: Feature workflows
- UI tests: Widget functionality (requires Qt)

See `tests/README.md` for detailed testing documentation.

## 📚 Documentation

### In-App Help (Recommended for Users)

The easiest way to get help is from within the application:
- Press `F1` or go to **Help → Help Documentation**
- Comprehensive guides for all features
- Troubleshooting tips
- Step-by-step tutorials

### Project Documentation

Technical documentation is in the `docs/` folder:
- **FAN_CONTROL_UI_BRAINSTORM.md** - Complete feature list and technology options
- **UI_MOCKUP_DESIGN.md** - Visual design mockups and layouts
- **PROJECT_STRUCTURE.md** - Project structure and code examples

Additional user guides:
- **HOW_TO_RUN.md** - Detailed instructions on running the application
- **QUICK_START.md** - Quick start guide
- **FEATURES.md** - Complete feature overview
- **STANDALONE_APP.md** - Standalone application setup guide

## 🛠️ Development

### Project Structure

```
~/projects/asus-control/
├── docs/              # All documentation
├── src/               # Source code
│   ├── ui/           # UI components
│   │   ├── main_window.py
│   │   ├── dashboard_widgets.py
│   │   └── dependency_dialog.py
│   ├── monitoring/   # System monitoring
│   │   └── system_monitor.py
│   ├── control/      # Fan control
│   ├── utils/        # Utilities
│   │   └── dependency_checker.py
│   └── main.py       # Application entry point
├── data/             # Resources (icons, themes, presets)
├── tests/            # Test files
├── asus-control-launcher.sh  # Standalone launcher script
├── install.sh        # Installation script
├── run.py            # Launch script
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

### Testing System Monitoring

You can test the monitoring module independently:

```bash
python src/monitoring/system_monitor.py
```

This will run a console version showing real-time metrics.

## 🔧 Troubleshooting

### "python3-venv package is not installed"

**Error:** `The virtual environment was not created successfully because ensurepip is not available`

**Solution:**
```bash
sudo apt install python3.12-venv
```
(Replace `python3.12` with your Python version - check with `python3 --version`)

Then run the installer:
```bash
./install.sh
```

### "externally-managed-environment" Error

**Error:** `This environment is externally managed`

**Solution:**
The installer handles this automatically. Just run:
```bash
./install.sh
```

The installer will create a virtual environment for you.

### "Command 'python' not found"

**Error:** `Command 'python' not found, did you mean: command 'python3'`

**Solution:**
Use `python3` instead of `python`:
```bash
python3 --version
```

The installer and launcher scripts use `python3` automatically.

### "bash: venv/bin/activate: No such file or directory"

**Error:** Virtual environment doesn't exist or wasn't created properly

**Solution:**
Run the installer:
```bash
./install.sh
```

### Dependency Issues

- The app automatically checks dependencies on startup
- Use Help → Check Dependencies from the menu to re-check anytime
- Missing dependencies show clear installation instructions

### GPU Monitoring Not Working

- Ensure NVIDIA drivers are installed
- Try: `nvidia-smi` to verify GPU is accessible
- The module automatically falls back to nvidia-smi command if py3nvml fails

### Temperature Not Showing

- Install `lm-sensors`: `sudo apt install lm-sensors`
- Run: `sudo sensors-detect`
- Check: `/sys/class/thermal/` for thermal zones

## 🎯 Quick Reference

**First Time Setup:**
```bash
cd ~/projects/asus-control
./install.sh
```

**Launch Options:**
- Application Menu → Search "ASUS Fan Control"
- Double-click `asus-control-launcher.sh`
- Run `./asus-control-launcher.sh` from terminal

**Uninstall:**
```bash
rm ~/.local/share/applications/asus-control.desktop
# Optionally remove venv folder:
# rm -r ~/projects/asus-control/venv
```

## 📝 License

[To be determined]

## 🤝 Contributing

Contributions welcome! See documentation for architecture details.
