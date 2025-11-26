#!/bin/bash
#
# Fix System Log Errors
#
# This script fixes the following system log errors:
# 1. Invalid udev rules syntax in /etc/udev/rules.d/99-supergfxctl.rules
# 2. nvidia-persistenced permission issues
# 3. nvidia-powerd service (optional, provides info)
# 4. Bluetooth SAP errors (informational)

set -e

echo "============================================================"
echo "System Log Error Fixer"
echo "============================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run this script with sudo:"
    echo "   sudo $0"
    exit 1
fi

# 1. Fix udev rules file
echo "🔧 Fixing udev rules file..."
UDEV_RULES_FILE="/etc/udev/rules.d/99-supergfxctl.rules"

if [ -f "$UDEV_RULES_FILE" ]; then
    # Backup original
    cp "$UDEV_RULES_FILE" "${UDEV_RULES_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
    echo "   💾 Backed up original to ${UDEV_RULES_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
    
    # Create fixed version
    cat > "$UDEV_RULES_FILE" << 'UDEVEOF'
# Fixed udev rule for supergfxctl
# Match NVIDIA GPU devices and set permissions
# This replaces the invalid syntax that was causing errors
SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", MODE="0666"
UDEVEOF
    
    echo "   ✅ Fixed udev rules file syntax"
    echo "   📝 New content:"
    cat "$UDEV_RULES_FILE"
    echo ""
else
    echo "   ⚠️  File not found, creating new one..."
    cat > "$UDEV_RULES_FILE" << 'UDEVEOF'
# udev rule for supergfxctl - NVIDIA GPU permissions
SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", MODE="0666"
UDEVEOF
    echo "   ✅ Created new udev rules file"
fi

# Reload udev rules
echo "   🔄 Reloading udev rules..."
udevadm control --reload-rules
udevadm trigger
echo "   ✅ Udev rules reloaded"
echo ""

# 2. Check nvidia-persistenced
echo "🔧 Checking nvidia-persistenced service..."

# Check if service is installed
if systemctl list-unit-files | grep -q "nvidia-persistenced.service"; then
    # Check device permissions
    if [ -e /dev/nvidia0 ]; then
        # Check current permissions
        PERMS=$(stat -c "%a" /dev/nvidia0)
        if [ "$PERMS" != "666" ]; then
            echo "   ⚠️  Adjusting NVIDIA device permissions..."
            chmod 666 /dev/nvidia*
            echo "   ✅ Set permissions to 666"
        else
            echo "   ✅ Device permissions are correct"
        fi
    else
        echo "   ⚠️  NVIDIA devices not found - drivers may not be loaded"
    fi
    
    # Enable and start service
    systemctl enable nvidia-persistenced.service 2>/dev/null || true
    systemctl restart nvidia-persistenced.service 2>/dev/null || true
    
    if systemctl is-active --quiet nvidia-persistenced.service; then
        echo "   ✅ Service is running"
    else
        echo "   ⚠️  Service is not running (may require reboot or driver reload)"
    fi
else
    echo "   ⚠️  nvidia-persistenced service not found"
    echo "   💡 Install with: apt install nvidia-persistenced"
fi
echo ""

# 3. Check nvidia-powerd (optional)
echo "🔧 Checking nvidia-powerd service..."
if systemctl list-unit-files | grep -q "nvidia-powerd.service"; then
    echo "   ✅ Service exists"
    systemctl enable nvidia-powerd.service 2>/dev/null || true
else
    echo "   ℹ️  Service not found (this is optional)"
    echo "   💡 nvidia-powerd is not required for basic NVIDIA functionality"
    echo "   💡 If needed, install with: apt install nvidia-powerd"
fi
echo ""

# 4. Bluetooth SAP (informational)
echo "ℹ️  Bluetooth SAP errors:"
echo "   These errors are usually harmless and can be safely ignored."
echo "   SAP (SIM Access Profile) is rarely used on desktop systems."
echo "   If you don't use Bluetooth for phone connectivity, these are normal."
echo ""

# 5. casper-md5check (informational)
echo "ℹ️  casper-md5check errors:"
echo "   These errors only occur on Live ISO systems."
echo "   If you have an installed system, these can be safely ignored."
echo ""

echo "============================================================"
echo "✅ Fix complete!"
echo "============================================================"
echo ""
echo "📋 Summary:"
echo "   ✅ Fixed udev rules syntax"
echo "   ✅ Reloaded udev rules"
echo "   ✅ Checked nvidia-persistenced"
echo ""
echo "💡 Next steps:"
echo "   1. The udev rules errors should stop appearing in logs"
echo "   2. You may need to reboot for all changes to take full effect"
echo "   3. Check logs with: journalctl -p err -n 20"
echo ""
echo "📝 To verify fixes, run:"
echo "   journalctl -p err --since '5 minutes ago' | grep -i supergfxctl"
echo ""


