#!/usr/bin/env python3
"""
asusctl Interface Module

Handles communication with asusctl for fan control operations.
"""

import subprocess
import json
import re
from typing import List, Dict, Optional, Tuple
from enum import Enum


class Profile(Enum):
    """ASUS power profiles."""
    BALANCED = "Balanced"
    QUIET = "Quiet"
    PERFORMANCE = "Performance"


class FanCurvePoint:
    """Represents a single point in a fan curve."""
    
    def __init__(self, temperature: int, fan_speed: int):
        """
        Initialize a fan curve point.
        
        Args:
            temperature: Temperature in Celsius (typically 30-90)
            fan_speed: Fan speed percentage (0-100)
        """
        self.temperature = max(30, min(90, temperature))
        self.fan_speed = max(0, min(100, fan_speed))
    
    def __repr__(self):
        return f"FanCurvePoint({self.temperature}°C, {self.fan_speed}%)"
    
    def to_asusctl_format(self) -> str:
        """Convert to asusctl format: '<temp>c:<speed>%'"""
        return f"{self.temperature}c:{self.fan_speed}%"
    
    @classmethod
    def from_asusctl_format(cls, data: str) -> 'FanCurvePoint':
        """Parse from asusctl format: '<temp>c:<speed>%' or '<temp> <speed>'"""
        # Try new format first: 30c:100%
        if 'c:' in data and '%' in data:
            # Format: 30c:100%
            temp_str, speed_str = data.split('c:')
            speed_str = speed_str.rstrip('%')
            return cls(int(temp_str), int(speed_str))
        
        # Fallback to old format: space-separated
        parts = data.strip().split()
        if len(parts) >= 2:
            return cls(int(parts[0]), int(parts[1]))
        
        raise ValueError(f"Invalid fan curve point format: {data}")


class FanCurve:
    """Represents a complete fan curve."""
    
    def __init__(self, points: List[FanCurvePoint] = None):
        """
        Initialize a fan curve.
        
        Args:
            points: List of FanCurvePoint objects (sorted by temperature)
        """
        self.points = sorted(points or [], key=lambda p: p.temperature)
        self._validate()
    
    def _validate(self):
        """Validate the fan curve."""
        if not self.points:
            raise ValueError("Fan curve must have at least one point")
        
        if len(self.points) < 2:
            raise ValueError("Fan curve must have at least 2 points")
        
        # Check for duplicate temperatures
        temps = [p.temperature for p in self.points]
        if len(temps) != len(set(temps)):
            raise ValueError("Fan curve cannot have duplicate temperatures")
        
        # Ensure monotonic (non-decreasing fan speed with temperature)
        speeds = [p.fan_speed for p in self.points]
        for i in range(1, len(speeds)):
            if speeds[i] < speeds[i-1]:
                raise ValueError("Fan speed must not decrease as temperature increases")
    
    def add_point(self, temperature: int, fan_speed: int):
        """Add a point to the curve (maintains sorting)."""
        # Remove existing point at this temperature if any
        self.points = [p for p in self.points if p.temperature != temperature]
        
        # Add new point and sort
        self.points.append(FanCurvePoint(temperature, fan_speed))
        self.points = sorted(self.points, key=lambda p: p.temperature)
        
        # Validate
        try:
            self._validate()
        except ValueError as e:
            # Remove the problematic point
            self.points = [p for p in self.points if p.temperature != temperature]
            raise e
    
    def remove_point(self, temperature: int):
        """Remove a point from the curve."""
        if len(self.points) <= 2:
            raise ValueError("Cannot remove point: fan curve must have at least 2 points")
        
        self.points = [p for p in self.points if p.temperature != temperature]
    
    def to_asusctl_format(self) -> str:
        """Convert to asusctl format: comma-separated '<temp>c:<speed>%' pairs"""
        return ",".join(p.to_asusctl_format() for p in self.points)
    
    @classmethod
    def from_asusctl_format(cls, data: str) -> 'FanCurve':
        """Parse from asusctl format: comma-separated or space-separated."""
        # Try comma-separated format first: 30c:100%,50c:100%
        if ',' in data and 'c:' in data:
            point_strings = data.split(',')
            points = []
            for point_str in point_strings:
                points.append(FanCurvePoint.from_asusctl_format(point_str.strip()))
            return cls(points)
        
        # Fallback to space-separated format: 30 100 50 100
        parts = data.strip().split()
        if len(parts) % 2 != 0:
            raise ValueError("Invalid fan curve format: must have pairs of temperature and speed")
        
        points = []
        for i in range(0, len(parts), 2):
            temp = int(parts[i])
            speed = int(parts[i + 1])
            points.append(FanCurvePoint(temp, speed))
        
        return cls(points)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'points': [{'temperature': p.temperature, 'fan_speed': p.fan_speed} for p in self.points]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FanCurve':
        """Create from dictionary."""
        points = [FanCurvePoint(p['temperature'], p['fan_speed']) for p in data['points']]
        return cls(points)
    
    def get_fan_speed_at_temp(self, temperature: int) -> int:
        """Get fan speed for a given temperature (linear interpolation)."""
        if not self.points:
            return 0
        
        # Find surrounding points
        if temperature <= self.points[0].temperature:
            return self.points[0].fan_speed
        
        if temperature >= self.points[-1].temperature:
            return self.points[-1].fan_speed
        
        # Linear interpolation
        for i in range(len(self.points) - 1):
            if self.points[i].temperature <= temperature <= self.points[i + 1].temperature:
                t1, s1 = self.points[i].temperature, self.points[i].fan_speed
                t2, s2 = self.points[i + 1].temperature, self.points[i + 1].fan_speed
                
                if t2 == t1:
                    return s1
                
                # Linear interpolation
                speed = s1 + (s2 - s1) * (temperature - t1) / (t2 - t1)
                return int(round(speed))
        
        return self.points[-1].fan_speed


class AsusctlInterface:
    """Interface for communicating with asusctl."""
    
    def __init__(self):
        """Initialize the asusctl interface."""
        self._check_asusctl_available()
    
    def _check_asusctl_available(self) -> bool:
        """Check if asusctl is available."""
        try:
            result = subprocess.run(
                ['asusctl', '--version'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def is_available(self) -> bool:
        """Check if asusctl is available."""
        return self._check_asusctl_available()
    
    def get_current_profile(self) -> Optional[Profile]:
        """Get the current active power profile."""
        try:
            result = subprocess.run(
                ['asusctl', 'profile', '-p'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                # Look for "Active profile is X" line
                for line in output.split('\n'):
                    if 'active profile is' in line.lower():
                        profile_name = line.split('is')[-1].strip().lower()
                        if 'balanced' in profile_name:
                            return Profile.BALANCED
                        elif 'quiet' in profile_name:
                            return Profile.QUIET
                        elif 'performance' in profile_name:
                            return Profile.PERFORMANCE
                
                # Fallback: check entire output
                output_lower = output.lower()
                if 'performance' in output_lower:
                    return Profile.PERFORMANCE
                elif 'quiet' in output_lower:
                    return Profile.QUIET
                elif 'balanced' in output_lower:
                    return Profile.BALANCED
        except Exception:
            pass
        
        return None
    
    def get_available_profiles(self) -> List[Profile]:
        """Get list of available power profiles."""
        return [Profile.BALANCED, Profile.QUIET, Profile.PERFORMANCE]
    
    def get_fan_curve(self, fan_name: str) -> Optional[List[Tuple[int, int]]]:
        """Get current fan curve for a specific fan."""
        current_profile = self.get_current_profile()
        if not current_profile:
            return None
            
        curves = self.get_fan_curves(current_profile)
        curve = curves.get(fan_name.upper())
        
        if curve:
            return [(p.temperature, p.fan_speed) for p in curve.points]
        return None
    
    def apply_fan_curve(self, fan_name: str, curve_points: List[Tuple[int, int]]) -> Tuple[bool, str]:
        """Apply a fan curve to the current profile."""
        try:
            # Convert points to FanCurve
            points = [FanCurvePoint(temp, speed) for temp, speed in curve_points]
            curve = FanCurve(points)
            
            # Get current profile
            current_profile = self.get_current_profile()
            if not current_profile:
                return False, "Could not determine current profile"
            
            # Apply the curve
            return self.set_fan_curve(current_profile, fan_name, curve)
            
        except Exception as e:
            return False, str(e)
    
    def set_profile(self, profile: Profile) -> Tuple[bool, str]:
        """
        Set the power profile.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            profile_map = {
                Profile.BALANCED: 'Balanced',
                Profile.QUIET: 'Quiet',
                Profile.PERFORMANCE: 'Performance'
            }
            
            result = subprocess.run(
                ['asusctl', 'profile', '-P', profile_map[profile]],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return True, f"Profile set to {profile.value}"
            else:
                return False, result.stderr or result.stdout
        except Exception as e:
            return False, str(e)
    
    def get_fan_curves(self, profile: Profile) -> Dict[str, FanCurve]:
        """
        Get fan curves for a profile.
        
        Returns:
            Dictionary mapping fan names to FanCurve objects
        """
        curves = {}
        
        try:
            profile_map = {
                Profile.BALANCED: 'Balanced',
                Profile.QUIET: 'Quiet',
                Profile.PERFORMANCE: 'Performance'
            }
            
            result = subprocess.run(
                ['asusctl', 'fan-curve', '--mod-profile', profile_map[profile]],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse output - format varies, need to extract curve data
                # This is a simplified parser - may need adjustment based on actual asusctl output
                lines = result.stdout.strip().split('\n')
                current_fan = None
                current_curve_data = []
                
                for line in lines:
                    # Look for fan identifiers
                    if 'fan' in line.lower() or 'cpu' in line.lower() or 'gpu' in line.lower():
                        if current_fan and current_curve_data:
                            try:
                                curve_str = ' '.join(current_curve_data)
                                curves[current_fan] = FanCurve.from_asusctl_format(curve_str)
                            except:
                                pass
                        
                        # Extract fan name
                        current_fan = line.strip().split()[0] if line.strip() else 'unknown'
                        current_curve_data = []
                    else:
                        # Try to parse as curve data
                        parts = line.strip().split()
                        if len(parts) >= 2 and all(p.isdigit() for p in parts):
                            current_curve_data.extend(parts)
                
                # Handle last fan
                if current_fan and current_curve_data:
                    try:
                        curve_str = ' '.join(current_curve_data)
                        curves[current_fan] = FanCurve.from_asusctl_format(curve_str)
                    except:
                        pass
        except Exception:
            pass
        
        return curves
    
    def set_fan_curve(
        self,
        profile: Profile,
        fan_name: str,
        curve: FanCurve,
        save_persistent: bool = True
    ) -> Tuple[bool, str]:
        """
        Set a fan curve for a profile and fan.
        
        Args:
            profile: Power profile
            fan_name: Name of the fan (e.g., 'CPU', 'GPU')
            curve: FanCurve object
            save_persistent: If True, save to persistent storage for restoration
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            profile_map = {
                Profile.BALANCED: 'Balanced',
                Profile.QUIET: 'Quiet',
                Profile.PERFORMANCE: 'Performance'
            }
            
            # First ensure fan curves are enabled
            enable_result = self.enable_fan_curves(profile, True)
            if not enable_result[0]:
                print(f"Warning: Could not enable fan curves: {enable_result[1]}")
            
            # Convert curve to asusctl format
            curve_data = curve.to_asusctl_format()
            print(f"Applying curve for {fan_name}: {curve_data}")
            
            # Apply the curve
            result = subprocess.run(
                [
                    'asusctl', 'fan-curve',
                    '--mod-profile', profile_map[profile],
                    '--fan', fan_name.lower(),  # Use lowercase for asusctl
                    '--data', curve_data
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            print(f"asusctl output: {result.stdout}")
            if result.stderr:
                print(f"asusctl error: {result.stderr}")
            
            if result.returncode == 0:
                # Verify the curve was applied by reading it back
                applied_curves = self.get_fan_curves(profile)
                applied_curve = applied_curves.get(fan_name)
                
                if applied_curve and self._curves_match(curve, applied_curve):
                    print(f"✅ Curve successfully applied and verified for {fan_name}")
                else:
                    print(f"⚠️  Curve applied but verification failed for {fan_name}")
                
                # Save to persistent storage
                if save_persistent:
                    try:
                        from .fan_curve_persistence import FanCurvePersistence
                        persistence = FanCurvePersistence()
                        persistence.save_active_curve(profile, fan_name, curve)
                    except Exception as e:
                        print(f"Warning: Could not save curve to persistent storage: {e}")
                
                return True, f"Fan curve set for {fan_name}"
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                return False, f"asusctl failed: {error_msg}"
        except Exception as e:
            return False, str(e)
    
    def _curves_match(self, curve1: FanCurve, curve2: FanCurve) -> bool:
        """Check if two curves match (for verification)."""
        if not curve1 or not curve2:
            return False
        if len(curve1.points) != len(curve2.points):
            return False
        
        for p1, p2 in zip(curve1.points, curve2.points):
            if abs(p1.temperature - p2.temperature) > 1 or abs(p1.fan_speed - p2.fan_speed) > 1:
                return False
        return True
    
    def enable_fan_curves(self, profile: Profile, enabled: bool) -> Tuple[bool, str]:
        """
        Enable or disable fan curves for a profile.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            profile_map = {
                Profile.BALANCED: 'Balanced',
                Profile.QUIET: 'Quiet',
                Profile.PERFORMANCE: 'Performance'
            }
            
            result = subprocess.run(
                [
                    'asusctl', 'fan-curve',
                    '--mod-profile', profile_map[profile],
                    '--enable-fan-curves', str(enabled).lower()
                ],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                status = "enabled" if enabled else "disabled"
                return True, f"Fan curves {status} for {profile.value}"
            else:
                return False, result.stderr or result.stdout
        except Exception as e:
            return False, str(e)
    
    def get_fan_curve_enabled(self, profile: Profile) -> Optional[bool]:
        """Check if fan curves are enabled for a profile."""
        try:
            result = subprocess.run(
                ['asusctl', 'fan-curve', '--get-enabled'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                output = result.stdout.strip().lower()
                return 'true' in output or 'enabled' in output or 'yes' in output
        except Exception:
            pass
        
        return None
    
    def test_fan(self, fan_name: str, duration: int = 5) -> Tuple[bool, str]:
        """
        Test fan by setting it to 100% for a specified duration.
        
        Args:
            fan_name: Name of the fan (e.g., 'CPU', 'GPU')
            duration: Duration in seconds (default: 5)
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Use the max preset curve (already has 8 points)
            max_curve = get_preset_curve('max')
            
            # Get current profile
            current_profile = self.get_current_profile() or Profile.BALANCED
            
            # Save original curve if possible (store it temporarily)
            original_curves = self.get_fan_curves(current_profile)
            original_curve = original_curves.get(fan_name)
            
            # Set fan to 100% using a temporary curve
            curve_data = max_curve.to_asusctl_format()
            profile_map = {
                Profile.BALANCED: 'Balanced',
                Profile.QUIET: 'Quiet',
                Profile.PERFORMANCE: 'Performance'
            }
            
            # Apply max curve
            result = subprocess.run(
                [
                    'asusctl', 'fan-curve',
                    '--mod-profile', profile_map[current_profile],
                    '--fan', fan_name,
                    '--data', curve_data
                ],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return False, f"Failed to set fan to 100%: {result.stderr or result.stdout}"
            
            # Note: The actual duration wait and restore would need to be handled
            # by the calling code using threading/timers since this is synchronous
            return True, f"Fan {fan_name} set to 100% for testing"
            
        except Exception as e:
            return False, str(e)


# Preset fan curves
def get_preset_curve(name: str) -> FanCurve:
    """
    Get a preset fan curve with exactly 8 points (required by asusctl).
    
    Available presets:
    - 'quiet' / 'silent': Low fan speeds, quiet operation
    - 'balanced': Balanced cooling and noise
    - 'performance': Aggressive cooling, higher fan speeds
    - 'conservative': Fan at 100% at 60% utilization (54°C equivalent)
    - 'max': Maximum fan speed at all times
    """
    presets = {
        'quiet': FanCurve([
            FanCurvePoint(30, 20),
            FanCurvePoint(40, 25),
            FanCurvePoint(50, 30),
            FanCurvePoint(60, 40),
            FanCurvePoint(70, 50),
            FanCurvePoint(80, 60),
            FanCurvePoint(85, 70),
            FanCurvePoint(90, 80),
        ]),
        'silent': FanCurve([
            FanCurvePoint(30, 15),
            FanCurvePoint(40, 20),
            FanCurvePoint(50, 25),
            FanCurvePoint(60, 35),
            FanCurvePoint(70, 45),
            FanCurvePoint(80, 55),
            FanCurvePoint(85, 65),
            FanCurvePoint(90, 75),
        ]),
        'balanced': FanCurve([
            FanCurvePoint(30, 30),
            FanCurvePoint(40, 35),
            FanCurvePoint(50, 45),
            FanCurvePoint(60, 55),
            FanCurvePoint(70, 65),
            FanCurvePoint(80, 75),
            FanCurvePoint(85, 85),
            FanCurvePoint(90, 95),
        ]),
        'performance': FanCurve([
            FanCurvePoint(30, 40),
            FanCurvePoint(40, 50),
            FanCurvePoint(50, 60),
            FanCurvePoint(60, 70),
            FanCurvePoint(70, 80),
            FanCurvePoint(80, 90),
            FanCurvePoint(85, 100),
            FanCurvePoint(90, 100),
        ]),
        'conservative': FanCurve([
            FanCurvePoint(30, 30),
            FanCurvePoint(40, 40),
            FanCurvePoint(50, 60),
            FanCurvePoint(54, 100),  # 100% at ~60% utilization (54°C)
            FanCurvePoint(60, 100),
            FanCurvePoint(70, 100),
            FanCurvePoint(80, 100),
            FanCurvePoint(90, 100),
        ]),
        'max': FanCurve([
            FanCurvePoint(30, 100),
            FanCurvePoint(40, 100),
            FanCurvePoint(50, 100),
            FanCurvePoint(60, 100),
            FanCurvePoint(70, 100),
            FanCurvePoint(80, 100),
            FanCurvePoint(85, 100),
            FanCurvePoint(90, 100),
        ]),
        'loudmouth': FanCurve([
            FanCurvePoint(30, 100),  # Max at all temps
            FanCurvePoint(40, 100),
            FanCurvePoint(50, 100),
            FanCurvePoint(60, 100),
            FanCurvePoint(70, 100),
            FanCurvePoint(80, 100),
            FanCurvePoint(85, 100),
            FanCurvePoint(90, 100),
        ]),
        'shush': FanCurve([
            FanCurvePoint(30, 10),   # Very quiet
            FanCurvePoint(40, 15),
            FanCurvePoint(50, 20),
            FanCurvePoint(60, 30),
            FanCurvePoint(70, 40),
            FanCurvePoint(80, 50),
            FanCurvePoint(85, 60),
            FanCurvePoint(90, 70),
        ]),
    }
    
    return presets.get(name.lower(), presets['balanced'])


