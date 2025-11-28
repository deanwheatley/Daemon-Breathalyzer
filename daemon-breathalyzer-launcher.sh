#!/bin/bash
# Daemon Breathalyzer Launcher
# Automatically handles virtual environment and launches the application

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Log file for debugging
LOG_FILE="$HOME/.local/share/daemon-breathalyzer/launcher.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Function to show error dialog
show_error() {
    local message="$1"
    echo "$(date): ERROR: $message" >> "$LOG_FILE"
    
    if command -v zenity > /dev/null 2>&1; then
        zenity --error --text="$message" --title="Daemon Breathalyzer Error" 2>/dev/null &
    elif command -v kdialog > /dev/null 2>&1; then
        kdialog --error "$message" --title "Daemon Breathalyzer Error" 2>/dev/null &
    else
        # Fallback: try to show in terminal if available
        echo "ERROR: $message" >&2
        echo "Check log file: $LOG_FILE" >&2
    fi
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    # Try to create venv automatically
    echo "Virtual environment not found. Creating it..."
    
    # Check if python3-venv is available
    if ! python3 -m venv --help > /dev/null 2>&1; then
        # Show error dialog if possible
        if command -v zenity > /dev/null 2>&1; then
            zenity --error --text="python3-venv is not installed.\n\nPlease install it with:\nsudo apt install python3-venv\n\nThen run the setup script:\npython3 setup_venv.py" --title="Setup Required"
        else
            echo "Error: python3-venv is not installed."
            echo "Please install it with: sudo apt install python3-venv"
            echo "Then run: python3 setup_venv.py"
            read -p "Press Enter to exit..."
        fi
        exit 1
    fi
    
    python3 -m venv venv
    
    if [ $? -ne 0 ]; then
        if command -v zenity > /dev/null 2>&1; then
            zenity --error --text="Failed to create virtual environment.\n\nPlease run the setup script manually:\npython3 setup_venv.py" --title="Setup Error"
        else
            echo "Failed to create virtual environment."
            echo "Please run: python3 setup_venv.py"
            read -p "Press Enter to exit..."
        fi
        exit 1
    fi
fi

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if ! python3 -c "import PyQt6" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -q -r requirements.txt
    
    if [ $? -ne 0 ]; then
        if command -v zenity > /dev/null 2>&1; then
            zenity --error --text="Failed to install dependencies.\n\nPlease run manually:\nsource venv/bin/activate\npip install -r requirements.txt" --title="Installation Error"
        else
            echo "Failed to install dependencies."
            echo "Please run: pip install -r requirements.txt"
            read -p "Press Enter to exit..."
        fi
        exit 1
    fi
fi

# Run the application with error handling
echo "$(date): Starting Daemon Breathalyzer..." >> "$LOG_FILE"
python3 run.py >> "$LOG_FILE" 2>&1

# Capture exit code
EXIT_CODE=$?

# Check if application failed
if [ $EXIT_CODE -ne 0 ]; then
    ERROR_MSG="Application failed to start (exit code: $EXIT_CODE).\n\n"
    ERROR_MSG+="Check the log file for details:\n$LOG_FILE\n\n"
    
    # Try to extract specific error from log
    if grep -q "xcb-cursor0\|libxcb-cursor0\|Qt platform plugin" "$LOG_FILE" 2>/dev/null; then
        ERROR_MSG+="Qt platform plugin error detected.\n"
        ERROR_MSG+="Please install: sudo apt install libxcb-cursor0"
    fi
    
    show_error "$ERROR_MSG"
fi

# Deactivate virtual environment
deactivate

exit $EXIT_CODE

