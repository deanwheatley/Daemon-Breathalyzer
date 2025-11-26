#!/usr/bin/env python3
"""
Test Fans Tab

Allows manual control of fans with per-fan test mode switches, sliders, and timers.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QSlider, QCheckBox, QPushButton, QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Dict, Optional
import time
import subprocess
import re
import glob
import os

from ..control.asusctl_interface import AsusctlInterface, Profile, FanCurve, FanCurvePoint
from ..monitoring.system_monitor import SystemMonitor
from .game_style_theme import GAME_COLORS, GAME_STYLES


class FanTestTile(QGroupBox):
    """Tile for testing a single fan."""
    
    test_mode_changed = pyqtSignal(str, bool)  # fan_name, enabled
    timer_expired = pyqtSignal(str)  # fan_name
    
    def __init__(self, fan_name: str, monitor: SystemMonitor, asusctl: AsusctlInterface, parent=None):
        super().__init__(parent)
        self.fan_name = fan_name.upper()
        self.monitor = monitor
        self.asusctl = asusctl
        self.test_mode_enabled = False
        self.original_curve: Optional[FanCurve] = None
        self.current_profile = None
        
        # Timer settings (5 minutes = 300 seconds)
        self.test_duration = 300  # 5 minutes in seconds
        self.time_remaining = 0
        
        self._init_ui()
        self._init_timers()
    
    def _init_ui(self):
        """Initialize the UI."""
        self.setTitle(f"{self.fan_name} Fan")
        # Apply game-style theme
        self.setStyleSheet(GAME_STYLES['groupbox'])
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Test Mode switch
        switch_layout = QHBoxLayout()
        self.test_mode_checkbox = QCheckBox("Test Mode")
        self.test_mode_checkbox.setStyleSheet(f"""
            QCheckBox {{
                font-weight: bold;
                font-size: 14px;
                color: {GAME_COLORS['text_primary']};
                padding: 5px;
            }}
            QCheckBox::indicator {{
                width: 40px;
                height: 20px;
                border: 2px solid {GAME_COLORS['border']};
                border-radius: 10px;
                background-color: {GAME_COLORS['bg_medium']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {GAME_COLORS['accent_green']};
            }}
        """)
        self.test_mode_checkbox.stateChanged.connect(self._on_test_mode_changed)
        switch_layout.addWidget(self.test_mode_checkbox)
        switch_layout.addStretch()
        layout.addLayout(switch_layout)
        
        # Timer display
        timer_layout = QHBoxLayout()
        timer_label = QLabel("Time Remaining:")
        timer_label.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {GAME_COLORS['text_secondary']};")
        self.timer_display = QLabel("--:--")
        self.timer_display.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {GAME_COLORS['accent_red']};")
        timer_layout.addWidget(timer_label)
        timer_layout.addWidget(self.timer_display)
        timer_layout.addStretch()
        layout.addLayout(timer_layout)
        
        # Current RPM display - make it more prominent
        rpm_layout = QHBoxLayout()
        rpm_label = QLabel("Current RPM:")
        rpm_label.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {GAME_COLORS['text_secondary']};")
        self.rpm_display = QLabel("N/A")
        self.rpm_display.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {GAME_COLORS['accent_blue']}; background-color: {GAME_COLORS['bg_medium']}; padding: 5px 10px; border-radius: 5px;")
        self.rpm_display.setMinimumWidth(100)
        self.rpm_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rpm_layout.addWidget(rpm_label)
        rpm_layout.addWidget(self.rpm_display)
        rpm_layout.addStretch()
        layout.addLayout(rpm_layout)
        
        # Fan speed slider - make it more readable
        slider_layout = QVBoxLayout()
        slider_label = QLabel("Fan Speed:")
        slider_label.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {GAME_COLORS['text_secondary']};")
        slider_layout.addWidget(slider_label)
        
        slider_row = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(0, 100)
        self.speed_slider.setValue(0)
        self.speed_slider.setEnabled(False)  # Disabled until test mode is on
        self.speed_slider.valueChanged.connect(self._on_slider_changed)
        
        self.speed_label = QLabel("0%")
        self.speed_label.setMinimumWidth(70)
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.speed_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {GAME_COLORS['accent_orange']}; background-color: {GAME_COLORS['bg_medium']}; padding: 5px 10px; border-radius: 5px;")
        
        slider_row.addWidget(self.speed_slider)
        slider_row.addWidget(self.speed_label)
        slider_layout.addLayout(slider_row)
        
        layout.addLayout(slider_layout)
        
        # Game-style styling
        border_color = GAME_COLORS['border']
        bg_card = GAME_COLORS['bg_card']
        bg_medium = GAME_COLORS['bg_medium']
        text_primary = GAME_COLORS['text_primary']
        accent_blue = GAME_COLORS['accent_blue']
        accent_cyan = GAME_COLORS['accent_cyan']
        
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 16px;
                border: 2px solid {border_color};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 20px;
                padding-bottom: 15px;
                padding-left: 15px;
                padding-right: 15px;
                background-color: {bg_card};
                color: {text_primary};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: {accent_blue};
                font-size: 16px;
            }}
            QLabel {{
                color: {text_primary};
            }}
            QSlider::groove:horizontal {{
                border: 1px solid {border_color};
                background: {bg_medium};
                height: 8px;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {accent_blue};
                border: 2px solid {accent_cyan};
                width: 20px;
                margin: -2px 0;
                border-radius: 10px;
            }}
            QSlider::handle:horizontal:disabled {{
                background: {border_color};
                border: 1px solid {border_color};
            }}
        """)
    
    def _init_timers(self):
        """Initialize countdown timer."""
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self._update_countdown)
        self.countdown_timer.setInterval(1000)  # Update every second
    
    def _on_test_mode_changed(self, state: int):
        """Handle test mode checkbox change."""
        enabled = state == Qt.CheckState.Checked.value
        
        if enabled:
            self._enable_test_mode()
        else:
            self._disable_test_mode()
        
        self.test_mode_changed.emit(self.fan_name, enabled)
    
    def _enable_test_mode(self):
        """Enable test mode for this fan."""
        self.test_mode_enabled = True
        
        # Save original curve (create a copy to avoid issues)
        try:
            self.current_profile = self.asusctl.get_current_profile() or Profile.BALANCED
            curves = self.asusctl.get_fan_curves(self.current_profile)
            original = curves.get(self.fan_name)
            # Create a copy of the curve
            if original:
                self.original_curve = FanCurve([
                    FanCurvePoint(p.temperature, p.fan_speed) 
                    for p in original.points
                ])
            else:
                self.original_curve = None
        except Exception as e:
            print(f"Error saving original curve for {self.fan_name}: {e}")
            self.original_curve = None
        
        # Enable slider
        self.speed_slider.setEnabled(True)
        
        # Start countdown timer (5 minutes)
        self.time_remaining = self.test_duration
        self.countdown_timer.start()
        self._update_countdown()
        
        # Apply initial slider value
        self._apply_fan_speed(self.speed_slider.value())
    
    def _disable_test_mode(self):
        """Disable test mode and restore original curve."""
        self.test_mode_enabled = False
        
        # Stop timer
        self.countdown_timer.stop()
        self.time_remaining = 0
        self.timer_display.setText("--:--")
        
        # Disable slider
        self.speed_slider.setEnabled(False)
        
        # Restore original curve
        self._restore_original_curve()
    
    def _expand_curve_to_8_points(self, curve: FanCurve) -> FanCurve:
        """Expand a curve to exactly 8 points as required by asusctl."""
        if not curve or not curve.points:
            # Create a default 8-point curve if no curve exists
            return FanCurve([
                FanCurvePoint(30, 30),
                FanCurvePoint(40, 40),
                FanCurvePoint(50, 50),
                FanCurvePoint(60, 60),
                FanCurvePoint(70, 70),
                FanCurvePoint(80, 80),
                FanCurvePoint(85, 85),
                FanCurvePoint(90, 90),
            ])
        
        if len(curve.points) == 8:
            return curve
        
        # Standard temperature points for 8-point curve
        target_temps = [30, 40, 50, 60, 70, 80, 85, 90]
        
        # Get speeds for each target temperature using interpolation
        expanded_points = []
        for temp in target_temps:
            speed = curve.get_fan_speed_at_temp(temp)
            expanded_points.append(FanCurvePoint(temp, speed))
        
        return FanCurve(expanded_points)
    
    def _restore_original_curve(self):
        """Restore the original fan curve."""
        if self.original_curve and self.current_profile:
            try:
                # Expand to 8 points if needed
                curve_to_restore = self._expand_curve_to_8_points(self.original_curve)
                
                success, message = self.asusctl.set_fan_curve(
                    self.current_profile,
                    self.fan_name,
                    curve_to_restore
                )
                if not success:
                    print(f"Error restoring curve for {self.fan_name}: {message}")
            except Exception as e:
                print(f"Error restoring curve for {self.fan_name}: {e}")
        
        self.original_curve = None
    
    def _on_slider_changed(self, value: int):
        """Handle slider value change."""
        self.speed_label.setText(f"{value}%")
        if self.test_mode_enabled:
            self._apply_fan_speed(value)
    
    def _apply_fan_speed(self, speed_percent: int):
        """Apply fan speed as a curve (asusctl requires 8 points)."""
        if not self.test_mode_enabled:
            return
        
        try:
            # Create a flat curve at the specified speed
            # asusctl requires exactly 8 points
            curve_points = [
                FanCurvePoint(30, speed_percent),
                FanCurvePoint(40, speed_percent),
                FanCurvePoint(50, speed_percent),
                FanCurvePoint(60, speed_percent),
                FanCurvePoint(70, speed_percent),
                FanCurvePoint(80, speed_percent),
                FanCurvePoint(85, speed_percent),
                FanCurvePoint(90, speed_percent),
            ]
            curve = FanCurve(curve_points)
            
            # Ensure fan curves are enabled
            profile = self.asusctl.get_current_profile() or Profile.BALANCED
            if not self.asusctl.get_fan_curve_enabled(profile):
                self.asusctl.enable_fan_curves(profile, True)
            
            # Apply the curve
            success, message = self.asusctl.set_fan_curve(profile, self.fan_name, curve)
            if not success:
                print(f"Error setting fan speed for {self.fan_name}: {message}")
        except Exception as e:
            print(f"Error applying fan speed for {self.fan_name}: {e}")
    
    def _update_countdown(self):
        """Update the countdown timer display."""
        if self.time_remaining > 0:
            minutes = self.time_remaining // 60
            seconds = self.time_remaining % 60
            self.timer_display.setText(f"{minutes:02d}:{seconds:02d}")
            self.time_remaining -= 1
        else:
            # Timer expired
            self.countdown_timer.stop()
            self.timer_display.setText("00:00")
            self._disable_test_mode()
            self.test_mode_checkbox.setChecked(False)
            self.timer_expired.emit(self.fan_name)
    
    def update_rpm(self, rpm: Optional[int]):
        """Update the current RPM display."""
        if rpm is not None:
            self.rpm_display.setText(f"{rpm:,} RPM")
        else:
            self.rpm_display.setText("N/A")
    
    def cleanup(self):
        """Cleanup: restore original curve if test mode is active."""
        if self.test_mode_enabled:
            self._restore_original_curve()
            self.test_mode_enabled = False
            self.countdown_timer.stop()


class TestFansTab(QWidget):
    """Tab for testing fans with manual control."""
    
    def __init__(self, monitor: SystemMonitor, asusctl: AsusctlInterface, parent=None):
        super().__init__(parent)
        self.monitor = monitor
        self.asusctl = asusctl
        self.fan_tiles: Dict[str, FanTestTile] = {}
        
        self._init_ui()
        self._start_update_timer()
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Apply game-style theme
        self.setStyleSheet(GAME_STYLES['widget'])
        
        # Title
        title = QLabel("Test Fans")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {GAME_COLORS['accent_blue']}; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Enable Test Mode for a fan to manually control its speed using the slider. "
            "Test Mode automatically disables after 5 minutes. "
            "When Test Mode is disabled, the fan returns to its configured curve."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet(f"color: {GAME_COLORS['text_secondary']}; padding: 10px; background-color: {GAME_COLORS['bg_card']}; border: 2px solid {GAME_COLORS['border']}; border-radius: 5px;")
        layout.addWidget(instructions)
        
        # Fan tiles container
        self.tiles_container = QWidget()
        self.tiles_layout = QGridLayout(self.tiles_container)
        self.tiles_layout.setSpacing(15)
        layout.addWidget(self.tiles_container)
        
        layout.addStretch()
        
        # Styling
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
        """)
        
        # Detect and create tiles for available fans
        self._detect_fans()
    
    def _detect_fans(self):
        """Detect available fans and create tiles for all fans, regardless of current RPM."""
        detected_fans = set()
        
        # Method 1: Try to get fan names from asusctl (shows all fans)
        try:
            result = subprocess.run(
                ['asusctl', 'fan-curve', '--mod-profile', 'Balanced'],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode == 0:
                # Look for fan names in output (e.g., "CPU:", "GPU:", "Fan1:")
                for line in result.stdout.split('\n'):
                    # Match common fan name patterns
                    match = re.search(r'\b(CPU|GPU|Fan\d*)\b', line, re.IGNORECASE)
                    if match:
                        fan_name = match.group(1).upper()
                        # Normalize Fan1, Fan2, etc. to just keep the number or use as-is
                        if fan_name.startswith('FAN'):
                            # Keep as Fan1, Fan2, etc.
                            detected_fans.add(fan_name.title())
                        else:
                            detected_fans.add(fan_name)
        except Exception:
            pass
        
        # Method 2: Scan hwmon directories for all fan devices (not just spinning ones)
        try:
            for fan_path in glob.glob('/sys/class/hwmon/hwmon*/fan*_input'):
                # Check if file exists (fan is present)
                if os.path.exists(fan_path):
                    fan_name = fan_path.split('/')[-1].replace('_input', '')
                    
                    # Try to get a label to determine fan type
                    label_path = fan_path.replace('_input', '_label')
                    normalized_name = None
                    if os.path.exists(label_path):
                        try:
                            with open(label_path, 'r') as lf:
                                label = lf.read().strip().lower()
                                if 'cpu' in label:
                                    normalized_name = 'CPU'
                                elif 'gpu' in label:
                                    normalized_name = 'GPU'
                        except:
                            pass
                    
                    # If no label, use the raw name but make it readable
                    if not normalized_name:
                        # Convert fan1_input to Fan1, cpu_fan to CPU, etc.
                        if 'cpu' in fan_name.lower():
                            normalized_name = 'CPU'
                        elif 'gpu' in fan_name.lower():
                            normalized_name = 'GPU'
                        else:
                            # Keep the fan name but make it title case
                            normalized_name = fan_name.replace('_', ' ').title().replace(' ', '')
                    
                    detected_fans.add(normalized_name)
        except Exception:
            pass
        
        # Method 3: Check current fan speeds (includes currently spinning fans)
        self.monitor.update_metrics()
        metrics = self.monitor.get_metrics()
        fan_speeds = metrics.get('fan_speeds', [])
        for fan_info in fan_speeds:
            fan_name = fan_info.get('name', '').upper()
            if fan_name:
                detected_fans.add(fan_name)
        
        # Ensure at least CPU and GPU are in the list (common fans)
        # Only add if we haven't found anything specific
        if not detected_fans:
            detected_fans.add('CPU')
            detected_fans.add('GPU')
        
        # Clear existing tiles layout first
        while self.tiles_layout.count():
            child = self.tiles_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Create tiles for all detected fans
        row = 0
        col = 0
        max_cols = 2  # 2 columns
        
        # Sort fans: CPU first, then GPU, then others
        sorted_fans = sorted(detected_fans, key=lambda x: (
            0 if x == 'CPU' else (1 if x == 'GPU' else 2),
            x
        ))
        
        for fan_name in sorted_fans:
            fan_name_upper = fan_name.upper()
            if fan_name_upper not in self.fan_tiles:
                tile = FanTestTile(fan_name, self.monitor, self.asusctl, self)
                tile.test_mode_changed.connect(self._on_test_mode_changed)
                tile.timer_expired.connect(self._on_timer_expired)
                self.fan_tiles[fan_name_upper] = tile
                
                self.tiles_layout.addWidget(tile, row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
        
        # If no fans detected, show message
        if not self.fan_tiles:
            no_fans_label = QLabel("No fans detected. Fans will appear here when detected.")
            no_fans_label.setStyleSheet("color: #999; font-style: italic; padding: 20px;")
            self.tiles_layout.addWidget(no_fans_label, 0, 0)
    
    def _start_update_timer(self):
        """Start timer to update fan RPM displays."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_fan_rpms)
        self.update_timer.start(2000)  # Update every 2 seconds
    
    def _update_fan_rpms(self):
        """Update RPM displays for all fan tiles."""
        self.monitor.update_metrics()
        metrics = self.monitor.get_metrics()
        fan_speeds = metrics.get('fan_speeds', [])
        
        # Create a mapping of normalized names to RPM values
        rpm_map = {}
        for fan_info in fan_speeds:
            fan_name = fan_info.get('name', '').upper()
            rpm = fan_info.get('rpm', 0)
            if rpm > 0:  # Only map non-zero RPMs
                rpm_map[fan_name] = rpm
        
        # Update existing tiles with RPM (or None if not spinning)
        for fan_name in self.fan_tiles:
            rpm = rpm_map.get(fan_name)
            self.fan_tiles[fan_name].update_rpm(rpm)
    
    def _on_test_mode_changed(self, fan_name: str, enabled: bool):
        """Handle test mode change for a fan."""
        # Could add global state tracking here if needed
        pass
    
    def _on_timer_expired(self, fan_name: str):
        """Handle timer expiration for a fan."""
        # Timer already disabled the test mode in the tile
        # Could show a notification here if desired
        pass
    
    def cleanup(self):
        """Cleanup: restore all fan curves before closing."""
        for tile in self.fan_tiles.values():
            tile.cleanup()
    
    def closeEvent(self, event):
        """Handle close event - restore curves."""
        self.cleanup()
        super().closeEvent(event)

