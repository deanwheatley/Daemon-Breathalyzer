#!/usr/bin/env python3
"""
Fix System Configuration Errors

This script detects and fixes common system configuration errors that appear in logs.
"""

import subprocess
import sys
from pathlib import Path
import re


def run_command(cmd, check=False, capture_output=True):
    """Run a shell command."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture_output,
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        return e


def check_udev_rules():
    """Check and fix udev rules errors."""
    rules_file = Path("/etc/udev/rules.d/99-supergfxctl.rules")
    
    if not rules_file.exists():
        return False, "File does not exist"
    
    try:
        content = rules_file.read_text()
        lines = content.strip().split('\n')
        
        # Check for invalid syntax
        issues = []
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Check for invalid key patterns like "10de=="
            if re.search(r'^\s*[0-9a-fA-F]{4}==', line):
                issues.append(f"Line {i}: Invalid key pattern (bare hex key)")
            
            # Check if line looks like it's trying to match PCI vendor/device
            if '10de' in line.lower() and 'attr' not in line.lower():
                issues.append(f"Line {i}: Missing ATTR{{}} wrapper for PCI attributes")
        
        if issues:
            return True, issues
        return False, None
        
    except PermissionError:
        return None, "Permission denied - need sudo"
    except Exception as e:
        return None, f"Error reading file: {e}"


def fix_udev_rules():
    """Fix the supergfxctl udev rules file."""
    rules_file = Path("/etc/udev/rules.d/99-supergfxctl.rules")
    
    print("\n🔍 Checking udev rules file...")
    
    if not rules_file.exists():
        print("   ⚠️  File doesn't exist, skipping")
        return False
    
    try:
        content = rules_file.read_text()
        original_content = content
        
        # Fix the invalid syntax
        # Original: SUBSYSTEM=="pci", 10de=="0x1043", 249d=="0x2007", MODE="0666"
        # Should be: SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{device}=="0x249d", MODE="0666"
        
        # Pattern to match invalid syntax: bare hex keys
        # But we need to be careful - we should match PCI vendor/device IDs properly
        
        # Get the actual GPU vendor/device IDs from lspci
        result = run_command("lspci -nn | grep -iE 'nvidia.*vga'", check=False)
        if result.returncode == 0 and result.stdout:
            # Extract vendor:device IDs from output like: [10de:249d]
            match = re.search(r'\[([0-9a-f]{4}):([0-9a-f]{4})\]', result.stdout)
            if match:
                vendor_id = match.group(1)
                device_id = match.group(2)
            else:
                vendor_id = "10de"  # Default NVIDIA
                device_id = None
        else:
            vendor_id = "10de"
            device_id = None
        
        # Fix the content
        fixed_content = content
        
        # Replace invalid patterns
        # Pattern: SUBSYSTEM=="pci", 10de=="0x1043", 249d=="0x2007", MODE="0666"
        # This looks like it's trying to match vendor and device but using wrong syntax
        
        # Check if it's trying to match NVIDIA GPU
        if '10de' in content.lower():
            # Replace invalid syntax with proper udev syntax
            # The original seems wrong - 0x1043 is ASUS vendor ID, not NVIDIA
            # Let's create a proper rule for NVIDIA GPUs
            
            # For supergfxctl, we typically want to match PCI devices and trigger actions
            # A better rule would be:
            new_rule = f"""# Fixed udev rule for supergfxctl
# Match NVIDIA GPU devices
SUBSYSTEM=="pci", ATTR{{vendor}}=="0x10de", MODE="0666"

# Optional: Match specific device ID if needed
# SUBSYSTEM=="pci", ATTR{{vendor}}=="0x10de", ATTR{{device}}=="0x{device_id if device_id else '249d'}", MODE="0666"
"""
            
            # Only update if content looks broken
            if re.search(r'\b10de==', content) or re.search(r'\b[0-9a-f]{4}==', content):
                fixed_content = new_rule
                print(f"   ✅ Found invalid syntax, prepared fix")
            else:
                print("   ℹ️  File syntax looks okay")
                return False
        else:
            print("   ℹ️  No NVIDIA vendor ID found in file")
            return False
        
        if fixed_content != original_content:
            print(f"\n📝 Proposed fix for {rules_file}:")
            print("-" * 60)
            print("Current content:")
            print(original_content)
            print("-" * 60)
            print("Fixed content:")
            print(fixed_content)
            print("-" * 60)
            
            response = input("\n   Apply this fix? (y/N): ").strip().lower()
            if response == 'y':
                # Backup original
                backup_file = rules_file.with_suffix('.rules.bak')
                backup_file.write_text(original_content)
                print(f"   💾 Backed up original to {backup_file}")
                
                # Write fixed content (requires sudo)
                result = run_command(
                    f'sudo tee "{rules_file}" > /dev/null',
                    check=False,
                    capture_output=False
                )
                # Actually write using echo since we need sudo
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.rules') as tmp:
                    tmp.write(fixed_content)
                    tmp_path = tmp.name
                
                result = run_command(f'sudo cp "{tmp_path}" "{rules_file}"', check=False)
                Path(tmp_path).unlink()
                
                if result.returncode == 0:
                    print(f"   ✅ Fixed udev rules file")
                    
                    # Reload udev rules
                    print("   🔄 Reloading udev rules...")
                    reload_result = run_command("sudo udevadm control --reload-rules", check=False)
                    if reload_result.returncode == 0:
                        print("   ✅ Udev rules reloaded")
                        return True
                    else:
                        print(f"   ⚠️  Failed to reload udev rules: {reload_result.stderr}")
                        return True  # File was fixed, just reload failed
                else:
                    print(f"   ❌ Failed to write file: {result.stderr if hasattr(result, 'stderr') else 'Unknown error'}")
                    return False
            else:
                print("   ⏭️  Skipped fix")
                return False
        else:
            print("   ✅ File is already correct")
            return False
            
    except PermissionError:
        print("   ❌ Permission denied - please run with sudo")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def check_nvidia_persistenced():
    """Check nvidia-persistenced service."""
    print("\n🔍 Checking nvidia-persistenced service...")
    
    result = run_command("systemctl is-active nvidia-persistenced.service", check=False)
    
    if result.returncode == 0 and result.stdout.strip() == "active":
        print("   ✅ Service is running")
        return True
    else:
        print("   ⚠️  Service is not running")
        
        # Check if it's installed
        result = run_command("which nvidia-persistenced", check=False)
        if result.returncode != 0:
            print("   ⚠️  nvidia-persistenced not found")
            print("   💡 Install with: sudo apt install nvidia-persistenced")
            return False
        
        # Check device permissions
        result = run_command("ls -l /dev/nvidia* 2>&1 | head -3", check=False)
        if result.returncode == 0:
            print("   ℹ️  Checking device permissions...")
            if "crw-rw-rw" in result.stdout:
                print("   ✅ Device permissions look good")
            else:
                print("   ⚠️  Device permissions may need adjustment")
        
        return False


def check_nvidia_powerd():
    """Check nvidia-powerd service."""
    print("\n🔍 Checking nvidia-powerd service...")
    
    result = run_command("systemctl list-unit-files | grep nvidia-powerd", check=False)
    
    if result.returncode == 0 and result.stdout:
        print("   ✅ Service exists")
        return True
    else:
        print("   ⚠️  Service not found (this is optional)")
        print("   ℹ️  nvidia-powerd is not required for basic NVIDIA functionality")
        print("   💡 If needed, install with: sudo apt install nvidia-powerd")
        return True  # Not critical


def check_bluetooth_sap():
    """Check Bluetooth SAP configuration."""
    print("\n🔍 Checking Bluetooth SAP configuration...")
    
    print("   ⚠️  Bluetooth SAP errors are usually harmless")
    print("   ℹ️  SAP (SIM Access Profile) is rarely used on desktop systems")
    print("   💡 If you don't use Bluetooth for phone connectivity, you can ignore these errors")
    
    # Check if Bluetooth service is running
    result = run_command("systemctl is-active bluetooth.service", check=False)
    if result.returncode == 0:
        print("   ✅ Bluetooth service is running")
    else:
        print("   ℹ️  Bluetooth service status unknown")
    
    return True  # Not critical


def main():
    """Main function."""
    print("=" * 60)
    print("System Configuration Error Fixer")
    print("=" * 60)
    
    fixes_applied = []
    
    # Check and fix udev rules
    has_issues, issues = check_udev_rules()
    if has_issues:
        if fix_udev_rules():
            fixes_applied.append("udev rules")
    
    # Check nvidia-persistenced
    check_nvidia_persistenced()
    
    # Check nvidia-powerd
    check_nvidia_powerd()
    
    # Check Bluetooth SAP
    check_bluetooth_sap()
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if fixes_applied:
        print(f"✅ Fixed: {', '.join(fixes_applied)}")
        print("\n💡 You may need to reboot or reload services for all changes to take effect.")
    else:
        print("ℹ️  No fixes were applied.")
    
    print("\n📋 Errors that can be safely ignored:")
    print("   - casper-md5check: Only relevant for Live ISO systems")
    print("   - Bluetooth SAP: Rarely used, harmless")
    print("   - nvidia-powerd: Optional service")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()


