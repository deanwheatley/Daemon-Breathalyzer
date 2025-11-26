#!/bin/bash
# Quick Install Script for Daemon Breathalyzer
# Extracts archive and runs installer

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find the latest archive
ARCHIVE_PATH=$(ls -t "$SCRIPT_DIR"/daemon-breathalyzer-*.tar.gz 2>/dev/null | head -1)

if [ -z "$ARCHIVE_PATH" ] || [ ! -f "$ARCHIVE_PATH" ]; then
    echo "❌ Error: Archive file not found in $SCRIPT_DIR"
    echo "Please ensure the package archive exists in the bin/ directory."
    exit 1
fi

ARCHIVE_NAME=$(basename "$ARCHIVE_PATH")
echo "=========================================="
echo "Daemon Breathalyzer - Quick Install"
echo "=========================================="
echo ""
echo "📦 Using archive: $ARCHIVE_NAME"
echo ""

# Create temporary extraction directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "📦 Extracting package..."
tar -xzf "$ARCHIVE_PATH" -C "$TEMP_DIR"

echo "🚀 Running installer..."
cd "$TEMP_DIR"
chmod +x install.sh
./install.sh
