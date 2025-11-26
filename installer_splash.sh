#!/bin/bash
# Installer Splash Screen
# Displays an image window during installation

IMAGE_FILE="$1"

if [ -z "$IMAGE_FILE" ] || [ ! -f "$IMAGE_FILE" ]; then
    exit 0  # Silently exit if no image
fi

# Try different methods to display the image
if command -v feh > /dev/null 2>&1; then
    # feh - simple image viewer
    feh --title "Daemon Breathalyzer - Installing..." \
        --geometry 400x400 \
        --borderless \
        --no-menus \
        "$IMAGE_FILE" &
    FEH_PID=$!
    echo $FEH_PID
elif command -v eog > /dev/null 2>&1; then
    # Eye of GNOME
    eog --new-instance "$IMAGE_FILE" &
    EOG_PID=$!
    echo $EOG_PID
elif command -v zenity > /dev/null 2>&1; then
    # zenity can show images but in a dialog format
    zenity --info --title="Daemon Breathalyzer" \
           --text="Installing..." \
           --window-icon="$IMAGE_FILE" &
    ZENITY_PID=$!
    echo $ZENITY_PID
fi

