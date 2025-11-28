#!/bin/bash
#
# Build Binary Install Package Script
#
# This script creates installable packages in the bin/ folder
# including compressed archives and installation scripts
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$SCRIPT_DIR/bin"
PACKAGE_DIR="$SCRIPT_DIR/package"
PACKAGE_NAME="daemon-breathalyzer"
VERSION=$(date +%Y%m%d)

echo "============================================================"
echo "Building Install Package in bin/ folder"
echo "============================================================"
echo ""

# Ensure bin directory exists
mkdir -p "$BIN_DIR"

# First, ensure package directory is up to date
if [ ! -d "$PACKAGE_DIR" ] || [ -z "$(ls -A "$PACKAGE_DIR" 2>/dev/null)" ]; then
    echo "📦 Package directory is empty or missing. Building package first..."
    "$SCRIPT_DIR/build_package.sh"
fi

# Create versioned package archive
ARCHIVE_NAME="${PACKAGE_NAME}-${VERSION}.tar.gz"
ARCHIVE_PATH="$BIN_DIR/$ARCHIVE_NAME"

echo "📦 Creating compressed archive..."
cd "$PACKAGE_DIR"
tar --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='*.pyo' -czf "$ARCHIVE_PATH" .
cd "$SCRIPT_DIR"

ARCHIVE_SIZE=$(du -sh "$ARCHIVE_PATH" | cut -f1)

# Create a standalone installer script that includes everything
echo "📝 Creating standalone installer script..."
cat > "$BIN_DIR/install-${PACKAGE_NAME}.sh" << 'INSTALLER_EOF'
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
INSTALLER_EOF

chmod +x "$BIN_DIR/install-${PACKAGE_NAME}.sh"

# Create a quick-install script that extracts and installs
echo "📝 Creating quick-install script..."
cat > "$BIN_DIR/quick-install.sh" << QUICKINSTALL_EOF
#!/bin/bash
# Quick Install Script for Daemon Breathalyzer
# Extracts archive and runs installer

set -e

SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"

# Find the latest archive
ARCHIVE_PATH=\$(ls -t "\$SCRIPT_DIR"/daemon-breathalyzer-*.tar.gz 2>/dev/null | head -1)

if [ -z "\$ARCHIVE_PATH" ] || [ ! -f "\$ARCHIVE_PATH" ]; then
    echo "❌ Error: Archive file not found in \$SCRIPT_DIR"
    echo "Please ensure the package archive exists in the bin/ directory."
    exit 1
fi

ARCHIVE_NAME=\$(basename "\$ARCHIVE_PATH")
echo "=========================================="
echo "Daemon Breathalyzer - Quick Install"
echo "=========================================="
echo ""
echo "📦 Using archive: \$ARCHIVE_NAME"
echo ""

# Create temporary extraction directory
TEMP_DIR=\$(mktemp -d)
trap "rm -rf \$TEMP_DIR" EXIT

echo "📦 Extracting package..."
tar -xzf "\$ARCHIVE_PATH" -C "\$TEMP_DIR"

echo "🚀 Running installer..."
cd "\$TEMP_DIR"
chmod +x install.sh
./install.sh
QUICKINSTALL_EOF

chmod +x "$BIN_DIR/quick-install.sh"

# Create README for bin folder
echo "📝 Creating bin/README..."
cat > "$BIN_DIR/README.md" << BINREADME_EOF
# Install Packages

This directory contains ready-to-install packages for Daemon Breathalyzer.

## 📦 Available Packages

### Archive Package
- **\`${ARCHIVE_NAME}\`** - Complete distribution package (${ARCHIVE_SIZE})
  - Contains all source code, scripts, and documentation
  - Extract with: \`tar -xzf ${ARCHIVE_NAME}\`
  - Then run: \`cd ${PACKAGE_NAME}-${VERSION} && ./install.sh\`

### Quick Install Script
- **\`quick-install.sh\`** - One-command installer
  - Extracts archive and runs installation automatically
  - Run with: \`./quick-install.sh\`

### Standalone Installer
- **\`install-${PACKAGE_NAME}.sh\`** - Installer script wrapper
  - For use with extracted packages

## 🚀 Installation Methods

### Method 1: Quick Install (Recommended)
\`\`\`bash
cd bin
./quick-install.sh
\`\`\`

### Method 2: Manual Install
\`\`\`bash
cd bin
tar -xzf ${ARCHIVE_NAME}
cd ${PACKAGE_NAME}-${VERSION}
./install.sh
\`\`\`

### Method 3: Extract and Install Separately
\`\`\`bash
# Extract to desired location
tar -xzf bin/${ARCHIVE_NAME} -C ~/software/

# Install from extracted location
cd ~/software/${PACKAGE_NAME}-${VERSION}
./install.sh
\`\`\`

## 📋 Package Contents

The archive contains:
- Complete source code (\`src/\`)
- Installation scripts (\`install.sh\`)
- Launcher scripts (\`daemon-breathalyzer-launcher.sh\`)
- Desktop entry (\`daemon-breathalyzer.desktop\`)
- Documentation (\`README.md\`)
- Application icons (\`img/\`)
- Driver installation tools
- All dependencies list (\`requirements.txt\`)

## 🔧 System Requirements

- Linux Mint or compatible Linux distribution
- Python 3.10 or higher
- Internet connection (for downloading dependencies)
- sudo access (for installing system packages)

## 📝 Version

Package Version: ${VERSION}
Build Date: $(date)

## 🆘 Support

For issues or questions:
- GitHub: https://github.com/deanwheatley/Daemon-Breathalyzer
- Email: deanwheatley@hotmail.com
- Documentation: See README.md in the package
BINREADME_EOF

# Create checksum file
echo "🔐 Generating checksums..."
cd "$BIN_DIR"
if command -v sha256sum > /dev/null 2>&1; then
    sha256sum "$ARCHIVE_NAME" > "${ARCHIVE_NAME}.sha256"
    echo "✅ SHA256 checksum created: ${ARCHIVE_NAME}.sha256"
elif command -v shasum > /dev/null 2>&1; then
    shasum -a 256 "$ARCHIVE_NAME" > "${ARCHIVE_NAME}.sha256"
    echo "✅ SHA256 checksum created: ${ARCHIVE_NAME}.sha256"
fi

# Summary
echo ""
echo "============================================================"
echo "✅ Install package built successfully!"
echo "============================================================"
echo ""
echo "📁 Package location: $BIN_DIR"
echo "📦 Archive: $ARCHIVE_NAME (${ARCHIVE_SIZE})"
echo "📄 Files in bin/:"
ls -lh "$BIN_DIR" | grep -v "^d" | grep -v "^total" | awk '{print "   - " $9 " (" $5 ")"}'
echo ""
echo "🚀 To install:"
echo "   cd bin"
echo "   ./quick-install.sh"
echo ""
echo "✅ Done!"

