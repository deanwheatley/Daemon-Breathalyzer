#!/usr/bin/env python3
"""
Profile Manager

Manages fan curve profiles with save/load functionality.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from .asusctl_interface import FanCurve, Profile as AsusProfile, get_preset_curve


class SavedProfile:
    """Represents a saved fan curve profile."""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        cpu_fan_curve: Optional[FanCurve] = None,
        gpu_fan_curve: Optional[FanCurve] = None,
        created_at: Optional[str] = None,
        asus_profile: Optional[str] = None
    ):
        self.name = name
        self.description = description
        self.cpu_fan_curve = cpu_fan_curve
        self.gpu_fan_curve = gpu_fan_curve
        self.created_at = created_at or datetime.now().isoformat()
        self.asus_profile = asus_profile  # Which ASUS profile this is for
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'asus_profile': self.asus_profile,
        }
        
        if self.cpu_fan_curve:
            result['cpu_fan_curve'] = self.cpu_fan_curve.to_dict()
        if self.gpu_fan_curve:
            result['gpu_fan_curve'] = self.gpu_fan_curve.to_dict()
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SavedProfile':
        """Create from dictionary."""
        cpu_curve = None
        gpu_curve = None
        
        if 'cpu_fan_curve' in data:
            cpu_curve = FanCurve.from_dict(data['cpu_fan_curve'])
        if 'gpu_fan_curve' in data:
            gpu_curve = FanCurve.from_dict(data['gpu_fan_curve'])
        
        return cls(
            name=data['name'],
            description=data.get('description', ''),
            cpu_fan_curve=cpu_curve,
            gpu_fan_curve=gpu_curve,
            created_at=data.get('created_at'),
            asus_profile=data.get('asus_profile')
        )


class ProfileManager:
    """Manages saved fan curve profiles."""
    
    def __init__(self, profiles_dir: Optional[Path] = None):
        """
        Initialize the profile manager.
        
        Args:
            profiles_dir: Directory to store profiles. Defaults to ~/.config/asus-control/profiles/
        """
        if profiles_dir is None:
            profiles_dir = Path.home() / '.config' / 'asus-control' / 'profiles'
        
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        self.profiles: Dict[str, SavedProfile] = {}
        self.load_all_profiles()
    
    def get_profile_path(self, name: str) -> Path:
        """Get the file path for a profile."""
        # Sanitize filename
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        return self.profiles_dir / f"{safe_name}.json"
    
    def save_profile(self, profile: SavedProfile) -> bool:
        """
        Save a profile to disk.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            path = self.get_profile_path(profile.name)
            data = profile.to_dict()
            
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.profiles[profile.name] = profile
            return True
        except Exception as e:
            print(f"Error saving profile: {e}")
            return False
    
    def load_profile(self, name: str) -> Optional[SavedProfile]:
        """Load a profile by name."""
        try:
            path = self.get_profile_path(name)
            if not path.exists():
                return None
            
            with open(path, 'r') as f:
                data = json.load(f)
            
            profile = SavedProfile.from_dict(data)
            self.profiles[name] = profile
            return profile
        except Exception as e:
            print(f"Error loading profile: {e}")
            return None
    
    def load_all_profiles(self):
        """Load all profiles from disk."""
        self.profiles.clear()
        
        if not self.profiles_dir.exists():
            return
        
        for path in self.profiles_dir.glob('*.json'):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                
                profile = SavedProfile.from_dict(data)
                self.profiles[profile.name] = profile
            except Exception as e:
                print(f"Error loading profile from {path}: {e}")
    
    def delete_profile(self, name: str) -> bool:
        """
        Delete a profile.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            path = self.get_profile_path(name)
            if path.exists():
                path.unlink()
            
            if name in self.profiles:
                del self.profiles[name]
            
            return True
        except Exception as e:
            print(f"Error deleting profile: {e}")
            return False
    
    def list_profiles(self) -> List[str]:
        """Get list of all profile names."""
        return sorted(self.profiles.keys())
    
    def get_profile(self, name: str) -> Optional[SavedProfile]:
        """Get a profile by name."""
        return self.profiles.get(name)
    
    def export_profile(self, name: str, export_path: Path, format: str = 'json') -> bool:
        """
        Export a profile to a file.
        
        Args:
            name: Profile name
            export_path: Path to export file
            format: 'json' or 'yaml'
        
        Returns:
            True if successful
        """
        profile = self.get_profile(name)
        if not profile:
            return False
        
        try:
            data = profile.to_dict()
            
            if format.lower() == 'yaml':
                if not YAML_AVAILABLE:
                    raise ImportError("PyYAML is required for YAML export")
                with open(export_path, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            else:
                with open(export_path, 'w') as f:
                    json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting profile: {e}")
            return False
    
    def import_profile(self, import_path: Path) -> Optional[SavedProfile]:
        """
        Import a profile from a file.
        
        Returns:
            SavedProfile if successful, None otherwise
        """
        try:
            with open(import_path, 'r') as f:
                if import_path.suffix.lower() in ['.yaml', '.yml']:
                    if not YAML_AVAILABLE:
                        raise ImportError("PyYAML is required for YAML import")
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            profile = SavedProfile.from_dict(data)
            self.save_profile(profile)
            return profile
        except Exception as e:
            print(f"Error importing profile: {e}")
            return None
    
    def get_preset_names(self) -> List[str]:
        """Get list of available preset names."""
        return ['quiet', 'balanced', 'performance', 'conservative', 'max']
    
    def load_preset(self, preset_name: str) -> Dict:
        """Load a preset curve configuration."""
        from .asusctl_interface import get_preset_curve
        
        try:
            cpu_curve = get_preset_curve(preset_name)
            gpu_curve = get_preset_curve(preset_name)
            
            return {
                'name': preset_name.title(),
                'description': f'{preset_name.title()} preset curve',
                'cpu_curve': [(p.temperature, p.fan_speed) for p in cpu_curve.points],
                'gpu_curve': [(p.temperature, p.fan_speed) for p in gpu_curve.points]
            }
        except Exception as e:
            print(f"Error loading preset {preset_name}: {e}")
            return {
                'name': preset_name.title(),
                'description': f'{preset_name.title()} preset curve',
                'cpu_curve': [(30, 30), (50, 50), (70, 70), (90, 90)],
                'gpu_curve': [(30, 30), (50, 50), (70, 70), (90, 90)]
            }

