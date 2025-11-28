#!/usr/bin/env python3
"""
Unified Fan Control Manager

Automatically detects system type and uses appropriate fan control interface.
"""

import subprocess
from typing import Optional, Tuple
from .asusctl_interface import AsusctlInterface
from .dell_fan_control import DellFanControl
from .generic_fan_control import GenericFanControl

class UnifiedFanControl:
    """Unified fan control that works across different laptop brands."""
    
    def __init__(self):
        self.system_type = self._detect_system()
        self.interface = self._get_interface()
    
    def _detect_system(self) -> str:
        """Detect system type (ASUS, Dell, or Generic)."""
        try:
            # Check for ASUS
            result = subprocess.run(['which', 'asusctl'], capture_output=True, timeout=2)
            if result.returncode == 0:
                return 'ASUS'
            
            # Check for Dell
            result = subprocess.run(['sudo', 'dmidecode', '-s', 'system-manufacturer'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and 'Dell' in result.stdout:
                return 'Dell'
            
            # Check if i8kctl is available (Dell tool)
            result = subprocess.run(['which', 'i8kctl'], capture_output=True, timeout=2)
            if result.returncode == 0:
                return 'Dell'
        except:
            pass
        
        return 'Generic'
    
    def _get_interface(self):
        """Get appropriate fan control interface."""
        if self.system_type == 'ASUS':
            return AsusctlInterface()
        elif self.system_type == 'Dell':
            return DellFanControl()
        else:
            return GenericFanControl()
    
    def get_system_type(self) -> str:
        """Get detected system type."""
        return self.system_type
    
    def is_available(self) -> bool:
        """Check if fan control is available."""
        return self.interface.is_available()
    
    def get_capabilities(self) -> dict:
        """Get fan control capabilities."""
        return {
            'system_type': self.system_type,
            'available': self.is_available(),
            'supports_curves': self.system_type == 'ASUS',
            'supports_manual': self.system_type in ['Dell', 'Generic'],
            'interface': type(self.interface).__name__
        }
