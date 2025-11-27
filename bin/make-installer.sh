#!/bin/bash
# Create working self-extracting installer

set -e

VERSION="1.0.7"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Creating installer v$VERSION..."

# Create payload
cd "$PROJECT_DIR"
tar czf /tmp/payload.tar.gz src requirements.txt install.sh asus-control-launcher.sh run.py check_and_install_drivers.py README.md

# Update version in template
sed "s/INSTALLER_VERSION=\".*\"/INSTALLER_VERSION=\"$VERSION\"/" "$SCRIPT_DIR/daemon-breathalyzer-installer.sh" > /tmp/installer-template.sh

# Create final installer
cat /tmp/installer-template.sh /tmp/payload.tar.gz > "$SCRIPT_DIR/daemon-breathalyzer-installer-v$VERSION.sh"
chmod +x "$SCRIPT_DIR/daemon-breathalyzer-installer-v$VERSION.sh"

# Cleanup
rm /tmp/payload.tar.gz /tmp/installer-template.sh

echo "✅ Created: daemon-breathalyzer-installer-v$VERSION.sh"
ls -lh "$SCRIPT_DIR/daemon-breathalyzer-installer-v$VERSION.sh"