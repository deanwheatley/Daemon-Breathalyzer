#!/usr/bin/env python3
"""
Fan Curve Builder Widget

Interactive fan curve builder with canvas-based point manipulation.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QFormLayout, QGroupBox, QMessageBox, QFileDialog,
    QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QFont
import pyqtgraph as pg
import numpy as np
import json
from pathlib import Path
from datetime import datetime

from .game_style_theme import GAME_COLORS, GAME_STYLES
from .ui_scaling import UIScaling
from ..control.curve_file_manager import CurveFileManager


class CurveData:
    """Data model for fan curves."""
    
    def __init__(self, name="New Curve", description=""):
        self.name = name
        self.description = description
        self.points = [(30, 0), (90, 0)]  # Default flat curve
        self.created = datetime.now().isoformat()
        self.modified = datetime.now().isoformat()
    
    def add_point(self, temp, speed):
        """Add or update a point."""
        # Remove existing point at same temperature
        self.points = [(t, s) for t, s in self.points if t != temp]
        # Add new point and sort by temperature
        self.points.append((temp, speed))
        self.points.sort(key=lambda p: p[0])
        self.modified = datetime.now().isoformat()
    
    def remove_point(self, temp):
        """Remove point at temperature."""
        if len(self.points) <= 2:
            raise ValueError("Cannot remove point - minimum 2 points required")
        self.points = [(t, s) for t, s in self.points if t != temp]
        self.modified = datetime.now().isoformat()
    
    def get_speed_at_temp(self, temp):
        """Get interpolated fan speed at temperature."""
        if not self.points:
            return 0
        
        # Sort points by temperature
        sorted_points = sorted(self.points, key=lambda p: p[0])
        
        # Handle edge cases
        if temp <= sorted_points[0][0]:
            return sorted_points[0][1]
        if temp >= sorted_points[-1][0]:
            return sorted_points[-1][1]
        
        # Linear interpolation
        for i in range(len(sorted_points) - 1):
            t1, s1 = sorted_points[i]
            t2, s2 = sorted_points[i + 1]
            
            if t1 <= temp <= t2:
                if t2 == t1:
                    return s1
                ratio = (temp - t1) / (t2 - t1)
                return s1 + ratio * (s2 - s1)
        
        return 0


class InteractiveCanvas(QWidget):
    """PyQtGraph canvas with interactive grid."""
    
    point_selected = pyqtSignal(int, int)  # temp, speed
    curve_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.curve_data = CurveData()
        self.selected_temp = None
        self.temp_range = (30, 90)
        self.speed_range = (0, 100)
        self.grid_size = 10  # 10x10 grid
        
        self._init_ui()
        self._update_display()
    
    def _init_ui(self):
        """Initialize the canvas UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create PyQtGraph widget
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground(pg.mkColor(GAME_COLORS['bg_card']))
        self.graph_widget.setLabel('left', 'Fan Speed (%)', color=GAME_COLORS['text_secondary'])
        self.graph_widget.setLabel('bottom', 'Temperature (°C)', color=GAME_COLORS['text_secondary'])
        self.graph_widget.setXRange(self.temp_range[0], self.temp_range[1])
        self.graph_widget.setYRange(self.speed_range[0], self.speed_range[1])
        
        # Style axes
        self.graph_widget.getAxis('left').setPen(pg.mkPen(color=GAME_COLORS['border'], width=1))
        self.graph_widget.getAxis('bottom').setPen(pg.mkPen(color=GAME_COLORS['border'], width=1))
        self.graph_widget.getAxis('left').setTextPen(pg.mkPen(color=GAME_COLORS['text_secondary']))
        self.graph_widget.getAxis('bottom').setTextPen(pg.mkPen(color=GAME_COLORS['text_secondary']))
        
        # Create 10x10 grid
        self._setup_grid()
        
        # Plot items
        self.curve_plot = self.graph_widget.plot([], [], pen=pg.mkPen(color=GAME_COLORS['accent_blue'], width=3))
        self.points_plot = None
        
        # Mouse interaction
        self.graph_widget.scene().sigMouseClicked.connect(self._on_mouse_click)
        self.graph_widget.scene().sigMouseMoved.connect(self._on_mouse_move)
        self.dragging_point = None
        
        layout.addWidget(self.graph_widget)
    
    def _setup_grid(self):
        """Setup 10x10 grid lines."""
        # Temperature grid lines (vertical)
        temp_step = (self.temp_range[1] - self.temp_range[0]) / self.grid_size
        for i in range(self.grid_size + 1):
            temp = self.temp_range[0] + i * temp_step
            line = pg.InfiniteLine(pos=temp, angle=90, pen=pg.mkPen(color=GAME_COLORS['border'], width=1, style=Qt.PenStyle.DotLine))
            self.graph_widget.addItem(line)
        
        # Speed grid lines (horizontal)
        speed_step = (self.speed_range[1] - self.speed_range[0]) / self.grid_size
        for i in range(self.grid_size + 1):
            speed = self.speed_range[0] + i * speed_step
            line = pg.InfiniteLine(pos=speed, angle=0, pen=pg.mkPen(color=GAME_COLORS['border'], width=1, style=Qt.PenStyle.DotLine))
            self.graph_widget.addItem(line)
    
    def _snap_to_grid(self, temp, speed):
        """Snap coordinates to nearest grid intersection."""
        temp_step = (self.temp_range[1] - self.temp_range[0]) / self.grid_size
        speed_step = (self.speed_range[1] - self.speed_range[0]) / self.grid_size
        
        snapped_temp = round((temp - self.temp_range[0]) / temp_step) * temp_step + self.temp_range[0]
        snapped_speed = round((speed - self.speed_range[0]) / speed_step) * speed_step + self.speed_range[0]
        
        # Clamp to ranges
        snapped_temp = max(self.temp_range[0], min(self.temp_range[1], snapped_temp))
        snapped_speed = max(self.speed_range[0], min(self.speed_range[1], snapped_speed))
        
        return int(snapped_temp), int(snapped_speed)
    
    def _on_mouse_click(self, event):
        """Handle mouse clicks on canvas."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Get click position in data coordinates
            pos = self.graph_widget.getPlotItem().vb.mapSceneToView(event.scenePos())
            temp, speed = self._snap_to_grid(pos.x(), pos.y())
            
            # Check if clicking on existing point
            clicked_existing = False
            for point_temp, point_speed in self.curve_data.points:
                if abs(point_temp - temp) < 3 and abs(point_speed - speed) < 5:
                    self.selected_temp = point_temp
                    self.dragging_point = point_temp
                    self.point_selected.emit(point_temp, point_speed)
                    clicked_existing = True
                    break
            
            if not clicked_existing:
                # Add new point
                self.curve_data.add_point(temp, speed)
                self.selected_temp = temp
                self.point_selected.emit(temp, speed)
                self.curve_changed.emit()
            
            self._update_display()
        elif event.button() == Qt.MouseButton.LeftButton and hasattr(event, 'isFinish') and event.isFinish():
            # Mouse release - stop dragging
            self.dragging_point = None
    
    def _on_mouse_move(self, event):
        """Handle mouse movement for dragging points."""
        if self.dragging_point is not None and hasattr(event, 'buttons') and event.buttons() == Qt.MouseButton.LeftButton:
            # Get current position
            pos = self.graph_widget.getPlotItem().vb.mapSceneToView(event.scenePos())
            new_temp, new_speed = self._snap_to_grid(pos.x(), pos.y())
            
            # Update point position
            try:
                self.curve_data.remove_point(self.dragging_point)
                self.curve_data.add_point(new_temp, new_speed)
                self.selected_temp = new_temp
                self.dragging_point = new_temp
                self.point_selected.emit(new_temp, new_speed)
                self.curve_changed.emit()
                self._update_display()
            except ValueError:
                # Ignore invalid moves
                pass
    
    def _update_display(self):
        """Update the visual display."""
        if not self.curve_data.points:
            return
        
        # Update curve line
        temps = [p[0] for p in self.curve_data.points]
        speeds = [p[1] for p in self.curve_data.points]
        
        # Create smooth curve
        if len(temps) >= 2:
            smooth_temps = np.linspace(min(temps), max(temps), 100)
            smooth_speeds = [self.curve_data.get_speed_at_temp(t) for t in smooth_temps]
            self.curve_plot.setData(smooth_temps, smooth_speeds)
        else:
            self.curve_plot.setData(temps, speeds)
        
        # Remove old points plot
        if self.points_plot:
            self.graph_widget.removeItem(self.points_plot)
        
        # Add control points
        point_colors = []
        for temp, speed in self.curve_data.points:
            if temp == self.selected_temp:
                point_colors.append(GAME_COLORS['accent_green'])  # Selected point
            else:
                point_colors.append(GAME_COLORS['accent_blue'])   # Normal point
        
        self.points_plot = pg.ScatterPlotItem(
            temps, speeds,
            pen=pg.mkPen(color=GAME_COLORS['accent_cyan'], width=2),
            brush=[pg.mkBrush(color=c) for c in point_colors],
            size=12,
            symbol='o'
        )
        self.graph_widget.addItem(self.points_plot)
    
    def delete_selected_point(self):
        """Delete the currently selected point."""
        if self.selected_temp is not None:
            try:
                self.curve_data.remove_point(self.selected_temp)
                self.selected_temp = None
                self.dragging_point = None
                self.curve_changed.emit()
                self._update_display()
                return True
            except ValueError as e:
                QMessageBox.warning(self, "Cannot Delete", str(e))
                return False
        return False
    
    def set_curve_data(self, curve_data):
        """Set new curve data."""
        self.curve_data = curve_data
        self.selected_temp = None
        self._update_display()


class PropertiesPanel(QGroupBox):
    """Properties panel for point editing."""
    
    point_updated = pyqtSignal(int, int, int, int)  # old_temp, old_speed, new_temp, new_speed
    
    def __init__(self, parent=None):
        super().__init__("Properties", parent)
        self.setStyleSheet(GAME_STYLES['groupbox'])
        self.selected_temp = None
        self.selected_speed = None
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize properties UI."""
        layout = QVBoxLayout(self)
        
        # Selected point section
        form_layout = QFormLayout()
        
        self.temp_input = QSpinBox()
        self.temp_input.setRange(30, 90)
        self.temp_input.setValue(50)
        self.temp_input.setStyleSheet(GAME_STYLES['spinbox'])
        form_layout.addRow("Temperature (°C):", self.temp_input)
        
        self.speed_input = QSpinBox()
        self.speed_input.setRange(0, 100)
        self.speed_input.setValue(0)
        self.speed_input.setStyleSheet(GAME_STYLES['spinbox'])
        form_layout.addRow("Fan Speed (%):", self.speed_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        self.update_btn = QPushButton("Update Point")
        self.update_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {GAME_COLORS['accent_blue']};
                color: {GAME_COLORS['text_primary']};
                border: none;
                padding: 8px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
            }}
        """)
        self.update_btn.clicked.connect(self._update_point)
        layout.addWidget(self.update_btn)
        
        self.delete_btn = QPushButton("Delete Point")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
            }
        """)
        layout.addWidget(self.delete_btn)
        
        layout.addStretch()
    
    def set_selected_point(self, temp, speed):
        """Set the selected point values."""
        self.selected_temp = temp
        self.selected_speed = speed
        self.temp_input.setValue(temp)
        self.speed_input.setValue(speed)
    
    def _update_point(self):
        """Update the selected point."""
        if self.selected_temp is not None:
            new_temp = self.temp_input.value()
            new_speed = self.speed_input.value()
            self.point_updated.emit(self.selected_temp, self.selected_speed, new_temp, new_speed)


class FileOperationsBar(QWidget):
    """File operations button bar."""
    
    new_clicked = pyqtSignal()
    load_clicked = pyqtSignal()
    save_clicked = pyqtSignal()
    save_as_clicked = pyqtSignal()
    delete_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize file operations UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        button_style = f"""
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
                background-color: {GAME_COLORS['bg_medium']};
            }}
        """
        
        buttons = [
            ("New", self.new_clicked),
            ("Load", self.load_clicked),
            ("Save", self.save_clicked),
            ("Save As", self.save_as_clicked),
            ("Delete", self.delete_clicked)
        ]
        
        for text, signal in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(button_style)
            btn.clicked.connect(signal.emit)
            layout.addWidget(btn)
        
        layout.addStretch()


class FanCurveBuilderWidget(QWidget):
    """Main Fan Curve Builder widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self.file_manager = CurveFileManager()
        
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """Initialize the main UI."""
        self.setStyleSheet(GAME_STYLES['widget'])
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Fan Curve Builder")
        title.setStyleSheet(f"color: {GAME_COLORS['accent_blue']}; font-size: 24pt; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # File operations bar
        self.file_ops = FileOperationsBar()
        layout.addWidget(self.file_ops)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Canvas (left side, 70%)
        canvas_container = QWidget()
        canvas_container.setStyleSheet(f"""
            QWidget {{
                background-color: {GAME_COLORS['bg_card']};
                border: 2px solid {GAME_COLORS['border']};
                border-radius: 12px;
            }}
        """)
        canvas_layout = QVBoxLayout(canvas_container)
        canvas_layout.setContentsMargins(15, 15, 15, 15)
        
        self.canvas = InteractiveCanvas()
        canvas_layout.addWidget(self.canvas)
        
        content_layout.addWidget(canvas_container, 7)
        
        # Properties panel (right side, 30%)
        self.properties = PropertiesPanel()
        content_layout.addWidget(self.properties, 3)
        
        layout.addLayout(content_layout)
    
    def _connect_signals(self):
        """Connect widget signals."""
        # Canvas signals
        self.canvas.point_selected.connect(self.properties.set_selected_point)
        self.canvas.curve_changed.connect(self._on_curve_changed)
        
        # Properties signals
        self.properties.point_updated.connect(self._update_point)
        self.properties.delete_btn.clicked.connect(self.canvas.delete_selected_point)
        
        # File operations
        self.file_ops.new_clicked.connect(self._new_curve)
        self.file_ops.load_clicked.connect(self._load_curve)
        self.file_ops.save_clicked.connect(self._save_curve)
        self.file_ops.save_as_clicked.connect(self._save_as_curve)
        self.file_ops.delete_clicked.connect(self._delete_curve)
    
    def _new_curve(self):
        """Create a new curve."""
        self.canvas.set_curve_data(CurveData())
        self.current_file = None
    
    def _update_point(self, old_temp, old_speed, new_temp, new_speed):
        """Update a point in the curve."""
        try:
            self.canvas.curve_data.remove_point(old_temp)
            self.canvas.curve_data.add_point(new_temp, new_speed)
            self.canvas.selected_temp = new_temp
            self.canvas._update_display()
        except ValueError as e:
            QMessageBox.warning(self, "Cannot Update", str(e))
    
    def _load_curve(self):
        """Load a curve from file."""
        # File dialog is already imported
        
        curves_dir = self.file_manager.curves_dir
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Fan Curve", str(curves_dir), "Curve Files (*.curve)"
        )
        
        if filename:
            curve_data = self.file_manager.load_curve(Path(filename).name)
            if curve_data:
                self.canvas.set_curve_data(curve_data)
                self.current_file = Path(filename).name
                QMessageBox.information(self, "Success", f"Loaded curve: {curve_data.name}")
            else:
                QMessageBox.warning(self, "Error", "Failed to load curve file.")
    
    def _save_curve(self):
        """Save current curve."""
        if self.current_file:
            if self.file_manager.save_curve(self.canvas.curve_data, self.current_file):
                QMessageBox.information(self, "Success", "Curve saved successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to save curve.")
        else:
            self._save_as_curve()
    
    def _save_as_curve(self):
        """Save curve with new name."""
        # Dialogs are already imported
        
        # Get curve name
        name, ok = QInputDialog.getText(self, "Save Curve", "Enter curve name:", text=self.canvas.curve_data.name)
        if not ok or not name.strip():
            return
        
        self.canvas.curve_data.name = name.strip()
        
        # Get description
        desc, ok = QInputDialog.getText(self, "Curve Description", "Enter description (optional):", text=self.canvas.curve_data.description)
        if ok:
            self.canvas.curve_data.description = desc.strip()
        
        # Save file
        curves_dir = self.file_manager.curves_dir
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Fan Curve", str(curves_dir / f"{name}.curve"), "Curve Files (*.curve)"
        )
        
        if filename:
            if self.file_manager.save_curve(self.canvas.curve_data, Path(filename).name):
                self.current_file = Path(filename).name
                QMessageBox.information(self, "Success", "Curve saved successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to save curve.")
    
    def _delete_curve(self):
        """Delete a curve file."""
        # Input dialog is already imported
        
        # List available curves
        curves = self.file_manager.list_curves()
        if not curves:
            QMessageBox.information(self, "No Curves", "No curve files found to delete.")
            return
        
        # Select curve to delete
        curve_name, ok = QInputDialog.getItem(self, "Delete Curve", "Select curve to delete:", curves, 0, False)
        if not ok:
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete '{curve_name}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.file_manager.delete_curve(curve_name):
                QMessageBox.information(self, "Success", f"Deleted curve: {curve_name}")
                # Clear current file if it was deleted
                if self.current_file and Path(self.current_file).stem == curve_name:
                    self.current_file = None
            else:
                QMessageBox.warning(self, "Error", "Failed to delete curve.")
    
    def _on_curve_changed(self):
        """Handle curve changes."""
        # Could add unsaved changes indicator here
        pass
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Delete:
            self.canvas.delete_selected_point()
        super().keyPressEvent(event)