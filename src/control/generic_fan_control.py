#!/usr/bin/env python3
"""
Generic Fan Control Interface

Provides generic fan control using PWM for non-ASUS/Dell laptops.
"""

import subprocess
import glob
from pathlib import Path
from typing import Optional, Tuple, List, Dict

class GenericFanControl:
    """Generic fan control using PWM."""
    
    def __init__(self):
        self.pwm_devices = self._find_pwm_devices()
        self.available = len(self.pwm_devices) > 0
    
    def _find_pwm_devices(self) -> List[Dict]:
        """Find available PWM fan control devices."""
        devices = []
        
        try:
            # Search for PWM controls in hwmon
            for pwm_path in glob.glob('/sys/class/hwmon/hwmon*/pwm*'):
                if '_enable' in pwm_path or '_mode' in pwm_path:
                    continue
                
                # Get device info
                device = {
                    'path': pwm_path,
                    'name': Path(pwm_path).name,
                    'max': 255  # Default PWM max
                }
                
                # Try to get max value
                max_path = pwm_path + '_max'
                if Path(max_path).exists():
                    try:
                        with open(max_path, 'r') as f:
                            device['max'] = int(f.read().strip())
                    except:
                        pass
                
                # Try to get label
                label_path = pwm_path.replace(Path(pwm_path).name, '') + Path(pwm_path).name.replace('pwm', 'fan') + '_label'
                if Path(label_path).exists():
                    try:
                        with open(label_path, 'r') as f:
                            device['label'] = f.read().strip()
                    except:
                        pass
                
                devices.append(device)
        except Exception as e:
            print(f"Error finding PWM devices: {e}")
        
        return devices
    
    def is_available(self) -> bool:
        """Check if generic fan control is available."""
        return self.available
    
    def get_fan_speed(self, device_index: int = 0) -> Optional[int]:
        """Get fan speed in RPM."""
        if device_index >= len(self.pwm_devices):
            return None
        
        try:
            device = self.pwm_devices[device_index]
            # Get corresponding fan input
            fan_input_path = device['path'].replace('pwm', 'fan') + '_input'
            
            if Path(fan_input_path).exists():
                with open(fan_input_path, 'r') as f:
                    return int(f.read().strip())
        except:
            pass
        return None
    
    def set_fan_speed_percent(self, device_index: int, percent: int) -> Tuple[bool, str]:
        """
        Set fan speed as percentage.
        
        Args:
            device_index: Index of PWM device
            percent: Speed percentage (0-100)
        
        Returns:
            Tuple of (success, message)
        """
        if device_index >= len(self.pwm_devices):
            return False, "Invalid device index"
        
        if percent < 0 or percent > 100:
            return False, "Percent must be 0-100"
        
        try:
            device = self.pwm_devices[device_index]
            pwm_value = int((percent / 100.0) * device['max'])
            
            # Enable manual control
            enable_path = device['path'] + '_enable'
            if Path(enable_path).exists():
                subprocess.run(['sudo', 'sh', '-c', f'echo 1 > {enable_path}'], timeout=2)
            
            # Set PWM value
            result = subprocess.run(
                ['sudo', 'sh', '-c', f'echo {pwm_value} > {device["path"]}'],
                capture_output=True, text=True, timeout=2
            )
            
            if result.returncode == 0:
                return True, f"Fan speed set to {percent}%"
            else:
                return False, result.stderr or "Failed to set fan speed"
        except Exception as e:
            return False, str(e)
    
    def enable_automatic_control(self, device_index: int = 0) -> Tuple[bool, str]:
        """Enable automatic fan control."""
        if device_index >= len(self.pwm_devices):
            return False, "Invalid device index"
        
        try:
            device = self.pwm_devices[device_index]
            enable_path = device['path'] + '_enable'
            
            if Path(enable_path).exists():
                result = subprocess.run(
                    ['sudo', 'sh', '-c', f'echo 2 > {enable_path}'],
                    capture_output=True, text=True, timeout=2
                )
                
                if result.returncode == 0:
                    return True, "Automatic fan control enabled"
                else:
                    return False, result.stderr or "Failed to enable automatic control"
            else:
                return False, "Automatic control not supported"
        except Exception as e:
            return False, str(e)
