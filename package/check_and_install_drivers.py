#!/usr/bin/env python3
"""
Hardware Detection and Driver Installation
Detects hardware and installs appropriate drivers and utilities for various motherboards and chipsets.
"""

import subprocess
import sys
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class HardwareDetector:
    """Detects hardware and suggests appropriate drivers/utilities."""
    
    def __init__(self):
        self.detected_hardware = {}
        self.required_packages = set()
        self.optional_packages = set()
        
    def detect_all_hardware(self) -> Dict[str, any]:
        """Detect all relevant hardware components."""
        print("🔍 Detecting hardware components...")
        
        results = {
            'cpu': self.detect_cpu(),
            'gpu': self.detect_gpu(),
            'motherboard': self.detect_motherboard(),
            'sensors': self.detect_sensors(),
            'fan_control': self.detect_fan_control_support(),
            'gaming': self.detect_gaming_support()
        }
        
        self.detected_hardware = results
        return results
    
    def detect_cpu(self) -> Dict[str, str]:
        """Detect CPU information."""
        cpu_info = {'vendor': 'unknown', 'model': 'unknown', 'features': []}
        
        try:
            # Get CPU info from /proc/cpuinfo
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
            
            # Extract vendor
            vendor_match = re.search(r'vendor_id\s*:\s*(.+)', cpuinfo)
            if vendor_match:
                vendor = vendor_match.group(1).strip()
                cpu_info['vendor'] = vendor
                
                if 'Intel' in vendor or 'GenuineIntel' in vendor:
                    cpu_info['vendor'] = 'intel'
                    self.required_packages.add('intel-microcode')
                elif 'AMD' in vendor or 'AuthenticAMD' in vendor:
                    cpu_info['vendor'] = 'amd'
                    self.required_packages.add('amd64-microcode')
            
            # Extract model name
            model_match = re.search(r'model name\s*:\s*(.+)', cpuinfo)
            if model_match:
                cpu_info['model'] = model_match.group(1).strip()
            
            print(f"  ✅ CPU: {cpu_info['vendor']} - {cpu_info['model']}")
            
        except Exception as e:
            print(f"  ⚠️  CPU detection failed: {e}")
        
        return cpu_info
    
    def detect_gpu(self) -> Dict[str, any]:
        """Detect GPU information and driver requirements."""
        gpu_info = {'nvidia': [], 'amd': [], 'intel': []}
        
        try:
            # Use lspci to detect GPUs
            result = subprocess.run(['lspci', '-nn'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                
                for line in lines:
                    if 'VGA compatible controller' in line or '3D controller' in line:
                        if 'NVIDIA' in line or 'GeForce' in line:
                            gpu_info['nvidia'].append(line.strip())
                            self.required_packages.update([
                                'nvidia-driver-535',  # Latest stable
                                'nvidia-utils-535',
                                'nvidia-settings'
                            ])
                            print(f"  ✅ NVIDIA GPU detected: {line.split(':')[-1].strip()}")
                            
                        elif 'AMD' in line or 'Radeon' in line:
                            gpu_info['amd'].append(line.strip())
                            self.required_packages.update([
                                'mesa-vulkan-drivers',
                                'libgl1-mesa-dri',
                                'radeontop'
                            ])
                            print(f"  ✅ AMD GPU detected: {line.split(':')[-1].strip()}")
                            
                        elif 'Intel' in line:
                            gpu_info['intel'].append(line.strip())
                            self.required_packages.update([
                                'intel-media-va-driver',
                                'mesa-vulkan-drivers'
                            ])
                            print(f"  ✅ Intel GPU detected: {line.split(':')[-1].strip()}")
            
            # Check if nvidia-smi is available
            if gpu_info['nvidia'] and shutil.which('nvidia-smi'):
                try:
                    result = subprocess.run(['nvidia-smi', '--query-gpu=name,driver_version', '--format=csv,noheader'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        print(f"  ✅ NVIDIA driver active: {result.stdout.strip()}")
                    else:
                        print(f"  ⚠️  NVIDIA driver may need installation")
                except:
                    print(f"  ⚠️  NVIDIA driver not responding")
                    
        except Exception as e:
            print(f"  ⚠️  GPU detection failed: {e}")
        
        return gpu_info
    
    def detect_motherboard(self) -> Dict[str, str]:
        """Detect motherboard and chipset information."""
        mb_info = {'vendor': 'unknown', 'product': 'unknown', 'chipset': 'unknown'}
        
        try:
            # Get motherboard info from DMI
            result = subprocess.run(['sudo', 'dmidecode', '-t', 'baseboard'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                dmi_output = result.stdout
                
                vendor_match = re.search(r'Manufacturer:\s*(.+)', dmi_output)
                if vendor_match:
                    vendor = vendor_match.group(1).strip()
                    mb_info['vendor'] = vendor.lower()
                    
                    # Add vendor-specific packages
                    if 'asus' in vendor.lower():
                        self.required_packages.update(['asusctl', 'supergfxctl'])
                        print(f"  ✅ ASUS motherboard detected - asusctl required")
                    elif 'msi' in vendor.lower():
                        self.optional_packages.add('msi-perkeyrgb')
                        print(f"  ✅ MSI motherboard detected")
                    elif 'gigabyte' in vendor.lower():
                        self.optional_packages.add('openrgb')
                        print(f"  ✅ Gigabyte motherboard detected")
                
                product_match = re.search(r'Product Name:\s*(.+)', dmi_output)
                if product_match:
                    mb_info['product'] = product_match.group(1).strip()
            
            # Detect chipset
            result = subprocess.run(['lspci', '-nn'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Host bridge' in line:
                        mb_info['chipset'] = line.split(':')[-1].strip()
                        break
            
            print(f"  ✅ Motherboard: {mb_info['vendor']} {mb_info['product']}")
            
        except Exception as e:
            print(f"  ⚠️  Motherboard detection failed: {e}")
        
        return mb_info
    
    def detect_sensors(self) -> Dict[str, any]:
        """Detect available hardware sensors."""
        sensors_info = {'lm_sensors': False, 'thermal_zones': [], 'hwmon': []}
        
        try:
            # Check if lm-sensors is installed
            if shutil.which('sensors'):
                sensors_info['lm_sensors'] = True
                print(f"  ✅ lm-sensors available")
            else:
                self.required_packages.add('lm-sensors')
                print(f"  ⚠️  lm-sensors not found - will install")
            
            # Check thermal zones
            thermal_path = Path('/sys/class/thermal')
            if thermal_path.exists():
                thermal_zones = list(thermal_path.glob('thermal_zone*'))
                sensors_info['thermal_zones'] = [str(tz) for tz in thermal_zones]
                print(f"  ✅ Found {len(thermal_zones)} thermal zones")
            
            # Check hwmon devices
            hwmon_path = Path('/sys/class/hwmon')
            if hwmon_path.exists():
                hwmon_devices = list(hwmon_path.glob('hwmon*'))
                sensors_info['hwmon'] = [str(hw) for hw in hwmon_devices]
                print(f"  ✅ Found {len(hwmon_devices)} hwmon devices")
                
        except Exception as e:
            print(f"  ⚠️  Sensor detection failed: {e}")
        
        return sensors_info
    
    def detect_fan_control_support(self) -> Dict[str, any]:
        """Detect fan control capabilities."""
        fan_info = {'asusctl': False, 'pwm_fans': [], 'other_tools': []}
        
        try:
            # Check for asusctl
            if shutil.which('asusctl'):
                fan_info['asusctl'] = True
                print(f"  ✅ asusctl available for fan control")
            else:
                # Only add asusctl if we detected ASUS hardware
                if self.detected_hardware.get('motherboard', {}).get('vendor') == 'asus':
                    self.required_packages.add('asusctl')
                    print(f"  ⚠️  asusctl not found but ASUS hardware detected")
            
            # Check for PWM fan controls
            pwm_path = Path('/sys/class/hwmon')
            if pwm_path.exists():
                for hwmon_dir in pwm_path.glob('hwmon*'):
                    pwm_files = list(hwmon_dir.glob('pwm*'))
                    if pwm_files:
                        fan_info['pwm_fans'].extend([str(f) for f in pwm_files])
                
                if fan_info['pwm_fans']:
                    print(f"  ✅ Found {len(fan_info['pwm_fans'])} PWM fan controls")
                    self.optional_packages.add('fancontrol')
            
            # Check for other fan control tools
            other_tools = ['fancontrol', 'pwmconfig', 'liquidctl']
            for tool in other_tools:
                if shutil.which(tool):
                    fan_info['other_tools'].append(tool)
                    print(f"  ✅ Found fan control tool: {tool}")
                    
        except Exception as e:
            print(f"  ⚠️  Fan control detection failed: {e}")
        
        return fan_info
    
    def detect_gaming_support(self) -> Dict[str, any]:
        """Detect gaming-related hardware and software."""
        gaming_info = {'mangohud': False, 'gamemode': False, 'steam': False}
        
        try:
            # Check MangoHud
            if shutil.which('mangohud'):
                gaming_info['mangohud'] = True
                print(f"  ✅ MangoHud available for FPS monitoring")
            else:
                self.required_packages.add('mangohud')
                print(f"  ⚠️  MangoHud not found - needed for FPS monitoring")
            
            # Check GameMode
            if shutil.which('gamemoderun'):
                gaming_info['gamemode'] = True
                print(f"  ✅ GameMode available")
            else:
                self.optional_packages.add('gamemode')
            
            # Check Steam
            if shutil.which('steam') or Path.home().joinpath('.steam').exists():
                gaming_info['steam'] = True
                print(f"  ✅ Steam detected")
                
        except Exception as e:
            print(f"  ⚠️  Gaming support detection failed: {e}")
        
        return gaming_info
    
    def install_packages(self, packages: List[str], package_type: str = "required") -> bool:
        """Install packages using apt."""
        if not packages:
            return True
            
        print(f"\n📦 Installing {package_type} packages: {', '.join(packages)}")
        
        try:
            # Update package list first
            print("  🔄 Updating package list...")
            subprocess.run(['sudo', 'apt', 'update'], check=True, capture_output=True)
            
            # Install packages
            cmd = ['sudo', 'apt', 'install', '-y'] + packages
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  ✅ Successfully installed {package_type} packages")
                return True
            else:
                print(f"  ❌ Failed to install some {package_type} packages:")
                print(f"     {result.stderr}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Package installation failed: {e}")
            return False
        except Exception as e:
            print(f"  ❌ Unexpected error during installation: {e}")
            return False
    
    def setup_asusctl(self) -> bool:
        """Set up asusctl service if ASUS hardware is detected."""
        if 'asus' not in self.detected_hardware.get('motherboard', {}).get('vendor', '').lower():
            return True  # Not needed
            
        print("\n🔧 Setting up asusctl service...")
        
        try:
            # Enable and start asusd service
            subprocess.run(['sudo', 'systemctl', 'enable', 'asusd'], check=True)
            subprocess.run(['sudo', 'systemctl', 'start', 'asusd'], check=True)
            
            # Check if service is running
            result = subprocess.run(['systemctl', 'is-active', 'asusd'], 
                                  capture_output=True, text=True)
            if result.stdout.strip() == 'active':
                print("  ✅ asusd service is running")
                return True
            else:
                print("  ⚠️  asusd service may not be running properly")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to setup asusctl: {e}")
            return False
    
    def setup_sensors(self) -> bool:
        """Set up lm-sensors if installed."""
        if not shutil.which('sensors'):
            return True  # Not installed
            
        print("\n🌡️  Setting up hardware sensors...")
        
        try:
            # Run sensors-detect non-interactively
            print("  🔍 Running sensors-detect...")
            result = subprocess.run(['sudo', 'sensors-detect', '--auto'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("  ✅ Sensors configured successfully")
                
                # Test sensors
                result = subprocess.run(['sensors'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    print("  ✅ Sensors are working")
                    return True
                else:
                    print("  ⚠️  Sensors may not be working properly")
                    return False
            else:
                print(f"  ⚠️  sensors-detect had issues: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("  ⚠️  sensors-detect timed out")
            return False
        except Exception as e:
            print(f"  ❌ Sensor setup failed: {e}")
            return False
    
    def generate_report(self) -> str:
        """Generate a hardware detection report."""
        report = []
        report.append("=" * 60)
        report.append("🖥️  Hardware Detection Report")
        report.append("=" * 60)
        
        for category, info in self.detected_hardware.items():
            report.append(f"\n{category.upper()}:")
            if isinstance(info, dict):
                for key, value in info.items():
                    if isinstance(value, list):
                        report.append(f"  {key}: {len(value)} items")
                    else:
                        report.append(f"  {key}: {value}")
            else:
                report.append(f"  {info}")
        
        if self.required_packages:
            report.append(f"\nREQUIRED PACKAGES:")
            for pkg in sorted(self.required_packages):
                report.append(f"  - {pkg}")
        
        if self.optional_packages:
            report.append(f"\nOPTIONAL PACKAGES:")
            for pkg in sorted(self.optional_packages):
                report.append(f"  - {pkg}")
        
        return "\n".join(report)

def main():
    """Main hardware detection and driver installation."""
    print("🔍 Hardware Detection and Driver Installation")
    print("=" * 60)
    
    detector = HardwareDetector()
    
    # Detect all hardware
    hardware = detector.detect_all_hardware()
    
    # Show what we found
    print(f"\n📋 Detection Summary:")
    print(f"  Required packages: {len(detector.required_packages)}")
    print(f"  Optional packages: {len(detector.optional_packages)}")
    
    # Install required packages
    if detector.required_packages:
        required_list = list(detector.required_packages)
        
        # Filter out packages that might not be available
        available_packages = []
        unavailable_packages = []
        
        for pkg in required_list:
            if pkg in ['asusctl', 'supergfxctl']:
                # These need special installation
                unavailable_packages.append(pkg)
            else:
                available_packages.append(pkg)
        
        if available_packages:
            success = detector.install_packages(available_packages, "required")
            if not success:
                print("⚠️  Some required packages failed to install")
        
        # Handle special packages
        if 'asusctl' in unavailable_packages:
            print("\n⚠️  asusctl requires manual installation:")
            print("   Visit: https://asus-linux.org/asusctl/")
            print("   Follow the installation guide for your distribution")
    
    # Offer to install optional packages
    if detector.optional_packages:
        optional_list = list(detector.optional_packages)
        print(f"\n💡 Optional packages available: {', '.join(optional_list)}")
        
        try:
            response = input("Install optional packages? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                detector.install_packages(optional_list, "optional")
        except KeyboardInterrupt:
            print("\nSkipping optional packages")
    
    # Set up services
    detector.setup_asusctl()
    detector.setup_sensors()
    
    # Generate and save report
    report = detector.generate_report()
    print(f"\n{report}")
    
    # Save report to file
    report_file = Path.home() / '.config' / 'asus-control' / 'hardware_report.txt'
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(report)
    print(f"\n📄 Report saved to: {report_file}")
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Hardware detection cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Hardware detection failed: {e}")
        sys.exit(1)