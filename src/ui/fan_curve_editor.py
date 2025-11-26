#!/usr/bin/env python3
"""
Fan Curve Designer Widget

Interactive fan curve designer focused on designing, loading, and saving curves.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QButtonGroup, QMessageBox, QSpinBox, QFormLayout, QGroupBox,
    QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF, QTimer
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QColor, QMouseEvent
import pyqtgraph as pg
import numpy as np

from ..control.asusctl_interface import FanCurve, FanCurvePoint, Profile, AsusctlInterface
from ..control.profile_manager import ProfileManager, SavedProfile
from .game_style_theme import GAME_COLORS, GAME_STYLES


class DraggablePoint(pg.ScatterPlotItem):
    """A draggable point on the fan curve."""
    
    def __init__(self, x, y, parent_editor):
        super().__init__([x], [y], 
                        pen=pg.mkPen(color='#2196F3', width=2),
                        brush=pg.mkBrush(color='white'),
                        size=12,
                        hoverable=True,
                        hoverPen=pg.mkPen(color='#2196F3', width=3))
        self.parent_editor = parent_editor
        self.original_temp = x
        self.original_speed = y
        self.setAcceptHoverEvents(True)
    
    def set_selected(self, selected):
        """Update selection state."""
        from .game_style_theme import GAME_COLORS
        if selected:
            self.setBrush(pg.mkBrush(color=GAME_COLORS['accent_blue']))
            self.setPen(pg.mkPen(color=GAME_COLORS['accent_blue'], width=2))
        else:
            self.setBrush(pg.mkBrush(color=GAME_COLORS['bg_card']))
            self.setPen(pg.mkPen(color=GAME_COLORS['accent_blue'], width=2))


class FanCurveEditor(QWidget):
    """Interactive fan curve designer widget - focused on designing, loading, and saving curves."""
    
    curve_changed = pyqtSignal(FanCurve)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_curve = None
        self.original_curve = None
        self.current_loaded_profile_name = None  # Track which profile is currently loaded
        self.control_points = []
        self.selected_point_temp = None  # Track by temperature, not index
        self.temp_range = (30, 90)  # Temperature range in Celsius
        self.speed_range = (0, 100)  # Fan speed range in %
        self.asusctl = AsusctlInterface()
        self.profile_manager = ProfileManager()
        
        self.setup_ui()
        self.refresh_profile_dropdown()
        
    def setup_ui(self):
        """Set up the UI."""
        # Apply game-style theme
        self.setStyleSheet(GAME_STYLES['widget'])
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title and fan selector
        header_layout = QHBoxLayout()
        
        title = QLabel("Fan Curve Designer")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {GAME_COLORS['accent_blue']}; margin-bottom: 5px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Preset curves dropdown
        preset_label = QLabel("Preset:")
        preset_label.setStyleSheet("color: #666; margin-right: 8px;")
        header_layout.addWidget(preset_label)
        
        self.preset_dropdown = QComboBox()
        self.preset_dropdown.setMinimumWidth(150)
        self.preset_dropdown.setStyleSheet(GAME_STYLES['combobox'])
        self.preset_dropdown.addItems(["Balanced", "Loudmouth", "Shush"])
        self.preset_dropdown.setCurrentText("Balanced")  # Default
        self.preset_dropdown.currentTextChanged.connect(self.on_preset_changed)
        header_layout.addWidget(self.preset_dropdown)
        
        header_layout.addSpacing(20)
        
        # Saved profiles dropdown
        profile_label = QLabel("Saved Profile:")
        profile_label.setStyleSheet("color: #666; margin-right: 8px;")
        header_layout.addWidget(profile_label)
        
        self.profile_dropdown = QComboBox()
        self.profile_dropdown.setMinimumWidth(180)
        self.profile_dropdown.setStyleSheet(GAME_STYLES['combobox'])
        self.profile_dropdown.addItem("-- Select Profile --")
        self.profile_dropdown.currentTextChanged.connect(self.on_profile_dropdown_changed)
        header_layout.addWidget(self.profile_dropdown)
        
        header_layout.addSpacing(20)
        
        # Fan selector buttons
        self.fan_button_group = QButtonGroup(self)
        self.cpu_fan_btn = QPushButton("CPU Fan")
        self.gpu_fan_btn = QPushButton("GPU Fan")
        
        for btn in [self.cpu_fan_btn, self.gpu_fan_btn]:
            btn.setCheckable(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {GAME_COLORS['bg_card']};
                    color: {GAME_COLORS['text_primary']};
                    border: 2px solid {GAME_COLORS['border']};
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    border: 2px solid {GAME_COLORS['accent_blue']};
                }}
                QPushButton:checked {{
                    background-color: {GAME_COLORS['accent_blue']};
                    color: {GAME_COLORS['text_primary']};
                    border: 2px solid {GAME_COLORS['accent_blue']};
                    box-shadow: 0 0 15px {GAME_COLORS['accent_blue']};
                }}
            """)
            self.fan_button_group.addButton(btn)
        
        self.cpu_fan_btn.setChecked(True)
        header_layout.addWidget(self.cpu_fan_btn)
        header_layout.addWidget(self.gpu_fan_btn)
        
        layout.addLayout(header_layout)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Graph area
        graph_container = QWidget()
        graph_layout = QVBoxLayout(graph_container)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create PyQtGraph widget with game-style theme
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground(pg.mkColor(GAME_COLORS['bg_card']))
        self.graph_widget.setLabel('left', 'Fan Speed (%)', **{'color': GAME_COLORS['text_secondary'], 'font-size': '11pt'})
        self.graph_widget.setLabel('bottom', 'Temperature (°C)', **{'color': GAME_COLORS['text_secondary'], 'font-size': '11pt'})
        self.graph_widget.setXRange(self.temp_range[0], self.temp_range[1])
        self.graph_widget.setYRange(self.speed_range[0], self.speed_range[1])
        self.graph_widget.showGrid(x=True, y=True, alpha=0.1)
        self.graph_widget.getAxis('left').setPen(pg.mkPen(color=GAME_COLORS['border'], width=1))
        self.graph_widget.getAxis('bottom').setPen(pg.mkPen(color=GAME_COLORS['border'], width=1))
        self.graph_widget.getAxis('left').setTextPen(pg.mkPen(color=GAME_COLORS['text_secondary']))
        self.graph_widget.getAxis('bottom').setTextPen(pg.mkPen(color=GAME_COLORS['text_secondary']))
        
        # Plot item for the curve with game-style color
        self.curve_plot = self.graph_widget.plot([], [], pen=pg.mkPen(color=GAME_COLORS['accent_blue'], width=3))
        
        # Scene for interactive points
        self.plot_item = self.graph_widget.getPlotItem()
        
        graph_layout.addWidget(self.graph_widget)
        graph_container.setStyleSheet(f"""
            QWidget {{
                background-color: {GAME_COLORS['bg_card']};
                border: 2px solid {GAME_COLORS['border']};
                border-radius: 12px;
            }}
        """)
        graph_layout.setContentsMargins(15, 15, 15, 15)
        
        content_layout.addWidget(graph_container, 2)
        
        # Control panel
        control_panel = self.create_control_panel()
        content_layout.addWidget(control_panel, 1)
        
        layout.addLayout(content_layout)
        
        # Action buttons - organized into groups for better UX
        button_layout = QVBoxLayout()
        button_layout.setSpacing(15)
        
        # Load section
        load_section = QGroupBox("Load")
        load_section.setStyleSheet(GAME_STYLES['groupbox'])
        load_layout = QVBoxLayout(load_section)
        load_layout.setSpacing(8)
        
        load_presets_layout = QHBoxLayout()
        load_presets_layout.setSpacing(8)
        self.preset_quiet_btn = QPushButton("Quiet")
        self.preset_balanced_btn = QPushButton("Balanced")
        self.preset_performance_btn = QPushButton("Performance")
        
        preset_buttons = [self.preset_quiet_btn, self.preset_balanced_btn, self.preset_performance_btn]
        for btn in preset_buttons:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {GAME_COLORS['bg_card']};
                    color: {GAME_COLORS['text_primary']};
                    border: 2px solid {GAME_COLORS['border']};
                    padding: 8px 12px;
                    border-radius: 6px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    border: 2px solid {GAME_COLORS['accent_blue']};
                    background-color: {GAME_COLORS['bg_medium']};
                }}
            """)
        
        self.preset_balanced_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {GAME_COLORS['accent_green']};
                color: {GAME_COLORS['text_primary']};
                border: 2px solid {GAME_COLORS['accent_green']};
                padding: 8px 12px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                box-shadow: 0 0 15px {GAME_COLORS['accent_green']};
            }}
        """)
        
        load_presets_layout.addWidget(self.preset_quiet_btn)
        load_presets_layout.addWidget(self.preset_balanced_btn)
        load_presets_layout.addWidget(self.preset_performance_btn)
        load_layout.addLayout(load_presets_layout)
        
        self.reset_btn = QPushButton("↺ Reset to Original")
        self.reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {GAME_COLORS['bg_card']};
                color: {GAME_COLORS['text_secondary']};
                border: 2px solid {GAME_COLORS['border']};
                padding: 8px 12px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border: 2px solid {GAME_COLORS['accent_blue']};
            }}
        """)
        load_layout.addWidget(self.reset_btn)
        
        button_layout.addWidget(load_section)
        
        # Save section
        save_section = QGroupBox("Save")
        save_section.setStyleSheet(GAME_STYLES['groupbox'])
        save_layout = QVBoxLayout(save_section)
        save_layout.setSpacing(8)
        
        self.save_profile_btn = QPushButton("💾 Save Curve")
        self.save_profile_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {GAME_COLORS['accent_green']};
                color: {GAME_COLORS['text_primary']};
                border: 2px solid {GAME_COLORS['accent_green']};
                padding: 10px 16px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12pt;
            }}
            QPushButton:hover {{
                box-shadow: 0 0 20px {GAME_COLORS['accent_green']};
            }}
        """)
        save_layout.addWidget(self.save_profile_btn)
        
        self.save_as_btn = QPushButton("💾 Save As...")
        self.save_as_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {GAME_COLORS['bg_card']};
                color: {GAME_COLORS['text_primary']};
                border: 2px solid {GAME_COLORS['border']};
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border: 2px solid {GAME_COLORS['accent_blue']};
            }}
        """)
        save_layout.addWidget(self.save_as_btn)
        
        button_layout.addWidget(save_section)
        
        # Connect signals
        self.preset_quiet_btn.clicked.connect(lambda: self.load_preset('quiet'))
        self.preset_balanced_btn.clicked.connect(lambda: self.load_preset('balanced'))
        self.preset_performance_btn.clicked.connect(lambda: self.load_preset('performance'))
        self.reset_btn.clicked.connect(self.reset_curve)
        self.save_profile_btn.clicked.connect(self.save_current_profile)
        self.save_as_btn.clicked.connect(self.save_as_profile)
        
        layout.addLayout(button_layout)
        
        # Set up initial curve - load Balanced preset
        self.load_preset('balanced')
        self.preset_dropdown.blockSignals(True)
        self.preset_dropdown.setCurrentText("Balanced")
        self.preset_dropdown.blockSignals(False)
        
    def create_control_panel(self) -> QWidget:
        """Create the control panel widget."""
        panel = QGroupBox("Controls")
        panel.setStyleSheet(GAME_STYLES['groupbox'])
        layout = QVBoxLayout(panel)
        
        # Add point controls
        form_layout = QFormLayout()
        
        self.temp_input = QSpinBox()
        self.temp_input.setRange(self.temp_range[0], self.temp_range[1])
        self.temp_input.setValue(50)
        self.temp_input.setStyleSheet(GAME_STYLES['spinbox'])
        temp_label = QLabel("Temperature (°C):")
        temp_label.setStyleSheet(f"color: {GAME_COLORS['text_primary']};")
        form_layout.addRow(temp_label, self.temp_input)
        
        self.speed_input = QSpinBox()
        self.speed_input.setRange(self.speed_range[0], self.speed_range[1])
        self.speed_input.setValue(50)
        self.speed_input.setStyleSheet(GAME_STYLES['spinbox'])
        speed_label = QLabel("Fan Speed (%):")
        speed_label.setStyleSheet(f"color: {GAME_COLORS['text_primary']};")
        form_layout.addRow(speed_label, self.speed_input)
        
        layout.addLayout(form_layout)
        
        add_point_btn = QPushButton("Add Point")
        add_point_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {GAME_COLORS['accent_green']};
                color: {GAME_COLORS['text_primary']};
                border: 2px solid {GAME_COLORS['accent_green']};
                padding: 8px;
                border-radius: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                box-shadow: 0 0 15px {GAME_COLORS['accent_green']};
            }}
        """)
        add_point_btn.clicked.connect(self.add_point_from_inputs)
        layout.addWidget(add_point_btn)
        
        remove_point_btn = QPushButton("Remove Selected")
        remove_point_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #F44336;
                color: white;
                padding: 8px;
                border-radius: 6px;
            }}
        """)
        remove_point_btn.clicked.connect(self.remove_selected_point)
        layout.addWidget(remove_point_btn)
        
        # Update point button
        update_point_btn = QPushButton("Update Selected")
        update_point_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                border-radius: 6px;
            }
        """)
        update_point_btn.clicked.connect(self.update_point_from_inputs)
        layout.addWidget(update_point_btn)
        
        layout.addStretch()
        
        return panel
    
    def update_point_from_inputs(self):
        """Update the selected point from input fields."""
        if self.selected_point_temp is None:
            QMessageBox.information(self, "No Selection", "Please select a point to update.")
            return
        
        temp = self.temp_input.value()
        speed = self.speed_input.value()
        
        if self.current_curve:
            try:
                # Remove old point by temperature
                self.current_curve.remove_point(self.selected_point_temp)
                
                # Add new point
                self.current_curve.add_point(temp, speed)
                
                self.selected_point_temp = None
                self.update_display()
            except (IndexError, ValueError) as e:
                QMessageBox.warning(self, "Invalid Curve", str(e))
    
    def load_curve(self, curve: FanCurve, profile_name: str = None):
        """Load a fan curve into the editor."""
        self.original_curve = curve
        self.current_curve = FanCurve([FanCurvePoint(p.temperature, p.fan_speed) for p in curve.points])
        self.current_loaded_profile_name = profile_name  # Track loaded profile
        # Clear profile dropdown selection when loading manually (only if not blocked)
        if hasattr(self, 'profile_dropdown') and not self.profile_dropdown.signalsBlocked():
            self.profile_dropdown.setCurrentIndex(0)
        # Clear preset dropdown when loading from profile
        if hasattr(self, 'preset_dropdown') and not self.preset_dropdown.signalsBlocked():
            self.preset_dropdown.setCurrentIndex(-1)
        self.update_display()
    
    def load_preset(self, preset_name: str):
        """Load a preset curve."""
        from ..control.asusctl_interface import get_preset_curve
        preset = get_preset_curve(preset_name)
        self.load_curve(preset)
    
    def on_preset_changed(self, preset_name: str):
        """Handle preset dropdown change."""
        if preset_name:
            # Map display names to preset keys
            preset_map = {
                "Balanced": "balanced",
                "Loudmouth": "loudmouth",
                "Shush": "shush"
            }
            preset_key = preset_map.get(preset_name, preset_name.lower())
            self.load_preset(preset_key)
            
            # Clear profile dropdown when preset is selected
            if hasattr(self, 'profile_dropdown'):
                self.profile_dropdown.blockSignals(True)
                self.profile_dropdown.setCurrentIndex(0)
                self.profile_dropdown.blockSignals(False)
    
    def refresh_profile_dropdown(self):
        """Refresh the profile dropdown with saved profiles."""
        if not hasattr(self, 'profile_dropdown'):
            return
        
        current_selection = self.profile_dropdown.currentText()
        self.profile_dropdown.clear()
        self.profile_dropdown.addItem("-- Select Profile --")
        
        # Load all profiles
        self.profile_manager.load_all_profiles()
        profiles = self.profile_manager.list_profiles()
        for profile_name in profiles:
            self.profile_dropdown.addItem(profile_name)
        
        # Restore selection if it still exists
        if current_selection and current_selection != "-- Select Profile --":
            index = self.profile_dropdown.findText(current_selection)
            if index >= 0:
                self.profile_dropdown.setCurrentIndex(index)
    
    def on_profile_dropdown_changed(self, profile_name: str):
        """Handle profile selection from dropdown."""
        if profile_name == "-- Select Profile --" or not profile_name:
            self.current_loaded_profile_name = None
            return
        
        profile = self.profile_manager.get_profile(profile_name)
        if not profile:
            return
        
        # Load the appropriate curve based on selected fan
        fan_name = self.get_current_fan_name()
        curve_to_load = None
        if fan_name == "CPU" and profile.cpu_fan_curve:
            curve_to_load = profile.cpu_fan_curve
        elif fan_name == "GPU" and profile.gpu_fan_curve:
            curve_to_load = profile.gpu_fan_curve
        elif profile.cpu_fan_curve:
            # Fallback to CPU curve if GPU not available
            curve_to_load = profile.cpu_fan_curve
        
        if curve_to_load:
            # Temporarily disconnect to avoid clearing dropdown
            self.profile_dropdown.blockSignals(True)
            self.load_curve(curve_to_load, profile_name)  # Pass profile name to track it
            self.profile_dropdown.blockSignals(False)
    
    def reset_curve(self):
        """Reset to original curve."""
        if self.original_curve:
            self.load_curve(self.original_curve, self.current_loaded_profile_name)
    
    def _is_curve_currently_active(self, curve: FanCurve, fan_name: str):
        """
        Check if a curve is currently active (applied) for a fan.
        
        Returns:
            Tuple of (is_active: bool, profile_name: str or None)
        """
        from ..control.fan_curve_persistence import FanCurvePersistence
        persistence = FanCurvePersistence()
        
        # Check all profiles for active curves
        all_active_curves = persistence.get_all_active_curves()
        
        for profile_key, curves in all_active_curves.items():
            active_curve = curves.get(fan_name)
            if active_curve and self._curves_match(active_curve, curve):
                # Convert profile key to readable name
                profile_name = profile_key.capitalize()
                return True, profile_name
        
        return False, None
    
    def _curves_match(self, curve1: FanCurve, curve2: FanCurve) -> bool:
        """Check if two curves match (same points)."""
        if not curve1 or not curve2:
            return False
        if len(curve1.points) != len(curve2.points):
            return False
        
        # Sort both curves by temperature for comparison
        points1 = sorted(curve1.points, key=lambda p: p.temperature)
        points2 = sorted(curve2.points, key=lambda p: p.temperature)
        
        for p1, p2 in zip(points1, points2):
            if p1.temperature != p2.temperature or p1.fan_speed != p2.fan_speed:
                return False
        
        return True
    
    def save_as_profile(self):
        """Save the current curve with a new name (Save As functionality)."""
        if not self.current_curve:
            QMessageBox.warning(
                self,
                "No Curve",
                "Please configure a fan curve first."
            )
            return
        
        # Import ProfileDialog
        from .profile_manager_tab import ProfileDialog
        from PyQt6.QtWidgets import QDialog
        
        dialog = ProfileDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.get_name()
            if not name:
                QMessageBox.warning(self, "Invalid Name", "Profile name cannot be empty.")
                return
            
            # Save the profile
            self._do_save_profile(name, dialog.get_description(), is_save_as=True)
    
    def save_current_profile(self):
        """Save the current curve to the loaded profile, or prompt for Save As if active."""
        if not self.current_curve:
            QMessageBox.warning(
                self,
                "No Curve",
                "Please configure a fan curve first."
            )
            return
        
        fan_name = self.get_current_fan_name()
        
        # Check if current curve matches an active curve
        is_active, active_profile = self._is_curve_currently_active(self.current_curve, fan_name)
        
        if is_active:
            # Curve is currently active - prompt for Save As or discard
            reply = QMessageBox.question(
                self,
                "Curve Currently in Use",
                f"This curve is currently applied to {fan_name} fan on {active_profile} profile.\n\n"
                "To modify it, you need to save it with a different name.\n\n"
                "Would you like to 'Save As' a new name, or discard your changes?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Save:
                # Save As
                self.save_as_profile()
                return
            elif reply == QMessageBox.StandardButton.Discard:
                # Reset to original
                self.reset_curve()
                return
            else:
                # Cancel
                return
        
        # If we have a loaded profile name, try to save to it
        if self.current_loaded_profile_name:
            # Check if the loaded profile curve is active
            profile = self.profile_manager.get_profile(self.current_loaded_profile_name)
            if profile:
                profile_curve = profile.cpu_fan_curve if fan_name == "CPU" else profile.gpu_fan_curve
                if profile_curve:
                    is_active, active_profile = self._is_curve_currently_active(profile_curve, fan_name)
                    if is_active:
                        # Cannot save over active curve
                        reply = QMessageBox.question(
                            self,
                            "Cannot Overwrite Active Curve",
                            f"The profile '{self.current_loaded_profile_name}' contains a curve that is currently applied.\n\n"
                            "Would you like to 'Save As' a new name?",
                            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel,
                            QMessageBox.StandardButton.Save
                        )
                        
                        if reply == QMessageBox.StandardButton.Save:
                            self.save_as_profile()
                        return
            
            # Save to loaded profile
            self._do_save_profile(
                self.current_loaded_profile_name, 
                profile.description if profile else "",
                is_save_as=False
            )
        else:
            # No loaded profile - prompt for Save As
            self.save_as_profile()
    
    def _do_save_profile(self, name: str, description: str, is_save_as: bool = False):
        """Internal method to save a profile."""
        if not self.current_curve:
            return
        
        # Check if profile exists (unless it's Save As with a new name)
        if name in self.profile_manager.list_profiles() and not is_save_as:
            reply = QMessageBox.question(
                self,
                "Overwrite?",
                f"Profile '{name}' already exists. Overwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # Get curves for current fan
        fan_name = self.get_current_fan_name()
        cpu_curve = self.current_curve if fan_name == "CPU" else None
        gpu_curve = self.current_curve if fan_name == "GPU" else None
        
        # If saving for one fan, try to preserve the other fan's curve from existing profile
        existing_profile = self.profile_manager.get_profile(name)
        if existing_profile:
            if fan_name == "CPU" and existing_profile.gpu_fan_curve:
                gpu_curve = existing_profile.gpu_fan_curve
            elif fan_name == "GPU" and existing_profile.cpu_fan_curve:
                cpu_curve = existing_profile.cpu_fan_curve
        
        profile = SavedProfile(
            name=name,
            description=description,
            cpu_fan_curve=cpu_curve,
            gpu_fan_curve=gpu_curve
        )
        
        if self.profile_manager.save_profile(profile):
            self.current_loaded_profile_name = name  # Update loaded profile name
            QMessageBox.information(self, "Saved", f"Profile '{name}' saved successfully!")
            self.refresh_profile_dropdown()
            # Select the newly saved profile in dropdown
            index = self.profile_dropdown.findText(name)
            if index >= 0:
                self.profile_dropdown.blockSignals(True)
                self.profile_dropdown.setCurrentIndex(index)
                self.profile_dropdown.blockSignals(False)
        else:
            QMessageBox.warning(self, "Error", "Failed to save profile.")
    
    def update_display(self):
        """Update the graph display."""
        if not self.current_curve or not self.current_curve.points:
            return
        
        # Clear existing points
        for item in self.control_points:
            if isinstance(item, tuple) and len(item) >= 2:
                scatter = item[0]
                self.plot_item.removeItem(scatter)
        self.control_points.clear()
        self.selected_point_temp = None
        
        # Plot the curve
        temps = [p.temperature for p in self.current_curve.points]
        speeds = [p.fan_speed for p in self.current_curve.points]
        
        # Create smooth curve for display
        if len(temps) >= 2:
            smooth_temps = np.linspace(min(temps), max(temps), 200)
            smooth_speeds = [self.current_curve.get_fan_speed_at_temp(int(t)) for t in smooth_temps]
            self.curve_plot.setData(smooth_temps, smooth_speeds)
        else:
            self.curve_plot.setData(temps, speeds)
        
        # Add control points using scatter plot with game-style colors
        for i, point in enumerate(self.current_curve.points):
            scatter = pg.ScatterPlotItem(
                [point.temperature], [point.fan_speed],
                pen=pg.mkPen(color=GAME_COLORS['accent_blue'], width=2),
                brush=pg.mkBrush(color=GAME_COLORS['bg_card']),
                size=12,
                symbol='o',
                hoverable=True,
                hoverPen=pg.mkPen(color=GAME_COLORS['accent_cyan'], width=3)
            )
            # Create a closure to capture the index correctly
            def make_click_handler(idx):
                def handler(item, points, ev):
                    self.on_point_clicked(idx)
                return handler
            
            scatter.sigClicked.connect(make_click_handler(i))
            self.plot_item.addItem(scatter)
            self.control_points.append((scatter, point, i))
    
    def on_point_clicked(self, index):
        """Handle point click."""
        if self.control_points and index < len(self.control_points):
            scatter, point, idx = self.control_points[index]
            self.temp_input.setValue(point.temperature)
            self.speed_input.setValue(point.fan_speed)
            self.selected_point_temp = point.temperature  # Track by temperature
    
    def add_point_from_inputs(self):
        """Add or update a point from the input fields."""
        temp = self.temp_input.value()
        speed = self.speed_input.value()
        
        if self.current_curve:
            try:
                # If a point is selected and has the same temperature, update it
                if self.selected_point_temp is not None and self.selected_point_temp == temp:
                    # Update existing point (remove will happen in add_point)
                    self.current_curve.add_point(temp, speed)
                    self.selected_point_temp = None
                else:
                    # Add new point (or update if same temp)
                    self.current_curve.add_point(temp, speed)
                    self.selected_point_temp = None
                
                self.update_display()
            except ValueError as e:
                QMessageBox.warning(self, "Invalid Curve", str(e))
    
    def remove_selected_point(self):
        """Remove the selected point."""
        if self.selected_point_temp is not None and self.current_curve:
            try:
                # Remove point by temperature
                self.current_curve.remove_point(self.selected_point_temp)
                self.selected_point_temp = None
                self.update_display()
            except (IndexError, ValueError) as e:
                QMessageBox.warning(self, "Cannot Remove Point", str(e))
        else:
            QMessageBox.information(self, "No Selection", "Please select a point to remove.")
    
    def get_current_fan_name(self) -> str:
        """Get the currently selected fan name."""
        if self.cpu_fan_btn.isChecked():
            return "CPU"
        elif self.gpu_fan_btn.isChecked():
            return "GPU"
        return "CPU"
