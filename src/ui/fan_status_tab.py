#!/usr/bin/env python3
"""
Fan Status Tab

Visual representation showing current position on fan curves, temperatures, RPM, and loads.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPen, QBrush, QColor
import pyqtgraph as pg
import numpy as np

from ..control.asusctl_interface import AsusctlInterface, Profile, FanCurve
from ..monitoring.system_monitor import SystemMonitor
from .game_style_theme import GAME_COLORS, GAME_STYLES


class FanStatusWidget(QWidget):
    """Widget showing status for a single fan (CPU or GPU)."""
    
    def __init__(self, fan_name: str, monitor: SystemMonitor, asusctl: AsusctlInterface, parent=None):
        super().__init__(parent)
        self.fan_name = fan_name.upper()
        self.monitor = monitor
        self.asusctl = asusctl
        self.current_curve = None
        self.current_temp = None
        self.current_rpm = None
        self.current_load = None
        self.glow_layers = []  # Initialize glow layers list
        
        self._init_ui()
        self._load_curve()
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel(f"{self.fan_name} Fan Status")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {GAME_COLORS['accent_blue']}; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Main content area - horizontal split
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Left side: Current metrics
        metrics_group = self._create_metrics_group()
        content_layout.addWidget(metrics_group, 1)
        
        # Right side: Visual curve representation
        curve_widget = self._create_curve_widget()
        content_layout.addWidget(curve_widget, 2)
        
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
        self.temp_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3;")
        layout.addWidget(self.temp_label, 0, 0)
        layout.addWidget(self.temp_value, 0, 1)
        
        # Fan Speed (RPM)
        self.rpm_label = QLabel("Fan Speed (RPM):")
        self.rpm_value = QLabel("N/A")
        self.rpm_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        layout.addWidget(self.rpm_label, 1, 0)
        layout.addWidget(self.rpm_value, 1, 1)
        
        # Fan Speed (%)
        self.percent_label = QLabel("Fan Speed (%):")
        self.percent_value = QLabel("N/A")
        self.percent_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #FF9800;")
        layout.addWidget(self.percent_label, 2, 0)
        layout.addWidget(self.percent_value, 2, 1)
        
        # Load
        load_name = "CPU Load" if self.fan_name == "CPU" else "GPU Load"
        self.load_label = QLabel(f"{load_name}:")
        self.load_value = QLabel("N/A")
        self.load_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #9C27B0;")
        layout.addWidget(self.load_label, 3, 0)
        layout.addWidget(self.load_value, 3, 1)
        
        # Expected fan speed from curve
        self.expected_label = QLabel("Expected Speed:")
        self.expected_value = QLabel("N/A")
        self.expected_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #F44336;")
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
        
        layout.addWidget(self.graph_widget)
        
        return group
    
    def _load_curve(self):
        """Load the current fan curve for this fan."""
        try:
            current_profile = self.asusctl.get_current_profile() or Profile.BALANCED
            curves = self.asusctl.get_fan_curves(current_profile)
            self.current_curve = curves.get(self.fan_name)
            
            if self.current_curve:
                self._update_curve_plot()
        except Exception as e:
            print(f"Error loading curve for {self.fan_name}: {e}")
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
        
        # Reload curve if needed (profile might have changed)
        try:
            current_profile = self.asusctl.get_current_profile() or Profile.BALANCED
            curves = self.asusctl.get_fan_curves(current_profile)
            new_curve = curves.get(self.fan_name)
            if new_curve != self.current_curve:
                self.current_curve = new_curve
                self._update_curve_plot()
        except:
            pass
        
        # Update horizontal line and intersection marker based on current fan speed
        self._update_current_position_marker()


class FanStatusTab(QWidget):
    """Tab showing visual status for CPU and GPU fans."""
    
    def __init__(self, monitor: SystemMonitor, asusctl: AsusctlInterface, parent=None):
        super().__init__(parent)
        self.monitor = monitor
        self.asusctl = asusctl
        
        self._init_ui()
        self._start_update_timer()
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Fan Status")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #333; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # CPU Fan Status
        self.cpu_fan_widget = FanStatusWidget("CPU", self.monitor, self.asusctl, self)
        layout.addWidget(self.cpu_fan_widget)
        
        # GPU Fan Status
        self.gpu_fan_widget = FanStatusWidget("GPU", self.monitor, self.asusctl, self)
        layout.addWidget(self.gpu_fan_widget)
        
        layout.addStretch()
        
        # Styling
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
        """)
    
    def _start_update_timer(self):
        """Start timer to update status periodically."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start(1000)  # Update every second
    
    def _update_status(self):
        """Update all fan status widgets."""
        self.cpu_fan_widget.update_status()
        self.gpu_fan_widget.update_status()

