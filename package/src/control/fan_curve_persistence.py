#!/usr/bin/env python3
"""
Fan Curve Persistence Manager

Manages persistent storage of fan curves to restore them across reboots and app restarts.
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from .asusctl_interface import FanCurve, Profile


class FanCurvePersistence:
    """Manages persistent storage and restoration of fan curves."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the persistence manager.
        
        Args:
            config_dir: Directory to store config. Defaults to ~/.config/asus-control/
        """
        if config_dir is None:
            config_dir = Path.home() / '.config' / 'asus-control'
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / 'active_fan_curves.json'
    
    def save_active_curves(self, profile: Profile, curves: Dict[str, FanCurve]):
        """
        Save the active fan curves for a profile.
        
        Args:
            profile: The ASUS profile (Balanced, Quiet, Performance)
            curves: Dictionary mapping fan names to FanCurve objects
        """
        try:
            # Load existing config
            config = self._load_config()
            
            # Convert curves to serializable format
            profile_key = profile.value
            config[profile_key] = {
                'last_updated': datetime.now().isoformat(),
                'curves': {}
            }
            
            for fan_name, curve in curves.items():
                config[profile_key]['curves'][fan_name] = curve.to_dict()
            
            # Save to file
            self._save_config(config)
        except Exception as e:
            print(f"Error saving active curves: {e}")
    
    def save_active_curve(self, profile: Profile, fan_name: str, curve: FanCurve):
        """
        Save a single active fan curve.
        
        Args:
            profile: The ASUS profile
            fan_name: Name of the fan (e.g., 'CPU', 'GPU')
            curve: FanCurve object
        """
        try:
            # Load existing config
            config = self._load_config()
            
            # Get or create profile entry
            profile_key = profile.value
            if profile_key not in config:
                config[profile_key] = {
                    'last_updated': datetime.now().isoformat(),
                    'curves': {}
                }
            
            # Update the curve
            config[profile_key]['curves'][fan_name] = curve.to_dict()
            config[profile_key]['last_updated'] = datetime.now().isoformat()
            
            # Save to file
            self._save_config(config)
        except Exception as e:
            print(f"Error saving active curve: {e}")
    
    def load_active_curves(self, profile: Profile) -> Dict[str, FanCurve]:
        """
        Load the active fan curves for a profile.
        
        Args:
            profile: The ASUS profile
            
        Returns:
            Dictionary mapping fan names to FanCurve objects
        """
        try:
            config = self._load_config()
            profile_key = profile.value
            
            if profile_key not in config:
                return {}
            
            curves_data = config[profile_key].get('curves', {})
            curves = {}
            
            for fan_name, curve_dict in curves_data.items():
                try:
                    curves[fan_name] = FanCurve.from_dict(curve_dict)
                except Exception as e:
                    print(f"Error loading curve for {fan_name}: {e}")
            
            return curves
        except Exception as e:
            print(f"Error loading active curves: {e}")
            return {}
    
    def get_all_active_curves(self) -> Dict[str, Dict[str, FanCurve]]:
        """
        Get all active curves for all profiles.
        
        Returns:
            Dictionary mapping profile names to dictionaries of fan curves
        """
        try:
            config = self._load_config()
            all_curves = {}
            
            for profile_key, profile_data in config.items():
                curves_data = profile_data.get('curves', {})
                curves = {}
                
                for fan_name, curve_dict in curves_data.items():
                    try:
                        curves[fan_name] = FanCurve.from_dict(curve_dict)
                    except Exception as e:
                        print(f"Error loading curve for {profile_key}/{fan_name}: {e}")
                
                if curves:
                    all_curves[profile_key] = curves
            
            return all_curves
        except Exception as e:
            print(f"Error loading all active curves: {e}")
            return {}
    
    def clear_active_curves(self, profile: Optional[Profile] = None):
        """
        Clear active curves for a profile or all profiles.
        
        Args:
            profile: If provided, clear only this profile. Otherwise clear all.
        """
        try:
            if profile:
                config = self._load_config()
                profile_key = profile.value
                if profile_key in config:
                    del config[profile_key]
                    self._save_config(config)
            else:
                # Clear all
                if self.config_file.exists():
                    self.config_file.unlink()
        except Exception as e:
            print(f"Error clearing active curves: {e}")
    
    def _load_config(self) -> Dict:
        """Load configuration from file."""
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def _save_config(self, config: Dict):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

