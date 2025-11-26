#!/usr/bin/env python3
"""
Dashboard Widget Components

Reusable widgets for displaying metrics and graphs.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPainter, QPen
import pyqtgraph as pg
from typing import Optional, List

from .game_style_theme import GAME_COLORS


class MetricCard(QWidget):
    """A card widget displaying a single metric value."""
    
    def __init__(self, title: str, unit: str = "", color: str = "#2196F3"):
        super().__init__()
        self.title = title
        self.unit = unit
        self.color = color
        self.value = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(5)
        
        # Title label
        self.title_label = QLabel(self.title)
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(False)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"color: #666;")
        layout.addWidget(self.title_label)
        
        # Value label
        self.value_label = QLabel("--")
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setStyleSheet(f"color: {self.color};")
        layout.addWidget(self.value_label)
        
        # Unit label (if provided)
        if self.unit:
            self.unit_label = QLabel(self.unit)
            unit_font = QFont()
            unit_font.setPointSize(9)
            self.unit_label.setFont(unit_font)
            self.unit_label.setStyleSheet("color: #999;")
            layout.addWidget(self.unit_label)
        
        # Modern minimalist styling
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #e8e8e8;
                border-radius: 12px;
            }
        """)
        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Add subtle hover effect (will be enhanced with event filtering if needed)
    
    def set_value(self, value: Optional[float], decimals: int = 1, text: str = None):
        """
        Update the displayed value.
        
        Args:
            value: Numeric value to display
            decimals: Number of decimal places
            text: Custom text to display instead of value
        """
        self.value = value
        
        if text is not None:
            display_text = text
        elif value is not None:
            display_text = f"{value:.{decimals}f}"
        else:
            display_text = "--"
        
        self.value_label.setText(display_text)


class GraphWidget(QWidget):
    """Widget for displaying real-time graphs."""
    
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Create PyQtGraph widget with game-style dark theme
        self.graph = pg.PlotWidget()
        # Dark background with game-style colors
        bg_color = GAME_COLORS['bg_card']
        self.graph.setBackground(pg.mkColor(bg_color))
        self.graph.setLabel('left', 'Value', **{'color': GAME_COLORS['text_secondary'], 'font-size': '11pt'})
        self.graph.setLabel('bottom', 'Time (seconds)', **{'color': GAME_COLORS['text_secondary'], 'font-size': '11pt'})
        self.graph.showGrid(x=True, y=True, alpha=0.1)
        
        # Game-style axis colors
        self.graph.getAxis('left').setPen(pg.mkPen(color=GAME_COLORS['border'], width=1))
        self.graph.getAxis('bottom').setPen(pg.mkPen(color=GAME_COLORS['border'], width=1))
        # Axis text colors
        self.graph.getAxis('left').setTextPen(pg.mkPen(color=GAME_COLORS['text_secondary']))
        self.graph.getAxis('bottom').setTextPen(pg.mkPen(color=GAME_COLORS['text_secondary']))
        
        # Create plots with game-style neon colors
        self.cpu_plot = self.graph.plot(pen=pg.mkPen(color=GAME_COLORS['accent_blue'], width=2.5), name='CPU %')
        self.cpu_temp_plot = self.graph.plot(pen=pg.mkPen(color=GAME_COLORS['accent_red'], width=2.5), name='CPU Temp')
        self.memory_plot = self.graph.plot(pen=pg.mkPen(color=GAME_COLORS['accent_orange'], width=2.5), name='Memory %')
        self.gpu_plot = self.graph.plot(pen=pg.mkPen(color=GAME_COLORS['accent_cyan'], width=2.5), name='GPU %')
        self.gpu_temp_plot = self.graph.plot(pen=pg.mkPen(color=GAME_COLORS['accent_pink'], width=2.5), name='GPU Temp')
        
        # Layout with game-style border
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {GAME_COLORS['bg_card']};
                border: 2px solid {GAME_COLORS['border']};
                border-radius: 12px;
            }}
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.addWidget(self.graph)
        
        layout.addWidget(container)
        
        # Game-style legend
        legend = self.graph.addLegend(offset=(10, 10))
        legend.setPen(pg.mkPen(color=GAME_COLORS['border'], width=1))
        legend.setBrush(pg.mkBrush(color=pg.mkColor(GAME_COLORS['bg_card'] + 'F0')))  # Semi-transparent
        # Legend text color
        for item in legend.items:
            if hasattr(item, 'label'):
                item.label.setColor(pg.mkColor(GAME_COLORS['text_primary']))
    
    def update_data(self, history: dict):
        """Update graph with new historical data."""
        if not history.get('timestamp'):
            return
        
        timestamps = history['timestamp']
        if not timestamps:
            return
        
        # Convert timestamps to relative time (seconds from start)
        if len(timestamps) > 1:
            base_time = timestamps[0]
            times = [(t - base_time) for t in timestamps]
        else:
            times = [0]
        
        # Update plots
        if history.get('cpu_percent'):
            self.cpu_plot.setData(times, list(history['cpu_percent']))
        
        if history.get('cpu_temp'):
            self.cpu_temp_plot.setData(times, list(history['cpu_temp']))
        
        if history.get('memory_percent'):
            self.memory_plot.setData(times, list(history['memory_percent']))
        
        if history.get('gpu_utilization'):
            self.gpu_plot.setData(times, list(history['gpu_utilization']))
        
        if history.get('gpu_temp'):
            self.gpu_temp_plot.setData(times, list(history['gpu_temp']))
        
        # Auto-range
        self.graph.enableAutoRange()

