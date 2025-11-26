#!/usr/bin/env python3
"""
Fan Curve Editor Widget

Interactive fan curve editor with draggable control points.
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
    """Interactive fan curve editor widget."""
    
    curve_changed = pyqtSignal(FanCurve)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_curve = None
        self.original_curve = None
        self.control_points = []
        self.selected_point_temp = None  # Track by temperature, not index
        self.temp_range = (30, 90)  # Temperature range in Celsius
        self.speed_range = (0, 100)  # Fan speed range in %
        self.asusctl = AsusctlInterface()
        self.profile_manager = ProfileManager()
        self.test_restore_timer = None
        self.test_countdown_timer = None
        self.test_seconds_remaining = 0
        self.original_curve_before_test = None
        
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
        
        title = QLabel("Fan Curve Editor")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setWeight(QFont.Weight.DemiBold)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {GAME_COLORS['accent_blue']};")
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
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.preset_silent_btn = QPushButton("Silent")
        self.preset_quiet_btn = QPushButton("Quiet")
        self.preset_balanced_btn = QPushButton("Balanced")
        self.preset_conservative_btn = QPushButton("Conservative")
        self.preset_performance_btn = QPushButton("Performance")
        self.preset_max_btn = QPushButton("Max Fan")
        self.reset_btn = QPushButton("Reset")
        self.apply_btn = QPushButton("Apply")
        
        preset_buttons = [
            self.preset_silent_btn, self.preset_quiet_btn, self.preset_balanced_btn,
            self.preset_conservative_btn, self.preset_performance_btn, self.preset_max_btn,
            self.reset_btn, self.apply_btn
        ]
        
        # Apply game-style theme to buttons
        for btn in preset_buttons:
            btn.setStyleSheet(GAME_STYLES['button'])
        
        # Custom colors for preset buttons
        self.preset_silent_btn.setStyleSheet(f"QPushButton {{ background-color: {GAME_COLORS['bg_card']}; color: {GAME_COLORS['text_secondary']}; border: 2px solid {GAME_COLORS['border']}; padding: 8px 16px; border-radius: 8px; font-weight: bold; }} QPushButton:hover {{ border: 2px solid {GAME_COLORS['accent_blue']}; }}")
        self.preset_quiet_btn.setStyleSheet(f"QPushButton {{ background-color: {GAME_COLORS['bg_card']}; color: {GAME_COLORS['text_secondary']}; border: 2px solid {GAME_COLORS['border']}; padding: 8px 16px; border-radius: 8px; font-weight: bold; }} QPushButton:hover {{ border: 2px solid {GAME_COLORS['accent_blue']}; }}")
        self.preset_balanced_btn.setStyleSheet(f"QPushButton {{ background-color: {GAME_COLORS['accent_green']}; color: {GAME_COLORS['text_primary']}; border: 2px solid {GAME_COLORS['accent_green']}; padding: 8px 16px; border-radius: 8px; font-weight: bold; }} QPushButton:hover {{ box-shadow: 0 0 15px {GAME_COLORS['accent_green']}; }}")
        self.preset_conservative_btn.setStyleSheet(f"QPushButton {{ background-color: {GAME_COLORS['accent_orange']}; color: {GAME_COLORS['text_primary']}; border: 2px solid {GAME_COLORS['accent_orange']}; padding: 8px 16px; border-radius: 8px; font-weight: bold; }} QPushButton:hover {{ box-shadow: 0 0 15px {GAME_COLORS['accent_orange']}; }}")
        self.preset_performance_btn.setStyleSheet(f"QPushButton {{ background-color: {GAME_COLORS['accent_red']}; color: {GAME_COLORS['text_primary']}; border: 2px solid {GAME_COLORS['accent_red']}; padding: 8px 16px; border-radius: 8px; font-weight: bold; }} QPushButton:hover {{ box-shadow: 0 0 15px {GAME_COLORS['accent_red']}; }}")
        self.preset_max_btn.setStyleSheet(f"QPushButton {{ background-color: {GAME_COLORS['accent_purple']}; color: {GAME_COLORS['text_primary']}; border: 2px solid {GAME_COLORS['accent_purple']}; padding: 8px 16px; border-radius: 8px; font-weight: bold; }} QPushButton:hover {{ box-shadow: 0 0 15px {GAME_COLORS['accent_purple']}; }}")
        self.reset_btn.setStyleSheet(f"QPushButton {{ background-color: {GAME_COLORS['bg_card']}; color: {GAME_COLORS['text_secondary']}; border: 2px solid {GAME_COLORS['border']}; padding: 8px 16px; border-radius: 8px; font-weight: bold; }} QPushButton:hover {{ border: 2px solid {GAME_COLORS['accent_blue']}; }}")
        self.apply_btn.setStyleSheet(f"QPushButton {{ background-color: {GAME_COLORS['accent_blue']}; color: {GAME_COLORS['text_primary']}; border: 2px solid {GAME_COLORS['accent_blue']}; padding: 8px 16px; border-radius: 8px; font-weight: bold; }} QPushButton:hover {{ box-shadow: 0 0 15px {GAME_COLORS['accent_blue']}; }}")
        
        button_layout.addWidget(self.preset_silent_btn)
        button_layout.addWidget(self.preset_quiet_btn)
        button_layout.addWidget(self.preset_balanced_btn)
        button_layout.addWidget(self.preset_conservative_btn)
        button_layout.addWidget(self.preset_performance_btn)
        button_layout.addWidget(self.preset_max_btn)
        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.apply_btn)
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.preset_silent_btn.clicked.connect(lambda: self.load_preset('silent'))
        self.preset_quiet_btn.clicked.connect(lambda: self.load_preset('quiet'))
        self.preset_balanced_btn.clicked.connect(lambda: self.load_preset('balanced'))
        self.preset_conservative_btn.clicked.connect(lambda: self.load_preset('conservative'))
        self.preset_performance_btn.clicked.connect(lambda: self.load_preset('performance'))
        self.preset_max_btn.clicked.connect(lambda: self.load_preset('max'))
        self.reset_btn.clicked.connect(self.reset_curve)
        self.apply_btn.clicked.connect(self.apply_curve)
        
        # Save Profile button
        self.save_profile_btn = QPushButton("💾 Save Profile")
        self.save_profile_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                border-radius: 6px;
                border: none;
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.save_profile_btn.clicked.connect(self.save_current_profile)
        button_layout.addWidget(self.save_profile_btn)
        
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
        remove_point_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                padding: 8px;
                border-radius: 6px;
            }
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
        
        # Test Fan button
        self.test_fan_btn = QPushButton("Test Fan (100% for 5s)")
        self.test_fan_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
        """)
        self.test_fan_btn.clicked.connect(self.test_fan)
        layout.addWidget(self.test_fan_btn)
        
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
    
    def load_curve(self, curve: FanCurve):
        """Load a fan curve into the editor."""
        self.original_curve = curve
        self.current_curve = FanCurve([FanCurvePoint(p.temperature, p.fan_speed) for p in curve.points])
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
            return
        
        profile = self.profile_manager.get_profile(profile_name)
        if not profile:
            return
        
        # Load the appropriate curve based on selected fan
        fan_name = self.get_current_fan_name()
        if fan_name == "CPU" and profile.cpu_fan_curve:
            # Temporarily disconnect to avoid clearing dropdown
            self.profile_dropdown.blockSignals(True)
            self.load_curve(profile.cpu_fan_curve)
            self.profile_dropdown.blockSignals(False)
        elif fan_name == "GPU" and profile.gpu_fan_curve:
            self.profile_dropdown.blockSignals(True)
            self.load_curve(profile.gpu_fan_curve)
            self.profile_dropdown.blockSignals(False)
        elif profile.cpu_fan_curve:
            # Fallback to CPU curve if GPU not available
            self.profile_dropdown.blockSignals(True)
            self.load_curve(profile.cpu_fan_curve)
            self.profile_dropdown.blockSignals(False)
    
    def save_current_profile(self):
        """Save the current fan curves as a profile."""
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
            
            # Check if profile exists
            if name in self.profile_manager.list_profiles():
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
                description=dialog.get_description(),
                cpu_fan_curve=cpu_curve,
                gpu_fan_curve=gpu_curve
            )
            
            if self.profile_manager.save_profile(profile):
                QMessageBox.information(self, "Saved", f"Profile '{name}' saved successfully!")
                self.refresh_profile_dropdown()
                # Select the newly saved profile in dropdown
                index = self.profile_dropdown.findText(name)
                if index >= 0:
                    self.profile_dropdown.setCurrentIndex(index)
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
    
    def reset_curve(self):
        """Reset to original curve."""
        if self.original_curve:
            self.load_curve(self.original_curve)
    
    def apply_curve(self):
        """Apply the current curve and save it."""
        if not self.current_curve:
            QMessageBox.warning(self, "No Curve", "Please configure a fan curve first.")
            return
        
        # Get current profile and fan
        from ..control.asusctl_interface import Profile
        current_profile = self.asusctl.get_current_profile() or Profile.BALANCED
        fan_name = self.get_current_fan_name()
        
        # Ensure fan curves are enabled
        if not self.asusctl.get_fan_curve_enabled(current_profile):
            success, msg = self.asusctl.enable_fan_curves(current_profile, True)
            if not success:
                QMessageBox.warning(self, "Error", f"Failed to enable fan curves: {msg}")
                return
        
        # Apply the curve
        success, message = self.asusctl.set_fan_curve(current_profile, fan_name, self.current_curve)
        
        if success:
            # Update original curve to match current
            self.original_curve = FanCurve([FanCurvePoint(p.temperature, p.fan_speed) for p in self.current_curve.points])
            # Clear preset dropdown since we're applying a custom curve
            if hasattr(self, 'preset_dropdown'):
                self.preset_dropdown.blockSignals(True)
                self.preset_dropdown.setCurrentIndex(-1)  # Clear selection
                self.preset_dropdown.blockSignals(False)
            # Clear profile dropdown too
            if hasattr(self, 'profile_dropdown'):
                self.profile_dropdown.blockSignals(True)
                self.profile_dropdown.setCurrentIndex(0)
                self.profile_dropdown.blockSignals(False)
            
            self.curve_changed.emit(self.current_curve)
            QMessageBox.information(self, "Applied", f"Fan curve has been applied and saved for {fan_name}!")
        else:
            QMessageBox.warning(self, "Error", f"Failed to apply fan curve:\n{message}")
    
    def get_current_fan_name(self) -> str:
        """Get the currently selected fan name."""
        if self.cpu_fan_btn.isChecked():
            return "CPU"
        elif self.gpu_fan_btn.isChecked():
            return "GPU"
        return "CPU"
    
    def test_fan(self):
        """Test fan by setting it to 100% for 5 seconds with countdown."""
        if not self.asusctl.is_available():
            QMessageBox.warning(
                self,
                "Not Available",
                "asusctl is not available. Cannot test fan."
            )
            return
        
        fan_name = self.get_current_fan_name()
        
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Test Fan",
            f"This will set the {fan_name} fan to 100% for 5 seconds.\n\n"
            "The fan will be very loud. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Stop any existing timers
        if self.test_restore_timer:
            self.test_restore_timer.stop()
        if self.test_countdown_timer:
            self.test_countdown_timer.stop()
        
        # Disable button during test
        self.test_fan_btn.setEnabled(False)
        self.test_seconds_remaining = 5
        self.test_fan_name = fan_name  # Store fan name for countdown display
        
        # Save original curve
        if self.current_curve:
            self.original_curve_before_test = FanCurve([
                FanCurvePoint(p.temperature, p.fan_speed) 
                for p in self.current_curve.points
            ])
        else:
            # If no current curve, try to get original from system
            current_profile = self.asusctl.get_current_profile() or Profile.BALANCED
            curves = self.asusctl.get_fan_curves(current_profile)
            if fan_name in curves:
                self.original_curve_before_test = curves[fan_name]
        
        # Get current profile
        current_profile = self.asusctl.get_current_profile() or Profile.BALANCED
        
        # Enable fan curves for the profile if not already enabled
        enabled = self.asusctl.get_fan_curve_enabled(current_profile)
        if enabled is False:
            self.asusctl.enable_fan_curves(current_profile, True)
        
        # Create max curve for testing - asusctl requires exactly 8 points
        # Use a range that covers typical temperatures: 30°C to 90°C
        max_curve = FanCurve([
            FanCurvePoint(30, 100),
            FanCurvePoint(40, 100),
            FanCurvePoint(50, 100),
            FanCurvePoint(60, 100),
            FanCurvePoint(70, 100),
            FanCurvePoint(80, 100),
            FanCurvePoint(85, 100),
            FanCurvePoint(90, 100),
        ])
        
        # Update button text to show starting
        self.test_fan_btn.setText(f"⏳ Setting {fan_name} fan to 100%...")
        
        # Give a moment for the button update to show
        from PyQt6.QtCore import QCoreApplication
        QCoreApplication.processEvents()
        
        # Apply max curve
        success, message = self.asusctl.set_fan_curve(current_profile, fan_name, max_curve)
        
        if not success:
            QMessageBox.warning(self, "Test Failed", f"Failed to test fan:\n{message}\n\nMake sure asusctl is properly installed and you have permissions.")
            self.test_fan_btn.setEnabled(True)
            self.test_fan_btn.setText("Test Fan (100% for 5s)")
            return
        
        # Start countdown timer (updates every second) - must be singleShot=False for repeating
        self.test_countdown_timer = QTimer(self)
        self.test_countdown_timer.timeout.connect(self.update_test_countdown)
        self.test_countdown_timer.start(1000)  # Update every second
        
        # Set timer to restore after 5 seconds
        self.test_restore_timer = QTimer(self)
        self.test_restore_timer.setSingleShot(True)
        self.test_restore_timer.timeout.connect(lambda: self.restore_after_test(fan_name, current_profile))
        self.test_restore_timer.start(5000)  # 5 seconds
        
        # Initial countdown update - show immediately
        self.update_test_countdown()
        
        # Show info dialog - but use show() instead of exec() so it's non-blocking
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("Test Started")
        msg_box.setText(f"✅ {fan_name} fan set to 100%.\n\nWatch the button for countdown.")
        msg_box.show()
        # Auto-close after 2 seconds
        QTimer.singleShot(2000, msg_box.close)
    
    def update_test_countdown(self):
        """Update the countdown display during fan test."""
        if not hasattr(self, 'test_seconds_remaining') or not hasattr(self, 'test_fan_name'):
            return
        
        if self.test_seconds_remaining > 0:
            self.test_fan_btn.setText(
                f"⏱️ Testing {self.test_fan_name} Fan: {self.test_seconds_remaining}s remaining (100% speed)"
            )
            self.test_seconds_remaining -= 1
        elif self.test_seconds_remaining == 0:
            self.test_fan_btn.setText(f"⏳ Restoring {self.test_fan_name} Fan to previous settings...")
            # Stop countdown timer
            if self.test_countdown_timer:
                self.test_countdown_timer.stop()
                self.test_countdown_timer = None
    
    def restore_after_test(self, fan_name: str, profile: Profile):
        """Restore fan curve after test."""
        # Stop countdown timer
        if self.test_countdown_timer:
            self.test_countdown_timer.stop()
            self.test_countdown_timer = None
        
        # Update button to show restoring
        self.test_fan_btn.setText(f"⏳ Restoring {fan_name} Fan to previous settings...")
        
        # Process events to update UI
        from PyQt6.QtCore import QCoreApplication
        QCoreApplication.processEvents()
        
        # Restore original curve if available
        if hasattr(self, 'original_curve_before_test') and self.original_curve_before_test:
            success, message = self.asusctl.set_fan_curve(profile, fan_name, self.original_curve_before_test)
            if success:
                # Reload curve in editor
                self.load_curve(self.original_curve_before_test)
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Test Complete",
                    f"✅ {fan_name} fan test completed successfully!\n\n"
                    "Fan has been restored to previous settings."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Restore Warning",
                    f"Test complete, but failed to restore original curve:\n{message}\n\n"
                    "Please manually restore your fan curve settings."
                )
        else:
            QMessageBox.information(
                self,
                "Test Complete",
                f"✅ {fan_name} fan test completed.\n\n"
                "Fan speed will return to normal based on temperature."
            )
        
        # Re-enable button and reset text
        self.test_fan_btn.setEnabled(True)
        self.test_fan_btn.setText("Test Fan (100% for 5s)")
        
        # Clean up
        if hasattr(self, 'test_restore_timer'):
            self.test_restore_timer = None
        if hasattr(self, 'test_countdown_timer'):
            self.test_countdown_timer = None
        if hasattr(self, 'test_fan_name'):
            delattr(self, 'test_fan_name')
        self.test_seconds_remaining = 0

