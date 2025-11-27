#!/usr/bin/env python3
"""
Curve File Manager

Handles saving, loading, and managing fan curve files.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime


class CurveFileManager:
    """Manages fan curve file operations."""
    
    def __init__(self):
        self.curves_dir = Path.home() / ".config" / "asus-control" / "curves"
        self.curves_dir.mkdir(parents=True, exist_ok=True)
    
    def save_curve(self, filename: str, curve_data) -> bool:
        """Save curve data to file."""
        try:
            if not filename.endswith('.curve'):
                filename += '.curve'
            
            filepath = self.curves_dir / filename
            
            # Handle different curve data formats
            if isinstance(curve_data, dict):
                # Direct dict format
                data = curve_data.copy()
                data["modified"] = datetime.now().isoformat()
            else:
                # Object format
                data = {
                    "name": getattr(curve_data, 'name', 'Unnamed'),
                    "description": getattr(curve_data, 'description', ''),
                    "points": getattr(curve_data, 'points', []),
                    "created": getattr(curve_data, 'created', datetime.now().isoformat()),
                    "modified": datetime.now().isoformat()
                }
                
                # Convert points to proper format if needed
                if hasattr(curve_data, 'points') and curve_data.points:
                    if isinstance(curve_data.points[0], tuple):
                        data["points"] = [{"temperature": t, "fan_speed": s} for t, s in curve_data.points]
                    else:
                        data["points"] = curve_data.points
            
            # Create backup if file exists
            if filepath.exists():
                backup_path = filepath.with_suffix('.curve.bak')
                filepath.rename(backup_path)
            
            # Save file
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving curve: {e}")
            return False
    
    def load_curve(self, filename: str):
        """Load curve data from file."""
        try:
            if not filename.endswith('.curve'):
                filename += '.curve'
            
            filepath = self.curves_dir / filename
            
            if not filepath.exists():
                raise FileNotFoundError(f"Curve file not found: {filename}")
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Return raw dict for compatibility
            result = {
                "name": data.get("name", "Unnamed"),
                "description": data.get("description", ""),
                "created": data.get("created", datetime.now().isoformat()),
                "modified": data.get("modified", datetime.now().isoformat())
            }
            
            # Handle points format
            points = data.get("points", [])
            if points and isinstance(points[0], dict):
                result["points"] = [(p["temperature"], p["fan_speed"]) for p in points]
            else:
                result["points"] = points
            
            return result
            
        except Exception as e:
            print(f"Error loading curve: {e}")
            return None
    
    def delete_curve(self, filename: str) -> bool:
        """Delete a curve file."""
        try:
            if not filename.endswith('.curve'):
                filename += '.curve'
            
            filepath = self.curves_dir / filename
            
            if filepath.exists():
                # Move to backup before deleting
                backup_path = filepath.with_suffix('.curve.deleted')
                filepath.rename(backup_path)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting curve: {e}")
            return False
    
    def list_curves(self) -> List[str]:
        """List all available curve files."""
        try:
            curve_files = []
            for filepath in self.curves_dir.glob("*.curve"):
                curve_files.append(filepath.stem)
            return sorted(curve_files)
        except Exception as e:
            print(f"Error listing curves: {e}")
            return []
    
    def get_curve_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get curve metadata without loading full curve."""
        try:
            if not filename.endswith('.curve'):
                filename += '.curve'
            
            filepath = self.curves_dir / filename
            
            if not filepath.exists():
                return None
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            return {
                "name": data.get("name", "Unnamed"),
                "description": data.get("description", ""),
                "point_count": len(data.get("points", [])),
                "created": data.get("created"),
                "modified": data.get("modified"),
                "filename": filename
            }
            
        except Exception as e:
            print(f"Error getting curve info: {e}")
            return None