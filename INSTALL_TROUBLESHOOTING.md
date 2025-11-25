# Installation Troubleshooting

## Common Issues

### Issue: "ensurepip is not available"

**Error Message:**
```
The virtual environment was not created successfully because ensurepip is not
available. On Debian/Ubuntu systems, you need to install the python3-venv
package using the following command.

    apt install python3.12-venv
```

**Solution:**

Install the version-specific venv package for your Python version:

```bash
# Check your Python version
python3 --version

# Install the matching venv package
# For Python 3.12:
sudo apt install python3.12-venv

# For Python 3.11:
sudo apt install python3.11-venv

# For Python 3.10:
sudo apt install python3.10-venv

# Or install the generic package (may work for some versions):
sudo apt install python3-venv
```

**After installing, run the installer again:**
```bash
./install.sh
```

### Issue: "python3-venv is not installed"

**Solution:**

The installer now checks if venv is actually functional. If you see this error:

1. Install the venv package for your Python version:
   ```bash
   python3 --version  # Check version
   sudo apt install python3.X-venv  # Replace X with your version
   ```

2. Verify installation:
   ```bash
   python3 -m venv --help  # Should work without errors
   ```

3. Try creating a test venv:
   ```bash
   python3 -m venv test_venv
   rm -rf test_venv
   ```

### Issue: Virtual Environment Already Exists

**Solution:**

The installer will ask if you want to recreate it. If you're having issues:

```bash
# Remove the existing venv
rm -rf venv

# Run installer again
./install.sh
```

### Issue: Permission Denied

**Solution:**

Make sure the install script is executable:

```bash
chmod +x install.sh
./install.sh
```

### Issue: Desktop Entry Not Created

**Solution:**

The desktop entry is created in:
```
~/.local/share/applications/asus-control.desktop
```

If it's not there:

1. Check if the directory exists:
   ```bash
   mkdir -p ~/.local/share/applications
   ```

2. Manually create the desktop entry or run the installer again.

3. Refresh the application menu:
   ```bash
   update-desktop-database ~/.local/share/applications
   ```

## Manual Installation Steps

If the installer continues to fail, you can install manually:

### 1. Install Python venv package

```bash
# Check Python version
python3 --version

# Install matching venv package
sudo apt install python3.12-venv  # Adjust version as needed
```

### 2. Create virtual environment

```bash
cd ~/projects/asus-control
python3 -m venv venv
```

### 3. Activate and install dependencies

```bash
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Make launcher executable

```bash
chmod +x asus-control-launcher.sh
```

### 5. Create desktop entry manually

```bash
cat > ~/.local/share/applications/asus-control.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=ASUS Fan Control
Comment=Modern GUI for ASUS laptop fan curve configuration with system monitoring
Exec=/home/dean/projects/asus-control/asus-control-launcher.sh
Path=/home/dean/projects/asus-control
Icon=applications-system
Terminal=false
Categories=System;Settings;HardwareSettings;
StartupNotify=true
Keywords=asus;fan;temperature;cooling;laptop;control;
EOF

chmod +x ~/.local/share/applications/asus-control.desktop
update-desktop-database ~/.local/share/applications
```

## Verification

After installation, verify everything works:

```bash
# Check venv exists
ls -la venv/bin/activate

# Check dependencies installed
source venv/bin/activate
pip list | grep -E "(PyQt6|psutil)"

# Test run
python3 run.py
```

## Getting Help

If you continue to have issues:

1. Check Python version: `python3 --version`
2. Check if venv package is installed: `dpkg -l | grep python3.*venv`
3. Try manual installation steps above
4. Check system logs for errors

