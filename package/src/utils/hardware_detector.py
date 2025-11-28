#!/usr/bin/env python3
"""
Hardware Detection Module

Detects motherboard, CPU, and GPU hardware and suggests/installs appropriate drivers.
"""

import subprocess
import re
import os
from typing import Dict, Optional, List, Tuple
from pathlib import Path


class HardwareDetector:
    """Detect system hardware and driver requirements."""
    
    def __init__(self):
        self.hardware_info = {}
        self.driver_recommendations = []
    
    def detect_all(self) -> Dict:
        """Detect all hardware components."""
        self.hardware_info = {
            'motherboard': self.detect_motherboard(),
            'cpu': self.detect_cpu(),
            'gpu': self.detect_gpu(),
            'gpu_drivers': self.detect_gpu_drivers(),
        }
        return self.hardware_info
    
    def detect_motherboard(self) -> Dict:
        """Detect motherboard information."""
        info = {
            'vendor': None,
            'model': None,
            'version': None,
            'chipset': None,
        }
        
        try:
            # Try dmidecode (requires root or proper permissions)
            result = subprocess.run(
                ['sudo', 'dmidecode', '-t', 'baseboard'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # Extract vendor
                vendor_match = re.search(r'Manufacturer:\s*(.+)', output, re.IGNORECASE)
                if vendor_match:
                    info['vendor'] = vendor_match.group(1).strip()
                
                # Extract model
                model_match = re.search(r'Product Name:\s*(.+)', output, re.IGNORECASE)
                if model_match:
                    info['model'] = model_match.group(1).strip()
                
                # Extract version
                version_match = re.search(r'Version:\s*(.+)', output, re.IGNORECASE)
                if version_match:
                    info['version'] = version_match.group(1).strip()
        
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            pass
        
        # Fallback: Try sysfs (no root required)
        try:
            sysfs_path = Path('/sys/devices/virtual/dmi/id')
            if sysfs_path.exists():
                if (sysfs_path / 'board_vendor').exists():
                    vendor = (sysfs_path / 'board_vendor').read_text().strip()
                    if vendor and vendor != 'Default string':
                        info['vendor'] = vendor
                
                if (sysfs_path / 'board_name').exists():
                    model = (sysfs_path / 'board_name').read_text().strip()
                    if model and model != 'Default string':
                        info['model'] = model
                
                if (sysfs_path / 'board_version').exists():
                    version = (sysfs_path / 'board_version').read_text().strip()
                    if version and version != 'Default string':
                        info['version'] = version
        except Exception:
            pass
        
        # Detect chipset
        try:
            lspci_result = subprocess.run(
                ['lspci'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if lspci_result.returncode == 0:
                # Look for chipset/bridge controller
                chipset_patterns = [
                    r'Host bridge.*?:\s*(.+)',
                    r'ISA bridge.*?:\s*(.+)',
                    r'PCI bridge.*?:\s*(.+)',
                ]
                
                for pattern in chipset_patterns:
                    match = re.search(pattern, lspci_result.stdout, re.IGNORECASE)
                    if match:
                        info['chipset'] = match.group(1).strip()
                        break
        except Exception:
            pass
        
        return info
    
    def detect_cpu(self) -> Dict:
        """Detect CPU information."""
        info = {
            'vendor': None,
            'model': None,
            'cores': None,
            'threads': None,
        }
        
        try:
            # Try /proc/cpuinfo
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
            
            # Extract vendor
            vendor_match = re.search(r'vendor_id\s*:\s*(.+)', cpuinfo, re.IGNORECASE)
            if vendor_match:
                vendor = vendor_match.group(1).strip().upper()
                if 'INTEL' in vendor:
                    info['vendor'] = 'Intel'
                elif 'AMD' in vendor:
                    info['vendor'] = 'AMD'
            
            # Extract model
            model_match = re.search(r'model name\s*:\s*(.+)', cpuinfo, re.IGNORECASE)
            if model_match:
                info['model'] = model_match.group(1).strip()
            
            # Count cores and threads
            core_matches = re.findall(r'processor\s*:\s*\d+', cpuinfo)
            info['threads'] = len(core_matches) if core_matches else None
            
            # Physical cores (from cpu cores field)
            cores_match = re.search(r'cpu cores\s*:\s*(\d+)', cpuinfo, re.IGNORECASE)
            if cores_match:
                info['cores'] = int(cores_match.group(1))
        
        except Exception:
            pass
        
        return info
    
    def detect_gpu(self) -> Dict:
        """Detect GPU information."""
        info = {
            'vendor': None,
            'model': None,
            'pci_id': None,
            'type': None,  # 'discrete' or 'integrated'
            'drivers_installed': False,
        }
        
        gpus_found = []
        
        try:
            # Use lspci to detect GPU
            result = subprocess.run(
                ['lspci', '-nn'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Process each line looking for GPU devices
                for line in result.stdout.split('\n'):
                    if not ('VGA' in line or '3D' in line or 'Display' in line):
                        continue
                    
                    # Extract PCI vendor:device ID
                    pci_match = re.search(r'\[(\w{4}):(\w{4})\]', line)
                    if not pci_match:
                        continue
                    
                    vendor_id = pci_match.group(1).lower()
                    device_id = pci_match.group(2)
                    
                    # Extract device name and model
                    # Format: "01:00.0 VGA compatible controller: NVIDIA Corporation GA104M [GeForce RTX 3070 Mobile / Max-Q] [10de:249d]"
                    # Extract the part after the colon and before the brackets
                    parts = line.split(':')
                    if len(parts) >= 3:
                        device_name_part = ':'.join(parts[2:]).strip()
                    else:
                        device_name_part = line.split(':')[-1].strip()
                    
                    # Extract model from brackets
                    # Pattern: text [0300] ... [Model Name] [vendor:device]
                    # Find all brackets and identify which one contains the model
                    all_brackets = re.findall(r'\[([^\]]+)\]', line)
                    model_in_brackets = None
                    
                    # Usually the model is in brackets between vendor name and PCI ID
                    # PCI IDs are hex:hex format like "1002:1638"
                    # Device class is hex format like "0300"
                    # Look for the bracket that contains descriptive text (not IDs or vendor names)
                    for bracket_content in all_brackets:
                        bracket = bracket_content.strip()
                        # Skip if it's a PCI ID (vendor:device)
                        if re.match(r'^[0-9a-f]{4}:[0-9a-f]{4}$', bracket.lower()):
                            continue
                        # Skip if it's just a device class number like "0300"
                        if re.match(r'^[0-9a-f]{4}$', bracket.lower()):
                            continue
                        # Skip vendor names like "AMD/ATI"
                        if bracket.lower() in ['amd/ati', 'amd', 'ati', 'nvidia corporation']:
                            continue
                        # This should be the model name (contains descriptive text)
                        if len(bracket) > 5 and not bracket.isdigit():
                            model_in_brackets = bracket
                            break
                    
                    # Extract base name (before any brackets)
                    base_name = device_name_part.split('[')[0].strip()
                    
                    gpu_info = {
                        'vendor_id': vendor_id,
                        'device_id': device_id,
                        'name': base_name,
                        'line': line,
                    }
                    
                    # Detect NVIDIA (vendor ID 10de)
                    if 'nvidia' in line.lower() or vendor_id == '10de':
                        gpu_info['vendor'] = 'NVIDIA'
                        gpu_info['type'] = 'discrete'
                        # Use model from brackets if available, otherwise use base name
                        if model_in_brackets:
                            gpu_info['model'] = model_in_brackets
                        else:
                            # Extract from base name (e.g., "NVIDIA Corporation GA104M")
                            name_parts = base_name.split()
                            if len(name_parts) > 2:
                                gpu_info['model'] = ' '.join(name_parts[2:])  # Skip "NVIDIA Corporation"
                            else:
                                gpu_info['model'] = base_name
                        gpus_found.append(gpu_info)
                    
                    # Detect AMD/ATI (vendor ID 1002)
                    elif 'amd' in line.lower() or 'ati' in line.lower() or 'radeon' in line.lower() or vendor_id == '1002':
                        gpu_info['vendor'] = 'AMD'
                        # Check if it's discrete (vendor ID 1002 usually means discrete)
                        if vendor_id == '1002':
                            gpu_info['type'] = 'discrete'
                        else:
                            gpu_info['type'] = 'integrated'
                        # Extract model - prefer the model in brackets
                        if model_in_brackets:
                            gpu_info['model'] = model_in_brackets
                        else:
                            # Extract from base name - look for codename and series
                            # Example: "Advanced Micro Devices, Inc. [AMD/ATI] Cezanne [Radeon Vega Series / Radeon Vega Mobile Series]"
                            name_parts = base_name.split()
                            
                            # Look for codenames or series names
                            model_keywords = ['Cezanne', 'Renoir', 'Lucienne', 'Rembrandt', 'Vega', 
                                            'Radeon', 'RX', 'R9', 'R7', 'R5']
                            found_model = False
                            for keyword in model_keywords:
                                if keyword in line:
                                    # Try to find the full model name
                                    keyword_idx = None
                                    for i, part in enumerate(name_parts):
                                        if keyword.lower() in part.lower():
                                            keyword_idx = i
                                            break
                                    
                                    if keyword_idx is not None:
                                        # Get a few words around the keyword
                                        start = max(0, keyword_idx - 1)
                                        end = min(len(name_parts), keyword_idx + 4)
                                        gpu_info['model'] = ' '.join(name_parts[start:end])
                                        found_model = True
                                        break
                            
                            if not found_model:
                                # Remove company name and use the rest
                                if '[AMD/ATI]' in base_name:
                                    parts = base_name.split('[AMD/ATI]')
                                    if len(parts) > 1:
                                        gpu_info['model'] = parts[1].strip().split('[')[0].strip()
                                    else:
                                        gpu_info['model'] = base_name.replace('Advanced Micro Devices, Inc.', '').strip()
                                else:
                                    gpu_info['model'] = base_name
                        gpus_found.append(gpu_info)
                    
                    # Detect Intel (vendor ID 8086)
                    elif 'intel' in line.lower() or vendor_id == '8086':
                        gpu_info['vendor'] = 'Intel'
                        gpu_info['type'] = 'integrated'
                        # Extract model
                        if model_in_brackets:
                            gpu_info['model'] = model_in_brackets
                        else:
                            # Extract from base name (e.g., "Intel Corporation UHD Graphics")
                            name_parts = base_name.split()
                            if len(name_parts) > 2:
                                gpu_info['model'] = ' '.join(name_parts[2:])  # Skip "Intel Corporation"
                            else:
                                gpu_info['model'] = base_name
                        gpus_found.append(gpu_info)
                
                # Prefer discrete GPU over integrated if both exist
                discrete_gpus = [g for g in gpus_found if g.get('type') == 'discrete']
                if discrete_gpus:
                    best_gpu = discrete_gpus[0]  # Take first discrete GPU
                elif gpus_found:
                    best_gpu = gpus_found[0]  # Take first GPU found
                else:
                    best_gpu = None
                
                if best_gpu:
                    info['vendor'] = best_gpu.get('vendor')
                    info['model'] = best_gpu.get('model')
                    info['pci_id'] = f"{best_gpu.get('vendor_id')}:{best_gpu.get('device_id')}"
                    info['type'] = best_gpu.get('type')
                    info['all_gpus'] = gpus_found  # Store all GPUs for reference
        
        except Exception as e:
            pass
        
        return info
    
    def detect_gpu_drivers(self) -> Dict:
        """Check if GPU drivers are installed."""
        drivers = {
            'nvidia': False,
            'amd': False,
            'intel': False,
            'status': 'unknown',
        }
        
        # Check NVIDIA drivers
        try:
            result = subprocess.run(
                ['nvidia-smi'],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode == 0:
                drivers['nvidia'] = True
                drivers['status'] = 'nvidia_installed'
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Check for NVIDIA driver modules
        try:
            if os.path.exists('/proc/driver/nvidia'):
                drivers['nvidia'] = True
                drivers['status'] = 'nvidia_installed'
        except Exception:
            pass
        
        # Check AMD drivers (amdgpu or radeon)
        try:
            result = subprocess.run(
                ['lsmod'],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode == 0:
                if 'amdgpu' in result.stdout or 'radeon' in result.stdout:
                    drivers['amd'] = True
                    drivers['status'] = 'amd_installed'
        except Exception:
            pass
        
        # Intel drivers are usually built into the kernel
        try:
            if os.path.exists('/sys/class/drm/card0'):
                # Check if Intel graphics
                result = subprocess.run(
                    ['lspci', '-nnk'],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                if result.returncode == 0 and '8086' in result.stdout:
                    # Intel GPU detected, drivers usually work out of the box
                    drivers['intel'] = True
                    drivers['status'] = 'intel_installed'
        except Exception:
            pass
        
        return drivers
    
    def get_driver_recommendations(self) -> List[Dict]:
        """Get driver installation recommendations."""
        recommendations = []
        
        hardware = self.hardware_info if self.hardware_info else self.detect_all()
        gpu = hardware.get('gpu', {})
        gpu_drivers = hardware.get('gpu_drivers', {})
        
        # GPU driver recommendations
        gpu_vendor = gpu.get('vendor')
        
        if gpu_vendor == 'NVIDIA':
            if not gpu_drivers.get('nvidia'):
                recommendations.append({
                    'type': 'gpu',
                    'vendor': 'NVIDIA',
                    'action': 'install',
                    'package': 'nvidia-driver',
                    'description': 'NVIDIA GPU drivers are required for GPU monitoring',
                    'install_command': 'sudo apt update && sudo apt install -y nvidia-driver-535',
                    'check_command': 'nvidia-smi',
                })
            else:
                recommendations.append({
                    'type': 'gpu',
                    'vendor': 'NVIDIA',
                    'action': 'installed',
                    'description': 'NVIDIA drivers are installed',
                })
        
        elif gpu_vendor == 'AMD':
            if not gpu_drivers.get('amd'):
                recommendations.append({
                    'type': 'gpu',
                    'vendor': 'AMD',
                    'action': 'install',
                    'package': 'mesa-amdgpu',
                    'description': 'AMD GPU drivers (mesa-amdgpu) for GPU monitoring',
                    'install_command': 'sudo apt update && sudo apt install -y mesa-amdgpu mesa-vulkan-drivers',
                    'check_command': 'lsmod | grep amdgpu',
                })
            else:
                recommendations.append({
                    'type': 'gpu',
                    'vendor': 'AMD',
                    'action': 'installed',
                    'description': 'AMD drivers are installed',
                })
        
        # Motherboard/Chipset drivers (usually in kernel, but check for specific cases)
        motherboard = hardware.get('motherboard', {})
        vendor = motherboard.get('vendor', '').lower()
        
        # ASUS-specific drivers
        if 'asus' in vendor:
            recommendations.append({
                'type': 'motherboard',
                'vendor': 'ASUS',
                'action': 'info',
                'description': 'ASUS motherboard detected. Most drivers are in the kernel.',
                'note': 'asusctl may provide additional functionality for ASUS laptops',
            })
        
        return recommendations
    
    def install_driver(self, recommendation: Dict) -> Tuple[bool, str]:
        """Install a recommended driver."""
        if recommendation.get('action') != 'install':
            return False, "Driver installation not required"
        
        install_cmd = recommendation.get('install_command')
        if not install_cmd:
            return False, "No installation command provided"
        
        try:
            # Execute installation command
            result = subprocess.run(
                install_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                return True, "Driver installed successfully"
            else:
                return False, f"Installation failed: {result.stderr}"
        
        except subprocess.TimeoutExpired:
            return False, "Installation timed out"
        except Exception as e:
            return False, f"Installation error: {str(e)}"

