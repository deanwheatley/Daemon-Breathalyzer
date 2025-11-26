#!/usr/bin/env python3
"""
Check and Install Hardware Drivers

This script detects hardware and installs appropriate drivers if needed.
Called during application installation.
"""

import sys
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.hardware_detector import HardwareDetector


def main():
    """Main driver installation check."""
    print("\n" + "=" * 60)
    print("  Hardware Detection & Driver Installation")
    print("=" * 60 + "\n")
    
    detector = HardwareDetector()
    
    # Detect hardware
    print("🔍 Scanning your system for hardware...")
    hardware = detector.detect_all()
    print()
    
    # Display detected hardware
    motherboard = hardware.get('motherboard', {})
    cpu = hardware.get('cpu', {})
    gpu = hardware.get('gpu', {})
    gpu_drivers = hardware.get('gpu_drivers', {})
    
    print("\n📋 Detected Hardware:")
    print("=" * 50)
    
    # Motherboard
    mb_vendor = motherboard.get('vendor', '').strip()
    mb_model = motherboard.get('model', '').strip()
    mb_version = motherboard.get('version', '').strip()
    if mb_vendor or mb_model:
        mb_display = f"{mb_vendor} {mb_model}".strip()
        if mb_version and mb_version != 'Default string':
            mb_display += f" (v{mb_version})"
        print(f"  🖥️  Motherboard: {mb_display}")
    else:
        print(f"  🖥️  Motherboard: Not detected")
    
    # CPU
    cpu_vendor = cpu.get('vendor', '').strip()
    cpu_model = cpu.get('model', '').strip()
    cpu_cores = cpu.get('cores') or cpu.get('threads')
    if cpu_vendor or cpu_model:
        cpu_display = f"{cpu_vendor} {cpu_model}".strip()
        if cpu_cores:
            cpu_display += f" ({cpu_cores} cores)"
        print(f"  🔧 CPU: {cpu_display}")
    else:
        print(f"  🔧 CPU: Not detected")
    
    # GPU
    gpu_vendor = gpu.get('vendor', '').strip()
    gpu_model = gpu.get('model', '').strip()
    gpu_type = gpu.get('type', '').strip()
    all_gpus = gpu.get('all_gpus', [])
    
    if gpu_vendor or gpu_model:
        gpu_display = f"{gpu_vendor} {gpu_model}".strip()
        if gpu_type:
            gpu_display += f" ({gpu_type})"
        print(f"  🎮 GPU: {gpu_display}")
        
        # Show additional GPUs if multiple detected
        if all_gpus and len(all_gpus) > 1:
            for additional_gpu in all_gpus[1:]:
                add_vendor = additional_gpu.get('vendor', 'Unknown')
                add_model = additional_gpu.get('model', '')
                add_type = additional_gpu.get('type', '')
                add_display = f"{add_vendor} {add_model}".strip()
                if add_type:
                    add_display += f" ({add_type})"
                print(f"       └─ Additional: {add_display}")
    else:
        print(f"  🎮 GPU: Not detected")
    
    print("=" * 50)
    print()
    
    # Get driver recommendations
    recommendations = detector.get_driver_recommendations()
    
    if not recommendations:
        print("✅ All hardware drivers appear to be installed.")
        print("\n💡 Tip: If you experience issues, check:")
        print("   - GPU drivers: nvidia-smi (NVIDIA) or lsmod | grep amdgpu (AMD)")
        print("   - Sensors: sudo apt install lm-sensors")
        return 0
    
    print("📦 Driver Recommendations:")
    print("-" * 50)
    
    install_needed = []
    
    for rec in recommendations:
        action = rec.get('action', 'unknown')
        desc = rec.get('description', '')
        
        if action == 'install':
            print(f"\n⚠️  {rec.get('type', 'driver').upper()} Driver Needed:")
            print(f"   {desc}")
            print(f"   Package: {rec.get('package', 'N/A')}")
            install_needed.append(rec)
        elif action == 'installed':
            print(f"\n✅ {rec.get('type', 'driver').upper()} Driver:")
            print(f"   {desc}")
        elif action == 'info':
            print(f"\nℹ️  {rec.get('type', 'hardware').upper()} Info:")
            print(f"   {desc}")
            if rec.get('note'):
                print(f"   Note: {rec.get('note')}")
    
    # Offer to install missing drivers
    if install_needed:
        print("\n" + "=" * 50)
        print("Driver Installation")
        print("=" * 50)
        
        for rec in install_needed:
            vendor = rec.get('vendor', 'Unknown')
            package = rec.get('package', 'driver')
            install_cmd = rec.get('install_command', '')
            
            print(f"\n📦 {vendor} Driver Installation")
            print(f"   Package: {package}")
            
            if not install_cmd:
                print(f"   ⚠️  Manual installation required.")
                print(f"   Please install {package} manually.")
                continue
            
            # Check if user wants to install
            response = input(f"\n   Install {vendor} drivers automatically? (Y/n): ").strip().lower()
            
            if response and response[0] == 'n':
                print(f"   ⏭️  Skipping {vendor} driver installation.")
                print(f"   You can install it later with:")
                print(f"   {install_cmd}")
                continue
            
            print(f"   🔧 Installing {vendor} drivers...")
            print(f"   Command: {install_cmd}")
            print()
            
            success, message = detector.install_driver(rec)
            
            if success:
                print(f"   ✅ {vendor} drivers installed successfully!")
                
                # For NVIDIA, suggest reboot
                if vendor == 'NVIDIA':
                    print(f"\n   ⚠️  NVIDIA drivers require a system reboot to take effect.")
                    print(f"   Please reboot your system after installation completes.")
            else:
                print(f"   ❌ Installation failed: {message}")
                print(f"   Please install manually with:")
                print(f"   {install_cmd}")
    
    print("\n" + "=" * 50)
    print("✅ Hardware detection complete")
    print("=" * 50 + "\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

