"""
Tests for asusctl interface module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.control.asusctl_interface import (
    AsusctlInterface,
    Profile,
    FanCurve,
    FanCurvePoint,
    get_preset_curve
)


class TestFanCurvePoint:
    """Test FanCurvePoint class."""
    
    def test_point_creation(self):
        """Test creating a fan curve point."""
        point = FanCurvePoint(50, 60)
        
        assert point.temperature == 50
        assert point.fan_speed == 60
    
    def test_point_bounds_clamping(self):
        """Test point value clamping to valid ranges."""
        point1 = FanCurvePoint(100, 120)  # Both out of range
        assert point1.temperature == 90  # Clamped to max
        assert point1.fan_speed == 100  # Clamped to max
        
        point2 = FanCurvePoint(20, -10)  # Both out of range
        assert point2.temperature == 30  # Clamped to min
        assert point2.fan_speed == 0  # Clamped to min
    
    def test_point_to_asusctl_format(self):
        """Test converting point to asusctl format."""
        point = FanCurvePoint(50, 60)
        assert point.to_asusctl_format() == "50c:60%"
    
    def test_point_from_asusctl_format(self):
        """Test parsing point from asusctl format."""
        # Test new format
        point = FanCurvePoint.from_asusctl_format("50c:60%")
        assert point.temperature == 50
        assert point.fan_speed == 60
        # Test old format (backward compatibility)
        point2 = FanCurvePoint.from_asusctl_format("50 60")
        assert point2.temperature == 50
        assert point2.fan_speed == 60
    
    def test_point_from_asusctl_format_invalid(self):
        """Test parsing invalid asusctl format."""
        with pytest.raises(ValueError):
            FanCurvePoint.from_asusctl_format("invalid")


class TestFanCurve:
    """Test FanCurve class."""
    
    def test_curve_creation(self):
        """Test creating a fan curve."""
        points = [
            FanCurvePoint(30, 20),
            FanCurvePoint(70, 80)
        ]
        curve = FanCurve(points)
        
        assert len(curve.points) == 2
        assert curve.points[0].temperature == 30
        assert curve.points[1].temperature == 70
    
    def test_curve_auto_sorting(self):
        """Test that points are automatically sorted by temperature."""
        points = [
            FanCurvePoint(70, 80),
            FanCurvePoint(30, 20)
        ]
        curve = FanCurve(points)
        
        assert curve.points[0].temperature == 30
        assert curve.points[1].temperature == 70
    
    def test_curve_validation_min_points(self):
        """Test curve validation requires at least 2 points."""
        with pytest.raises(ValueError, match="at least 2"):
            FanCurve([FanCurvePoint(50, 50)])
    
    def test_curve_validation_duplicate_temps(self):
        """Test curve validation rejects duplicate temperatures."""
        points = [
            FanCurvePoint(50, 50),
            FanCurvePoint(50, 60)  # Duplicate temp
        ]
        
        with pytest.raises(ValueError, match="duplicate"):
            FanCurve(points)
    
    def test_curve_validation_monotonic(self):
        """Test curve validation requires monotonic fan speeds."""
        points = [
            FanCurvePoint(30, 50),
            FanCurvePoint(70, 40)  # Decreasing speed
        ]
        
        with pytest.raises(ValueError, match="decrease"):
            FanCurve(points)
    
    def test_curve_add_point(self):
        """Test adding a point to curve."""
        curve = FanCurve([
            FanCurvePoint(30, 20),
            FanCurvePoint(70, 80)
        ])
        
        curve.add_point(50, 50)
        
        assert len(curve.points) == 3
        assert any(p.temperature == 50 for p in curve.points)
    
    def test_curve_add_point_replaces_existing(self):
        """Test adding point replaces existing at same temperature."""
        curve = FanCurve([
            FanCurvePoint(30, 20),
            FanCurvePoint(50, 50),
            FanCurvePoint(70, 80)
        ])
        
        curve.add_point(50, 60)  # Replace existing
        
        assert len(curve.points) == 3
        point = next(p for p in curve.points if p.temperature == 50)
        assert point.fan_speed == 60
    
    def test_curve_remove_point(self):
        """Test removing a point from curve."""
        curve = FanCurve([
            FanCurvePoint(30, 20),
            FanCurvePoint(50, 50),
            FanCurvePoint(70, 80)
        ])
        
        curve.remove_point(50)
        
        assert len(curve.points) == 2
        assert not any(p.temperature == 50 for p in curve.points)
    
    def test_curve_remove_point_minimum(self):
        """Test cannot remove point if only 2 remain."""
        curve = FanCurve([
            FanCurvePoint(30, 20),
            FanCurvePoint(70, 80)
        ])
        
        with pytest.raises(ValueError, match="at least 2"):
            curve.remove_point(30)
    
    def test_curve_to_asusctl_format(self):
        """Test converting curve to asusctl format."""
        curve = FanCurve([
            FanCurvePoint(30, 20),
            FanCurvePoint(70, 80)
        ])
        
        result = curve.to_asusctl_format()
        # Format should be comma-separated: "30c:20%,70c:80%"
        assert "30c:20%" in result
        assert "70c:80%" in result
        assert "," in result
    
    def test_curve_from_asusctl_format(self):
        """Test parsing curve from asusctl format."""
        curve = FanCurve.from_asusctl_format("30 20 70 80")
        
        assert len(curve.points) == 2
        assert curve.points[0].temperature == 30
        assert curve.points[1].temperature == 70
    
    def test_curve_get_fan_speed_at_temp(self):
        """Test getting fan speed for temperature with interpolation."""
        curve = FanCurve([
            FanCurvePoint(30, 20),
            FanCurvePoint(70, 80)
        ])
        
        # Test exact points
        assert curve.get_fan_speed_at_temp(30) == 20
        assert curve.get_fan_speed_at_temp(70) == 80
        
        # Test interpolation
        speed = curve.get_fan_speed_at_temp(50)
        assert 20 <= speed <= 80  # Should be between the two points
    
    def test_curve_to_dict(self):
        """Test converting curve to dictionary."""
        curve = FanCurve([
            FanCurvePoint(30, 20),
            FanCurvePoint(70, 80)
        ])
        
        data = curve.to_dict()
        
        assert 'points' in data
        assert len(data['points']) == 2
        assert data['points'][0]['temperature'] == 30
    
    def test_curve_from_dict(self):
        """Test creating curve from dictionary."""
        data = {
            'points': [
                {'temperature': 30, 'fan_speed': 20},
                {'temperature': 70, 'fan_speed': 80}
            ]
        }
        
        curve = FanCurve.from_dict(data)
        
        assert len(curve.points) == 2
        assert curve.points[0].temperature == 30


class TestPresetCurves:
    """Test preset fan curves."""
    
    def test_get_preset_quiet(self):
        """Test getting quiet preset."""
        curve = get_preset_curve('quiet')
        
        assert isinstance(curve, FanCurve)
        assert len(curve.points) > 0
    
    def test_get_preset_balanced(self):
        """Test getting balanced preset."""
        curve = get_preset_curve('balanced')
        
        assert isinstance(curve, FanCurve)
        assert len(curve.points) > 0
    
    def test_get_preset_performance(self):
        """Test getting performance preset."""
        curve = get_preset_curve('performance')
        
        assert isinstance(curve, FanCurve)
        assert len(curve.points) > 0
    
    def test_get_preset_invalid(self):
        """Test getting invalid preset defaults to balanced."""
        curve = get_preset_curve('invalid')
        
        assert isinstance(curve, FanCurve)
        # Should default to balanced
        assert len(curve.points) > 0


class TestAsusctlInterface:
    """Test AsusctlInterface class."""
    
    @patch('subprocess.run')
    def test_check_asusctl_available(self, mock_run):
        """Test checking if asusctl is available."""
        mock_run.return_value = Mock(returncode=0)
        
        interface = AsusctlInterface()
        assert interface.is_available() == True
    
    @patch('subprocess.run')
    def test_check_asusctl_not_available(self, mock_run):
        """Test when asusctl is not available."""
        mock_run.side_effect = FileNotFoundError()
        
        interface = AsusctlInterface()
        assert interface.is_available() == False
    
    @patch('subprocess.run')
    def test_get_current_profile(self, mock_run):
        """Test getting current power profile."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Balanced"
        )
        
        interface = AsusctlInterface()
        profile = interface.get_current_profile()
        
        assert profile == Profile.BALANCED
    
    @patch('subprocess.run')
    def test_set_profile(self, mock_run):
        """Test setting power profile."""
        mock_run.return_value = Mock(returncode=0)
        
        interface = AsusctlInterface()
        success, message = interface.set_profile(Profile.BALANCED)
        
        assert success == True
        assert "Balanced" in message
    
    @patch('subprocess.run')
    def test_set_profile_failure(self, mock_run):
        """Test setting profile failure."""
        mock_run.return_value = Mock(returncode=1, stderr="Error")
        
        interface = AsusctlInterface()
        success, message = interface.set_profile(Profile.BALANCED)
        
        assert success == False
    
    @patch('subprocess.run')
    def test_get_fan_curves(self, mock_run):
        """Test getting fan curves."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="CPU fan\n30 20 70 80"
        )
        
        interface = AsusctlInterface()
        curves = interface.get_fan_curves(Profile.BALANCED)
        
        assert isinstance(curves, dict)
    
    @patch('subprocess.run')
    def test_set_fan_curve(self, mock_run):
        """Test setting fan curve."""
        mock_run.return_value = Mock(returncode=0)
        
        interface = AsusctlInterface()
        curve = FanCurve([
            FanCurvePoint(30, 20),
            FanCurvePoint(70, 80)
        ])
        
        success, message = interface.set_fan_curve(
            Profile.BALANCED,
            "CPU",
            curve
        )
        
        assert success == True
    
    @patch('subprocess.run')
    def test_enable_fan_curves(self, mock_run):
        """Test enabling fan curves."""
        mock_run.return_value = Mock(returncode=0)
        
        interface = AsusctlInterface()
        success, message = interface.enable_fan_curves(Profile.BALANCED, True)
        
        assert success == True
        assert "enabled" in message.lower()


