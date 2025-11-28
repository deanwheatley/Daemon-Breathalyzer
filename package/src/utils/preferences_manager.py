#!/usr/bin/env python3
"""
Preferences Manager

Manages user preferences for UI visibility and layout with persistence.
"""

import json
from pathlib import Path
from typing import Dict, Optional


class PreferencesManager:
    """Manages user preferences with persistence."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the preferences manager.
        
        Args:
            config_dir: Directory to store config. Defaults to ~/.config/asus-control/
        """
        if config_dir is None:
            config_dir = Path.home() / '.config' / 'asus-control'
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.prefs_file = self.config_dir / 'preferences.json'
        
        # Default preferences
        self.default_prefs = {
            'visible_meters': {
                'cpu_percent': True,
                'cpu_temp': True,
                'cpu_freq': True,
                'memory': True,
                'memory_used': True,
                'gpu_usage': True,
                'gpu_temp': True,
                'gpu_memory': True,
                'network_sent': True,
                'network_recv': True,
                'network_total': True,
                'fps': True,
                'cpu_fan_gauge': True,
                'gpu_fan_gauge': True,
            },
            'ui_theme': 'game',  # 'game', 'modern', 'classic'
            'animations_enabled': True,
            'icon_animated': True,
            'averaging_window_seconds': 60,  # Default 60-second averaging for Network, GPU, FPS
        }
        
        self.preferences = self._load_preferences()
    
    def _load_preferences(self) -> Dict:
        """Load preferences from file."""
        if not self.prefs_file.exists():
            return self.default_prefs.copy()
        
        try:
            with open(self.prefs_file, 'r') as f:
                prefs = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged = self.default_prefs.copy()
                merged.update(prefs)
                # Ensure visible_meters dict is complete
                if 'visible_meters' in prefs:
                    merged['visible_meters'].update(prefs['visible_meters'])
                return merged
        except Exception as e:
            print(f"Error loading preferences: {e}")
            return self.default_prefs.copy()
    
    def _save_preferences(self):
        """Save preferences to file."""
        try:
            with open(self.prefs_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            print(f"Error saving preferences: {e}")
    
    def is_meter_visible(self, meter_name: str) -> bool:
        """Check if a meter is visible."""
        return self.preferences.get('visible_meters', {}).get(meter_name, True)
    
    def set_meter_visible(self, meter_name: str, visible: bool):
        """Set meter visibility."""
        if 'visible_meters' not in self.preferences:
            self.preferences['visible_meters'] = {}
        self.preferences['visible_meters'][meter_name] = visible
        self._save_preferences()
    
    def get_preference(self, key: str, default=None):
        """Get a preference value."""
        return self.preferences.get(key, default)
    
    def set_preference(self, key: str, value):
        """Set a preference value."""
        self.preferences[key] = value
        self._save_preferences()
    
    def reset_to_defaults(self):
        """Reset all preferences to defaults."""
        self.preferences = self.default_prefs.copy()
        self._save_preferences()

