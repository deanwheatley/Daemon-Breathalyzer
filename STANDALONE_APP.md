# Standalone Application Setup

The Daemon Breathalyzer application can be installed as a standalone app that can be launched from your application menu without needing the terminal.

## Installation

### One-Command Installation

Run the installer script:

```bash
cd ~/projects/daemon-breathalyzer
./install.sh
```

This will:
1. Check system requirements (Python, python3-venv)
2. Create virtual environment automatically
3. Install all dependencies
4. Create desktop entry in `~/.local/share/applications/`
5. Make launcher script executable

### What Gets Installed

- **Virtual Environment**: `venv/` directory in project folder
- **Desktop Entry**: `~/.local/share/applications/daemon-breathalyzer.desktop`
- **Launcher Script**: `daemon-breathalyzer-launcher.sh` (handles venv activation automatically)

## Launching the Application

After installation, you have several ways to launch:

### 1. From Application Menu (Easiest)
- Open your application menu
- Search for "Daemon Breathalyzer"
- Click to launch
- **No terminal needed!**

### 2. Double-Click Launcher
- Navigate to the project folder
- Double-click `daemon-breathalyzer-launcher.sh`
- The launcher handles everything automatically

### 3. Command Line
```bash
./daemon-breathalyzer-launcher.sh
```

## How the Launcher Works

The `daemon-breathalyzer-launcher.sh` script automatically:
- ✅ Checks if virtual environment exists (creates it if needed)
- ✅ Activates the virtual environment
- ✅ Checks for dependencies (installs if missing)
- ✅ Launches the application
- ✅ Cleans up when done

## Uninstallation

To remove the desktop entry:

```bash
rm ~/.local/share/applications/daemon-breathalyzer.desktop
```

To also remove the virtual environment:

```bash
rm -r ~/projects/daemon-breathalyzer/venv
```

## Troubleshooting

### Desktop Entry Not Appearing

After running `./install.sh`, the desktop entry should appear immediately. If it doesn't:
- Log out and log back in
- Or restart your desktop environment
- Or manually refresh: `update-desktop-database ~/.local/share/applications/`

### Launcher Shows Errors

If the launcher script encounters errors:
1. Check that `python3-venv` is installed: `sudo apt install python3-venv`
2. Run the installer again: `./install.sh`
3. Or check the launcher script manually: `bash -x daemon-breathalyzer-launcher.sh`

### Permission Denied

Make sure scripts are executable:
```bash
chmod +x install.sh daemon-breathalyzer-launcher.sh
```

## Technical Details

### Desktop Entry Location

The desktop entry is installed to:
```
~/.local/share/applications/daemon-breathalyzer.desktop
```

This is the user-specific location, so no sudo is needed.

### Launcher Script Features

- **Auto-detection**: Detects if venv exists
- **Auto-creation**: Creates venv if missing
- **Dependency checking**: Verifies dependencies are installed
- **Error handling**: Shows helpful error messages
- **GUI error dialogs**: Uses `zenity` if available for user-friendly errors

### Virtual Environment Location

The virtual environment is created in:
```
~/projects/daemon-breathalyzer/venv/
```

This keeps everything in one place and makes it easy to manage.


