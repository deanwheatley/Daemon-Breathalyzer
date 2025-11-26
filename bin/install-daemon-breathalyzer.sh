#!/bin/bash
# Daemon Breathalyzer - Standalone Installer
# This script contains everything needed for installation

set -e

echo "=========================================="
echo "Daemon Breathalyzer - Installation"
echo "=========================================="
echo ""

# Detect if we're running from an extracted archive or directly
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# If install.sh exists in the same directory, use it
if [ -f "$SCRIPT_DIR/install.sh" ]; then
    cd "$SCRIPT_DIR"
    exec ./install.sh
else
    echo "❌ Error: install.sh not found in package."
    echo "Please ensure you've extracted the full package."
    exit 1
fi
