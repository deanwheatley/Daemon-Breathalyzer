# How to Run the Daemon Breathalyzer Application

## Quick Start (Easiest Method)

1. **Navigate to the project directory:**
   ```bash
   cd ~/projects/daemon-breathalyzer
   ```

2. **Create a virtual environment (if you haven't already):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Run the application:**
   ```bash
   python run.py
   ```

   That's it! The app will:
   - Automatically check for dependencies
   - Show a dialog if anything is missing
   - Guide you through installation

## Step-by-Step Instructions

### First Time Setup

1. **Open a terminal and navigate to the project:**
   ```bash
   cd ~/projects/daemon-breathalyzer
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
   
   You should see `(venv)` in your terminal prompt, indicating the virtual environment is active.

3. **Install dependencies (optional - app can do this automatically):**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python run.py
   ```

### Running After First Setup

Once you've set up the virtual environment, you only need to:

```bash
cd ~/projects/daemon-breathalyzer
source venv/bin/activate
python run.py
```

## Alternative Ways to Run

### Method 1: Using run.py (Recommended)
```bash
python run.py
```

### Method 2: Using src/main.py directly
```bash
python src/main.py
```

### Method 3: Make run.py executable
```bash
chmod +x run.py
./run.py
```

## What Happens When You Run It

1. **Dependency Check**: The app automatically checks for all required dependencies
2. **Dependency Dialog** (if needed): Shows what's missing with installation options
3. **Main Window**: Opens with Dashboard, Fan Curves, Profiles, and Settings tabs

## Troubleshooting

### "Command not found: python"
Try using `python3` instead:
```bash
python3 run.py
```

### "No module named 'PyQt6'"
The app will show a dependency dialog. Alternatively, install manually:
```bash
pip install -r requirements.txt
```

### Virtual environment not activating
Make sure you're in the project directory:
```bash
cd ~/projects/daemon-breathalyzer
source venv/bin/activate
```

### Permission denied on run.py
Make it executable:
```bash
chmod +x run.py
```

## Quick Reference

```bash
# Navigate to project
cd ~/projects/daemon-breathalyzer

# Activate virtual environment
source venv/bin/activate

# Run the app
python run.py

# Deactivate virtual environment (when done)
deactivate
```

## Features Available

Once running, you'll have access to:
- **Dashboard**: Real-time system monitoring
- **Fan Curves**: Interactive fan curve editor (requires asusctl)
- **Profiles**: Save/load custom fan curve profiles
- **Help Menu**: Dependency checker, About dialog

Enjoy using Daemon Breathalyzer! 🚀


