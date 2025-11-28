#!/usr/bin/env python3
"""
Fan Status Tab

Visual representation showing current position on fan curves, temperatures, RPM, and loads.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QGridLayout, QComboBox, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSignal as Signal
from PyQt6.QtGui import QFont, QPen, QBrush, QColor, QMovie
import pyqtgraph as pg
import numpy as np

from ..control.asusctl_interface import AsusctlInterface, Profile, FanCurve
from ..monitoring.system_monitor import SystemMonitor
from ..control.profile_manager import ProfileManager
from ..control.curve_file_manager import CurveFileManager
from .game_style_theme import GAME_COLORS, GAME_STYLES
from .ui_scaling import UIScaling


class FanStatusWidget(QWidget):
    """Widget showing status for a single fan (CPU or GPU)."""
    
    def __init__(self, fan_name: str, monitor: SystemMonitor, asusctl: AsusctlInterface, parent=None):
        super().__init__(parent)
        self.fan_name = fan_name.upper()
        self.monitor = monitor
        self.asusctl = asusctl
        self.profile_manager = ProfileManager()
        self.curve_manager = CurveFileManager()
        self.current_curve = None
        self.current_temp = None
        self.current_rpm = None
        self.current_load = None
        self.glow_layers = []  # Initialize glow layers list
        self.applying_curve = False
        
        # Base sizes for scaling
        self._base_title_font_size = 16
        self._base_value_font_size = 18
        self._base_label_font_size = 10
        self._base_layout_margins = (15, 15, 15, 15)
        self._base_layout_spacing = 10
        self._base_graph_height = 300
        
        self._init_ui()
        self._load_curve()
        self._populate_curve_combo()
        self._connect_signals()
        self.update_scaling()
    
    def _connect_signals(self):
        """Connect widget signals."""
        self.curve_combo.currentTextChanged.connect(self._on_curve_selection_changed)
    
    def _on_curve_selection_changed(self):
        """Handle curve selection change - apply immediately."""
        selected = self.curve_combo.currentText()
        if not selected or self.applying_curve:
            return
        
        current_active = self._get_current_active_curve_name()
        if selected != current_active:
            self._apply_selected_curve()
    
    def _get_current_active_curve_name(self) -> str:
        """Get the name of currently active curve."""
        try:
            current_profile = self.asusctl.get_current_profile() or Profile.BALANCED
            
            # Check persistent storage first
            from ..control.fan_curve_persistence import FanCurvePersistence
            persistence = FanCurvePersistence()
            saved_curves = persistence.load_active_curves(current_profile)
            active_curve = saved_curves.get(self.fan_name)
            
            if active_curve:
                # Try to match with known curves
                return self._match_curve_to_name(active_curve)
            
            # Fallback to profile name
            return current_profile.value.capitalize()
        except:
            return "Balanced"
    
    def _match_curve_to_name(self, curve: FanCurve) -> str:
        """Match a curve to its name in available options."""
        if not curve or not curve.points:
            return "Unknown"
        
        # Check built-in presets
        from ..control.asusctl_interface import get_preset_curve
        for preset in ['quiet', 'balanced', 'performance']:
            try:
                preset_curve = get_preset_curve(preset)
                if self._curves_equal(curve, preset_curve):
                    return preset.capitalize()
            except:
                continue
        
        # Check saved profiles
        try:
            profiles = self.profile_manager.list_profiles()
            for profile_name in profiles:
                profile = self.profile_manager.get_profile(profile_name)
                if profile:
                    profile_curve = profile.cpu_fan_curve if self.fan_name == "CPU" else profile.gpu_fan_curve
                    if profile_curve and self._curves_equal(curve, profile_curve):
                        return f"Profile: {profile_name}"
        except:
            pass
        
        # Check custom curves
        try:
            custom_curves = self.curve_manager.list_curves()
            for curve_name in custom_curves:
                custom_curve_data = self.curve_manager.load_curve(curve_name)
                if custom_curve_data:
                    # Convert to FanCurve for comparison
                    from ..control.asusctl_interface import FanCurve, FanCurvePoint
                    custom_curve = FanCurve([FanCurvePoint(t, s) for t, s in custom_curve_data.points])
                    if self._curves_equal(curve, custom_curve):
                        return f"Custom: {curve_name}"
        except:
            pass
        
        return "Custom Curve"
    
    def _curves_equal(self, curve1: FanCurve, curve2: FanCurve) -> bool:
        """Check if two curves are equal."""
        if not curve1 or not curve2:
            return False
        if len(curve1.points) != len(curve2.points):
            return False
        
        points1 = sorted(curve1.points, key=lambda p: p.temperature)
        points2 = sorted(curve2.points, key=lambda p: p.temperature)
        
        for p1, p2 in zip(points1, points2):
            if p1.temperature != p2.temperature or p1.fan_speed != p2.fan_speed:
                return False
        return True
    
    def _populate_curve_combo(self):
        """Populate the curve selection combo box."""
        self.curve_combo.clear()
        
        # Built-in presets
        presets = ["Quiet", "Balanced", "Performance"]
        for preset in presets:
            self.curve_combo.addItem(preset)
        
        # Add separator (visual only)
        self.curve_combo.insertSeparator(self.curve_combo.count())
        
        # Saved profiles
        try:
            profiles = self.profile_manager.list_profiles()
            for profile_name in profiles:
                profile = self.profile_manager.get_profile(profile_name)
                if profile:
                    # Check if profile has curve for this fan
                    has_curve = False
                    if self.fan_name == "CPU" and profile.cpu_fan_curve:
                        has_curve = True
                    elif self.fan_name == "GPU" and profile.gpu_fan_curve:
                        has_curve = True
                    
                    if has_curve:
                        self.curve_combo.addItem(f"Profile: {profile_name}")
        except Exception as e:
            print(f"Error loading profiles: {e}")
        
        # Add separator if we have profiles
        if self.curve_combo.count() > len(presets) + 1:
            self.curve_combo.insertSeparator(self.curve_combo.count())
        
        # Custom curves from Fan Curve Builder
        try:
            custom_curves = self.curve_manager.list_curves()
            for curve_name in custom_curves:
                # Validate curve before adding
                curve_data = self.curve_manager.load_curve(curve_name)
                if curve_data and self._validate_curve_data(curve_data):
                    self.curve_combo.addItem(f"Custom: {curve_name}")
        except Exception as e:
            print(f"Error loading custom curves: {e}")
        
        # Set current selection
        current_active = self._get_current_active_curve_name()
        index = self.curve_combo.findText(current_active)
        if index >= 0:
            self.curve_combo.setCurrentIndex(index)
    
    def _validate_curve_data(self, curve_data) -> bool:
        """Validate curve data before allowing selection."""
        try:
            if not curve_data or not curve_data.points:
                return False
            
            # Check minimum points
            if len(curve_data.points) < 2:
                return False
            
            # Check temperature range and monotonic increase
            temps = [p[0] for p in curve_data.points]
            speeds = [p[1] for p in curve_data.points]
            
            # Validate ranges
            for temp, speed in curve_data.points:
                if not (30 <= temp <= 90) or not (0 <= speed <= 100):
                    return False
            
            # Check monotonic temperature increase
            sorted_temps = sorted(temps)
            if temps != sorted_temps:
                return False
            
            return True
        except:
            return False
    
    def _apply_selected_curve(self):
        """Apply the selected curve."""
        if self.applying_curve:
            return
        
        selected = self.curve_combo.currentText()
        if not selected:
            return
        
        self.applying_curve = True
        
        try:
            curve_to_apply = None
            
            # Parse selection type
            if selected in ["Quiet", "Balanced", "Performance"]:
                # Built-in preset
                from ..control.asusctl_interface import get_preset_curve
                curve_to_apply = get_preset_curve(selected.lower())
            
            elif selected.startswith("Profile: "):
                # Saved profile
                profile_name = selected[9:]  # Remove "Profile: " prefix
                profile = self.profile_manager.get_profile(profile_name)
                if profile:
                    curve_to_apply = profile.cpu_fan_curve if self.fan_name == "CPU" else profile.gpu_fan_curve
            
            elif selected.startswith("Custom: "):
                # Custom curve
                curve_name = selected[8:]  # Remove "Custom: " prefix
                curve_data = self.curve_manager.load_curve(curve_name)
                if curve_data:
                    # Convert to FanCurve
                    from ..control.asusctl_interface import FanCurve, FanCurvePoint
                    curve_to_apply = FanCurve([FanCurvePoint(t, s) for t, s in curve_data.points])
            
            if curve_to_apply:
                # Apply the curve
                current_profile = self.asusctl.get_current_profile() or Profile.BALANCED
                success, message = self.asusctl.set_fan_curve(
                    current_profile, self.fan_name, curve_to_apply, save_persistent=True
                )
                
                if success:
                    # Refresh curve display
                    self._load_curve()
                    self._populate_curve_combo()  # Refresh to show new active curve
                else:
                    QMessageBox.warning(self, "Error", f"Failed to apply curve: {message}")
            else:
                QMessageBox.warning(self, "Error", "Failed to load selected curve")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error applying curve: {str(e)}")
        
        finally:
            self.applying_curve = False
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with title and curve selection
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel(f"{self.fan_name} Fan Status")
        self.title_label.setStyleSheet(f"color: {GAME_COLORS['accent_blue']}; margin-bottom: 10px;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Curve selection combo box
        curve_label = QLabel("Apply Curve:")
        curve_label.setStyleSheet(f"color: {GAME_COLORS['text_secondary']}; margin-right: 8px;")
        header_layout.addWidget(curve_label)
        
        self.curve_combo = QComboBox()
        self.curve_combo.setMinimumWidth(180)
        self.curve_combo.setStyleSheet(GAME_STYLES['combobox'])
        header_layout.addWidget(self.curve_combo)
        
        layout.addLayout(header_layout)
        
        # Main content area - horizontal split
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Left side: Current metrics
        metrics_group = self._create_metrics_group()
        content_layout.addWidget(metrics_group, 1)
        
        # Right side: Visual curve representation
        self.curve_widget = self._create_curve_widget()
        self.curve_widget.setMinimumHeight(200)  # Minimum height to ensure visibility
        content_layout.addWidget(self.curve_widget, 2)
        
        layout.addLayout(content_layout)
        
        # Game-style theming
        self.setStyleSheet(GAME_STYLES['widget'])
        
        # Apply groupbox theme to all groupboxes
        for child in self.findChildren(QGroupBox):
            child.setStyleSheet(GAME_STYLES['groupbox'])
    
    def _create_metrics_group(self) -> QGroupBox:
        """Create the metrics display group."""
        group = QGroupBox("Current Status")
        layout = QGridLayout(group)
        layout.setSpacing(10)
        
        # Temperature
        self.temp_label = QLabel("Temperature:")
        self.temp_value = QLabel("N/A")
        self.temp_value.setStyleSheet("font-weight: bold; color: #2196F3;")
        layout.addWidget(self.temp_label, 0, 0)
        layout.addWidget(self.temp_value, 0, 1)
        
        # Fan Speed (RPM)
        self.rpm_label = QLabel("Fan Speed (RPM):")
        self.rpm_value = QLabel("N/A")
        self.rpm_value.setStyleSheet("font-weight: bold; color: #4CAF50;")
        layout.addWidget(self.rpm_label, 1, 0)
        layout.addWidget(self.rpm_value, 1, 1)
        
        # Fan Speed (%)
        self.percent_label = QLabel("Fan Speed (%):")
        self.percent_value = QLabel("N/A")
        self.percent_value.setStyleSheet("font-weight: bold; color: #FF9800;")
        layout.addWidget(self.percent_label, 2, 0)
        layout.addWidget(self.percent_value, 2, 1)
        
        # Load
        load_name = "CPU Load" if self.fan_name == "CPU" else "GPU Load"
        self.load_label = QLabel(f"{load_name}:")
        self.load_value = QLabel("N/A")
        self.load_value.setStyleSheet("font-weight: bold; color: #9C27B0;")
        layout.addWidget(self.load_label, 3, 0)
        layout.addWidget(self.load_value, 3, 1)
        
        # Expected fan speed from curve
        self.expected_label = QLabel("Expected Speed:")
        self.expected_value = QLabel("N/A")
        self.expected_value.setStyleSheet("font-weight: bold; color: #F44336;")
        layout.addWidget(self.expected_label, 4, 0)
        layout.addWidget(self.expected_value, 4, 1)
        
        return group
    
    def _create_curve_widget(self) -> QGroupBox:
        """Create the visual curve representation."""
        group = QGroupBox("Fan Curve Visualization")
        layout = QVBoxLayout(group)
        
        # Create PyQtGraph widget with game-style theme
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground(pg.mkColor(GAME_COLORS['bg_card']))
        self.graph_widget.setLabel('left', 'Fan Speed (%)', color=GAME_COLORS['text_secondary'])
        self.graph_widget.setLabel('bottom', 'Temperature (°C)', color=GAME_COLORS['text_secondary'])
        self.graph_widget.showGrid(x=True, y=True, alpha=0.1)
        self.graph_widget.setRange(xRange=[25, 95], yRange=[0, 105])
        
        # Style the axes with game colors
        self.graph_widget.getAxis('left').setPen(pg.mkPen(color=GAME_COLORS['border'], width=1))
        self.graph_widget.getAxis('bottom').setPen(pg.mkPen(color=GAME_COLORS['border'], width=1))
        self.graph_widget.getAxis('left').setTextPen(pg.mkPen(color=GAME_COLORS['text_secondary']))
        self.graph_widget.getAxis('bottom').setTextPen(pg.mkPen(color=GAME_COLORS['text_secondary']))
        
        # Plot items
        self.curve_plot = None  # The fan curve line
        self.horizontal_line = None  # Horizontal line representing current fan speed
        self.intersection_point = None  # Glowing dot at intersection of horizontal line and curve
        self.glow_layers = []  # List of glow effect layers for the intersection point
        
        # Set minimum and preferred size for graph
        self.graph_widget.setMinimumHeight(200)
        self.graph_widget.setMinimumWidth(300)
        layout.addWidget(self.graph_widget)
        
        return group
    
    def _load_curve(self):
        """Load the current fan curve for this fan."""
        try:
            current_profile = self.asusctl.get_current_profile() or Profile.BALANCED
            
            # First try loading from persistent storage (has applied curves)
            from ..control.fan_curve_persistence import FanCurvePersistence
            persistence = FanCurvePersistence()
            saved_curves = persistence.load_active_curves(current_profile)
            self.current_curve = saved_curves.get(self.fan_name)
            
            # Fall back to asusctl if not in persistent storage
            if not self.current_curve:
                curves = self.asusctl.get_fan_curves(current_profile)
                self.current_curve = curves.get(self.fan_name)
            
            # If no curve found, use default Balanced curve
            if not self.current_curve:
                from ..control.asusctl_interface import get_preset_curve
                self.current_curve = get_preset_curve('balanced')
                print(f"Using default Balanced curve for {self.fan_name}")
            
            if self.current_curve:
                self._update_curve_plot()
        except Exception as e:
            print(f"Error loading curve for {self.fan_name}: {e}")
            # Even on error, provide default curve
            try:
                from ..control.asusctl_interface import get_preset_curve
                self.current_curve = get_preset_curve('balanced')
                if self.current_curve:
                    self._update_curve_plot()
            except:
                self.current_curve = None
    
    def _update_curve_plot(self):
        """Update the curve plot with current curve."""
        if not self.current_curve or not self.current_curve.points:
            return
        
        # Clear existing plots (this will also clear horizontal line and intersection point)
        self.graph_widget.clear()
        self.horizontal_line = None
        self.intersection_point = None
        self.glow_layers.clear()
        
        # Get curve points
        temps = [p.temperature for p in self.current_curve.points]
        speeds = [p.fan_speed for p in self.current_curve.points]
        
        # Sort by temperature to ensure proper line drawing
        sorted_data = sorted(zip(temps, speeds), key=lambda x: x[0])
        temps, speeds = zip(*sorted_data) if sorted_data else ([], [])
        
        # Draw the curve line
        if len(temps) > 1:
            # Create smooth curve by interpolating
            temp_range = np.linspace(min(temps), max(temps), 100)
            speed_range = [self.current_curve.get_fan_speed_at_temp(int(t)) for t in temp_range]
            
            self.curve_plot = self.graph_widget.plot(
                temp_range, speed_range,
                pen=pg.mkPen(color=GAME_COLORS['accent_blue'], width=2),
                name='Fan Curve'
            )
            
            # Plot control points
            scatter = self.graph_widget.plot(
                temps, speeds,
                pen=None,
                symbol='o',
                symbolBrush=pg.mkBrush(color=GAME_COLORS['accent_blue']),
                symbolPen=pg.mkPen(color=GAME_COLORS['accent_cyan'], width=2),
                symbolSize=8,
                name='Control Points'
            )
        
        # Update horizontal line and intersection marker (redraw after curve is updated)
        self._update_current_position_marker()
    
    def _update_current_position_marker(self):
        """Update the horizontal line and intersection point showing current fan speed on the curve."""
        # Show horizontal line even if no curve is loaded (just based on current fan speed)
        if self.current_rpm is None:
            # Remove markers if no RPM data
            if self.horizontal_line is not None:
                self.graph_widget.removeItem(self.horizontal_line)
                self.horizontal_line = None
            if self.intersection_point is not None:
                self.graph_widget.removeItem(self.intersection_point)
                self.intersection_point = None
            for glow_item in self.glow_layers:
                self.graph_widget.removeItem(glow_item)
            self.glow_layers.clear()
            return
        
        # Calculate current fan speed percentage (0-100%)
        max_rpm = 6000
        current_speed_pct = min(100, max(0, (self.current_rpm / max_rpm) * 100) if max_rpm > 0 else 0)
        
        # Remove old horizontal line
        if self.horizontal_line is not None:
            self.graph_widget.removeItem(self.horizontal_line)
        
        # Draw horizontal line at current fan speed percentage
        # Line spans the entire temperature range (25 to 95)
        temp_min, temp_max = 25, 95
        self.horizontal_line = self.graph_widget.plot(
            [temp_min, temp_max],
            [current_speed_pct, current_speed_pct],
            pen=pg.mkPen(color=GAME_COLORS['accent_green'], width=2, style=Qt.PenStyle.DashLine),
            name='Current Fan Speed'
        )
        
        # Find intersection point where horizontal line meets the fan curve (only if curve exists)
        if self.current_curve and self.current_curve.points:
            intersection_temp = self._find_intersection_temperature(current_speed_pct)
            
            # Remove old intersection point and glow layers
            if self.intersection_point is not None:
                self.graph_widget.removeItem(self.intersection_point)
                self.intersection_point = None
            for glow_item in self.glow_layers:
                self.graph_widget.removeItem(glow_item)
            self.glow_layers.clear()
            
            if intersection_temp is not None:
                # Draw glowing dot at intersection point
                # Create a glowing effect with multiple circles
                glow_color = QColor(GAME_COLORS['accent_green'])
                
                # Outer glow (larger, semi-transparent)
                glow_outer = self.graph_widget.plot(
                    [intersection_temp], [current_speed_pct],
                    pen=None,
                    symbol='o',
                    symbolBrush=pg.mkBrush(color=(glow_color.red(), glow_color.green(), glow_color.blue(), 60)),
                    symbolSize=20,
                    name='Glow Outer'
                )
                self.glow_layers.append(glow_outer)
                
                # Middle glow (medium, more visible)
                glow_middle = self.graph_widget.plot(
                    [intersection_temp], [current_speed_pct],
                    pen=None,
                    symbol='o',
                    symbolBrush=pg.mkBrush(color=(glow_color.red(), glow_color.green(), glow_color.blue(), 120)),
                    symbolSize=14,
                    name='Glow Middle'
                )
                self.glow_layers.append(glow_middle)
                
                # Inner dot (solid, bright)
                self.intersection_point = self.graph_widget.plot(
                    [intersection_temp], [current_speed_pct],
                    pen=pg.mkPen(color=GAME_COLORS['accent_cyan'], width=2),
                    symbol='o',
                    symbolBrush=pg.mkBrush(color=GAME_COLORS['accent_green']),
                    symbolSize=10,
                    name='Intersection Point'
                )
    
    def _find_intersection_temperature(self, target_speed_pct: float) -> float:
        """
        Find the temperature at which the fan curve intersects the target fan speed.
        Returns None if no intersection is found.
        """
        if not self.current_curve or not self.current_curve.points:
            return None
        
        # Get sorted curve points
        points = sorted(self.current_curve.points, key=lambda p: p.temperature)
        
        # Check if target speed is outside curve bounds
        min_speed = min(p.fan_speed for p in points)
        max_speed = max(p.fan_speed for p in points)
        
        if target_speed_pct < min_speed:
            # Below minimum, return first point's temperature
            return float(points[0].temperature)
        if target_speed_pct > max_speed:
            # Above maximum, return last point's temperature
            return float(points[-1].temperature)
        
        # Find the segment where the curve crosses the target speed
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            
            speed1, speed2 = p1.fan_speed, p2.fan_speed
            
            # Check if target speed is within this segment
            if min(speed1, speed2) <= target_speed_pct <= max(speed1, speed2):
                # Linear interpolation to find temperature
                if speed2 == speed1:
                    # Horizontal segment - use midpoint
                    return (p1.temperature + p2.temperature) / 2.0
                
                # Linear interpolation
                temp_diff = p2.temperature - p1.temperature
                speed_diff = speed2 - speed1
                ratio = (target_speed_pct - speed1) / speed_diff
                intersection_temp = p1.temperature + ratio * temp_diff
                
                return intersection_temp
        
        # Fallback: find closest point
        closest_point = min(points, key=lambda p: abs(p.fan_speed - target_speed_pct))
        return float(closest_point.temperature)
    
    def update_status(self):
        """Update the status display with latest metrics."""
        metrics = self.monitor.get_metrics()
        
        # Get current temperature
        if self.fan_name == "CPU":
            self.current_temp = metrics.get('cpu_temp')
            self.current_load = metrics.get('cpu_percent', 0)
        else:  # GPU
            self.current_temp = metrics.get('gpu_temp')
            self.current_load = metrics.get('gpu_utilization', 0) or 0
        
        # Get current fan speed
        self.current_rpm = None
        fan_speeds = metrics.get('fan_speeds', [])
        for fan in fan_speeds:
            if fan.get('name', '').upper() == self.fan_name:
                self.current_rpm = fan.get('rpm')
                break
        
        # Update display
        if self.current_temp is not None:
            self.temp_value.setText(f"{self.current_temp:.1f}°C")
        else:
            self.temp_value.setText("N/A")
        
        if self.current_rpm is not None:
            self.rpm_value.setText(f"{self.current_rpm:,} RPM")
            # Estimate percentage (assuming max 6000 RPM)
            max_rpm = 6000
            speed_pct = min(100, (self.current_rpm / max_rpm) * 100) if max_rpm > 0 else 0
            self.percent_value.setText(f"{speed_pct:.1f}%")
        else:
            self.rpm_value.setText("N/A")
            self.percent_value.setText("N/A")
        
        if self.current_load is not None:
            self.load_value.setText(f"{self.current_load:.1f}%")
        else:
            self.load_value.setText("N/A")
        
        # Expected fan speed from curve
        if self.current_temp is not None and self.current_curve:
            expected_speed = self.current_curve.get_fan_speed_at_temp(int(self.current_temp))
            self.expected_value.setText(f"{expected_speed}%")
        else:
            self.expected_value.setText("N/A")
        
        # Reload curve if needed (check from persistent storage for applied curves)
        try:
            current_profile = self.asusctl.get_current_profile() or Profile.BALANCED
            # Try loading from persistent storage first (this has the applied curves)
            from ..control.fan_curve_persistence import FanCurvePersistence
            persistence = FanCurvePersistence()
            saved_curves = persistence.load_active_curves(current_profile)
            new_curve = saved_curves.get(self.fan_name)
            
            # Fall back to asusctl if not in persistent storage
            if not new_curve:
                curves = self.asusctl.get_fan_curves(current_profile)
                new_curve = curves.get(self.fan_name)
            
            # Use default if still no curve
            if not new_curve:
                from ..control.asusctl_interface import get_preset_curve
                new_curve = get_preset_curve('balanced')
            
            # Check if curve changed (compare points, not object reference)
            curve_changed = False
            if self.current_curve and new_curve:
                # Compare curve points
                if len(self.current_curve.points) != len(new_curve.points):
                    curve_changed = True
                else:
                    for p1, p2 in zip(self.current_curve.points, new_curve.points):
                        if p1.temperature != p2.temperature or p1.fan_speed != p2.fan_speed:
                            curve_changed = True
                            break
            elif (self.current_curve is None) != (new_curve is None):
                curve_changed = True
            
            if curve_changed:
                self.current_curve = new_curve
                self._update_curve_plot()
                # Update curve widget title with profile name
                if hasattr(self, 'curve_widget'):
                    self._update_curve_widget_title()
                
                # Refresh combo box selection
                if hasattr(self, 'curve_combo'):
                    current_active = self._get_current_active_curve_name()
                    current_selection = self.curve_combo.currentText()
                    if current_selection != current_active:
                        index = self.curve_combo.findText(current_active)
                        if index >= 0:
                            self.curve_combo.blockSignals(True)
                            self.curve_combo.setCurrentIndex(index)
                            self.curve_combo.blockSignals(False)
                        self._on_curve_selection_changed()
        except Exception as e:
            print(f"Error reloading curve for {self.fan_name}: {e}")
    
    def update_scaling(self):
        """Update widget scaling based on window size."""
        window = self.window()
        if not window:
            return
        
        scale = UIScaling.get_scale_factor(window)
        
        # Update title font
        if hasattr(self, 'title_label'):
            title_font = UIScaling.scale_font(self._base_title_font_size, window, scale)
            title_font.setBold(True)
            self.title_label.setFont(title_font)
        
        # Update value fonts
        for value_widget in [self.temp_value, self.rpm_value, self.percent_value, 
                            self.load_value, self.expected_value]:
            if hasattr(value_widget, 'setFont'):
                value_font = UIScaling.scale_font(self._base_value_font_size, window, scale)
                value_font.setBold(True)
                value_widget.setFont(value_font)
        
        # Update label fonts
        for label_widget in [self.temp_label, self.rpm_label, self.percent_label, 
                            self.load_label, self.expected_label]:
            if hasattr(label_widget, 'setFont'):
                label_font = UIScaling.scale_font(self._base_label_font_size, window, scale)
                label_widget.setFont(label_font)
        
        # Update layout margins and spacing
        layout = self.layout()
        if layout:
            margins = tuple(UIScaling.scale_size(m, window, scale) for m in self._base_layout_margins)
            layout.setContentsMargins(*margins)
            layout.setSpacing(UIScaling.scale_size(self._base_layout_spacing, window, scale))
        
        # Update graph widget size
        if hasattr(self, 'graph_widget'):
            graph_height = UIScaling.scale_size(self._base_graph_height, window, scale)
            self.graph_widget.setMinimumHeight(max(200, graph_height))
        
        # Update curve widget minimum height
        if hasattr(self, 'curve_widget'):
            curve_height = UIScaling.scale_size(self._base_graph_height, window, scale)
            self.curve_widget.setMinimumHeight(max(200, curve_height))
    
    def resizeEvent(self, event):
        """Handle resize to update scaling."""
        super().resizeEvent(event)
        self.update_scaling()
        
        # Always update the horizontal line and intersection marker with current fan speed
        # This ensures the line updates even if the curve hasn't changed
        self._update_current_position_marker()
    
    def _update_curve_widget_title(self):
        """Update the curve widget title - no longer needed as we removed profile from title."""
        # Update horizontal line and intersection marker based on current fan speed
        self._update_current_position_marker()


class FanStatusTab(QWidget):
    """Tab showing visual status for CPU and GPU fans."""
    
    def __init__(self, monitor: SystemMonitor, asusctl: AsusctlInterface, parent=None):
        super().__init__(parent)
        self.monitor = monitor
        self.asusctl = asusctl
        self._base_title_font_size = 20
        self._base_spacing = 20
        self._base_margins = (20, 20, 20, 20)
        
        self._init_ui()
        self._start_update_timer()
    
    def _init_ui(self):
        """Initialize the UI."""
        from PyQt6.QtWidgets import QScrollArea
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f5f5f5;
            }
        """)
        
        # Content widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(self._base_spacing)
        layout.setContentsMargins(*self._base_margins)
        
        # Title
        self.title = QLabel("Fan Status")
        title_font = QFont()
        title_font.setPointSize(self._base_title_font_size)
        title_font.setBold(True)
        self.title.setFont(title_font)
        self.title.setStyleSheet("color: #333; margin-bottom: 10px;")
        layout.addWidget(self.title)
        
        # CPU Fan Status
        self.cpu_fan_widget = FanStatusWidget("CPU", self.monitor, self.asusctl, self)
        layout.addWidget(self.cpu_fan_widget)
        
        # GPU Fan Status
        self.gpu_fan_widget = FanStatusWidget("GPU", self.monitor, self.asusctl, self)
        layout.addWidget(self.gpu_fan_widget)
        
        layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        # Styling - match game theme
        from .game_style_theme import GAME_COLORS
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {GAME_COLORS['bg_dark']};
            }}
            QScrollArea {{
                background-color: {GAME_COLORS['bg_dark']};
                border: none;
            }}
        """)
    
    def update_scaling(self):
        """Update scaling based on window size."""
        window = self.window()
        if not window:
            return
        
        scale = UIScaling.get_scale_factor(window)
        
        # Update title font
        if hasattr(self, 'title'):
            title_font = UIScaling.scale_font(self._base_title_font_size, window, scale)
            title_font.setBold(True)
            self.title.setFont(title_font)
        
        # Update child widgets
        if hasattr(self, 'cpu_fan_widget'):
            self.cpu_fan_widget.update_scaling()
        if hasattr(self, 'gpu_fan_widget'):
            self.gpu_fan_widget.update_scaling()
    
    def resizeEvent(self, event):
        """Handle resize to update scaling."""
        super().resizeEvent(event)
        self.update_scaling()
    
    def _start_update_timer(self):
        """Start timer to update status periodically."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start(1000)  # Update every second
    
    def _update_status(self):
        """Update all fan status widgets."""
        if hasattr(self, 'cpu_fan_widget'):
            self.cpu_fan_widget.update_status()
        if hasattr(self, 'gpu_fan_widget'):
            self.gpu_fan_widget.update_status()

