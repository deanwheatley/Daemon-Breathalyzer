#!/usr/bin/env python3
"""
Dell Fan Control Interface

Provides fan control for Dell laptops using i8kutils.
"""

import subprocess
import re
from typing import Optional, Tuple, List

class DellFanControl:
    """Interface for Dell laptop fan control using i8kutils."""
    
    def __init__(self):
        self.available = self._check_available()
    
    def _check_available(self) -> bool:
        """Check if Dell fan control is available."""
        try:
            # Check if i8kctl command exists
            result = subprocess.run(['which', 'i8kctl'], capture_output=True, timeout=2)
            if result.returncode == 0:
                return True
            
            # Check if dell_smm_hwmon module is loaded
            result = subprocess.run(['lsmod'], capture_output=True, text=True, timeout=2)
            if 'dell_smm_hwmon' in result.stdout or 'i8k' in result.stdout:
                return True
        except:
            pass
        return False
    
    def is_available(self) -> bool:
        """Check if Dell fan control is available."""
        return self.available
    
    def get_fan_speed(self, fan_index: int = 0) -> Optional[int]:
        """Get fan speed in RPM."""
        try:
            result = subprocess.run(['i8kctl', 'fan'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                # Output format: "left_fan_rpm right_fan_rpm"
                speeds = result.stdout.strip().split()
                if len(speeds) > fan_index:
                    return int(speeds[fan_index])
        except:
            pass
        return None
    
    def set_fan_speed(self, fan_index: int, speed: int) -> Tuple[bool, str]:
        """
        Set fan speed.
        
        Args:
            fan_index: 0 for left fan, 1 for right fan
            speed: 0 (off), 1 (low), 2 (high)
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if speed < 0 or speed > 2:
                return False, "Speed must be 0 (off), 1 (low), or 2 (high)"
            
            result = subprocess.run(
                ['sudo', 'i8kctl', 'fan', str(fan_index), str(speed)],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                return True, f"Fan {fan_index} set to speed {speed}"
            else:
                return False, result.stderr or "Failed to set fan speed"
        except Exception as e:
            return False, str(e)
    
    def get_temperature(self) -> Optional[float]:
        """Get CPU temperature."""
        try:
            result = subprocess.run(['i8kctl', 'temp'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                temp = int(result.stdout.strip())
                return float(temp)
        except:
            pass
        return None
