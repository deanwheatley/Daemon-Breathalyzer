#!/usr/bin/env python3
"""
Responsive Dashboard

Responsive dashboard widget that scales with window size and supports hiding/showing meters.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QCheckBox, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QEvent
from PyQt6.QtGui import QFont, QIcon
from pathlib import Path
from typing import Dict, Optional
import math

from ..utils.preferences_manager import PreferencesManager
from .dashboard_widgets import MetricCard, GraphWidget
from .fan_speed_gauge import FanSpeedGauge
from .game_style_theme import GAME_COLORS, GAME_STYLES
from .animated_widgets import AnimatedMetricCard, AnimatedIcon


class ResponsiveDashboard(QWidget):
    """Responsive dashboard that scales with window size."""
    
    def __init__(self, monitor, asusctl, parent=None):
        super().__init__(parent)
        self.monitor = monitor
        self.asusctl = asusctl
        self.preferences = PreferencesManager()
        
        # Store all metric widgets
        self.metric_widgets: Dict[str, QWidget] = {}
        
        self._setup_ui()
        self._update_visibility()
    
    def _setup_ui(self):
        """Set up responsive UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title with animated icon
        title_layout = QHBoxLayout()
        title = QLabel("System Monitor")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {GAME_COLORS['text_primary']};")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # Animated icon
        icon_path = self._find_icon_path()
        if icon_path:
            self.animated_icon = AnimatedIcon(str(icon_path), self)
            self.animated_icon.setFixedSize(50, 50)
            title_layout.addWidget(self.animated_icon)
        
        layout.addLayout(title_layout)
        
        # Preferences button (eye icon to toggle visibility)
        prefs_btn = QPushButton("⚙ Preferences")
        prefs_btn.setStyleSheet(GAME_STYLES['button'])
        prefs_btn.clicked.connect(self._show_preferences_dialog)
        title_layout.insertWidget(1, prefs_btn)
        
        # Scrollable metrics area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        scroll_widget = QWidget()
        self.scroll_layout = QGridLayout(scroll_widget)
        self.scroll_layout.setSpacing(15)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Create all metric widgets
        self._create_metric_widgets()
        
        # Graphs
        self.graph_widget = GraphWidget()
        layout.addWidget(self.graph_widget)
    
    def resizeEvent(self, event):
        """Handle window resize to update layout."""
        super().resizeEvent(event)
        # Update layout when window is resized for responsive columns
        QTimer.singleShot(100, self._update_layout)
    
    def _find_icon_path(self) -> Optional[Path]:
        """Find icon path."""
        project_root = Path(__file__).parent.parent.parent
        icon_paths = [
            project_root / "img" / "icon.png",
            project_root / "img" / "icon.jpg",
        ]
        for icon_path in icon_paths:
            if icon_path.exists():
                return icon_path
        return None
    
    def _create_metric_widgets(self):
        """Create all metric widgets."""
        # CPU metrics
        self.metric_widgets['cpu_percent'] = AnimatedMetricCard("CPU Usage", "%", GAME_COLORS['accent_blue'])
        self.metric_widgets['cpu_temp'] = AnimatedMetricCard("CPU Temp", "°C", GAME_COLORS['accent_red'])
        self.metric_widgets['cpu_freq'] = AnimatedMetricCard("CPU Freq", "MHz", GAME_COLORS['accent_green'])
        
        # Memory metrics
        self.metric_widgets['memory'] = AnimatedMetricCard("Memory", "%", GAME_COLORS['accent_orange'])
        self.metric_widgets['memory_used'] = AnimatedMetricCard("Memory Used", "GB", GAME_COLORS['accent_purple'])
        
        # GPU metrics
        self.metric_widgets['gpu_usage'] = AnimatedMetricCard("GPU Usage", "%", GAME_COLORS['accent_cyan'])
        self.metric_widgets['gpu_temp'] = AnimatedMetricCard("GPU Temp", "°C", GAME_COLORS['accent_pink'])
        self.metric_widgets['gpu_memory'] = AnimatedMetricCard("GPU Memory", "%", GAME_COLORS['accent_blue'])
        
        # Network metrics
        self.metric_widgets['network_sent'] = AnimatedMetricCard("Network Sent", "Mbps", GAME_COLORS['accent_red'])
        self.metric_widgets['network_recv'] = AnimatedMetricCard("Network Recv", "Mbps", GAME_COLORS['accent_green'])
        self.metric_widgets['network_total'] = AnimatedMetricCard("Network Total", "Mbps", GAME_COLORS['accent_blue'])
        
        # FPS
        self.metric_widgets['fps'] = AnimatedMetricCard("FPS", "fps", GAME_COLORS['accent_pink'])
        
        # Fan gauges
        self.metric_widgets['cpu_fan_gauge'] = FanSpeedGauge("CPU Fan", max_rpm=7000, color=GAME_COLORS['accent_blue'])
        self.metric_widgets['gpu_fan_gauge'] = FanSpeedGauge("GPU Fan", max_rpm=7000, color=GAME_COLORS['accent_cyan'])
        
        # Add all widgets to grid
        self._update_layout()
    
    def _update_layout(self):
        """Update layout based on window size and visibility preferences."""
        # Clear existing layout
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Calculate columns based on available width (responsive)
        # Estimate card width (including spacing): ~200px per card
        available_width = self.width() - 60  # Account for margins
        cols = max(2, min(4, int(available_width / 220)))  # 2-4 columns based on width
        
        row = 0
        col = 0
        
        # Widget order
        widget_order = [
            'cpu_percent', 'cpu_temp', 'cpu_freq',
            'memory', 'memory_used', 'gpu_usage',
            'gpu_temp', 'gpu_memory', 'fps',
            'network_sent', 'network_recv', 'network_total',
            'cpu_fan_gauge', 'gpu_fan_gauge',
        ]
        
        for widget_name in widget_order:
            if widget_name in self.metric_widgets:
                if self.preferences.is_meter_visible(widget_name):
                    widget = self.metric_widgets[widget_name]
                    self.scroll_layout.addWidget(widget, row, col)
                    col += 1
                    if col >= cols:
                        col = 0
                        row += 1
    
    def _update_visibility(self):
        """Update widget visibility based on preferences."""
        for widget_name, widget in self.metric_widgets.items():
            visible = self.preferences.is_meter_visible(widget_name)
            widget.setVisible(visible)
        self._update_layout()
    
    def _show_preferences_dialog(self):
        """Show preferences dialog for hiding/showing meters."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QPushButton, QScrollArea
        from ..control.asusctl_interface import Profile
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Dashboard Preferences")
        dialog.setMinimumSize(400, 500)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {GAME_COLORS['bg_medium']};
                color: {GAME_COLORS['text_primary']};
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        
        title = QLabel("Show/Hide Meters")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {GAME_COLORS['accent_blue']}; margin-bottom: 10px;")
        layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        checkboxes = {}
        for widget_name in sorted(self.metric_widgets.keys()):
            cb = QCheckBox(widget_name.replace('_', ' ').title())
            cb.setChecked(self.preferences.is_meter_visible(widget_name))
            cb.setStyleSheet(f"""
                QCheckBox {{
                    color: {GAME_COLORS['text_primary']};
                    font-size: 12px;
                    padding: 5px;
                }}
                QCheckBox::indicator {{
                    width: 20px;
                    height: 20px;
                }}
            """)
            checkboxes[widget_name] = cb
            scroll_layout.addWidget(cb)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        apply_btn = QPushButton("Apply")
        apply_btn.setStyleSheet(GAME_STYLES['button'])
        apply_btn.clicked.connect(lambda: self._apply_preferences(checkboxes, dialog))
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(GAME_STYLES['button'])
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(apply_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def _apply_preferences(self, checkboxes: Dict[str, QCheckBox], dialog):
        """Apply visibility preferences."""
        for widget_name, checkbox in checkboxes.items():
            self.preferences.set_meter_visible(widget_name, checkbox.isChecked())
        self._update_visibility()
        dialog.accept()
    
    def update_metrics(self, metrics: Dict, history: Dict):
        """Update all visible metrics."""
        # CPU
        if 'cpu_percent' in self.metric_widgets:
            self.metric_widgets['cpu_percent'].set_value(metrics.get('cpu_percent', 0.0))
        if 'cpu_temp' in self.metric_widgets:
            self.metric_widgets['cpu_temp'].set_value(metrics.get('cpu_temp'))
        if 'cpu_freq' in self.metric_widgets:
            self.metric_widgets['cpu_freq'].set_value(metrics.get('cpu_freq', 0.0))
        
        # Memory
        if 'memory' in self.metric_widgets:
            self.metric_widgets['memory'].set_value(metrics.get('memory_percent', 0.0))
        if 'memory_used' in self.metric_widgets:
            self.metric_widgets['memory_used'].set_value(metrics.get('memory_used_gb', 0.0), decimals=2)
        
        # GPU
        if 'gpu_usage' in self.metric_widgets:
            gpu_util = metrics.get('gpu_utilization', 0.0) or 0.0
            self.metric_widgets['gpu_usage'].set_value(gpu_util)
        if 'gpu_temp' in self.metric_widgets:
            self.metric_widgets['gpu_temp'].set_value(metrics.get('gpu_temp'))
        if 'gpu_memory' in self.metric_widgets:
            self.metric_widgets['gpu_memory'].set_value(metrics.get('gpu_memory_percent'))
        
        # Network
        if 'network_sent' in self.metric_widgets:
            self.metric_widgets['network_sent'].set_value(metrics.get('network_sent_mbps', 0.0), decimals=2)
        if 'network_recv' in self.metric_widgets:
            self.metric_widgets['network_recv'].set_value(metrics.get('network_recv_mbps', 0.0), decimals=2)
        if 'network_total' in self.metric_widgets:
            self.metric_widgets['network_total'].set_value(metrics.get('network_total_mbps', 0.0), decimals=2)
        
        # FPS
        if 'fps' in self.metric_widgets:
            fps = metrics.get('fps')
            self.metric_widgets['fps'].set_value(fps, decimals=0) if fps is not None else \
                self.metric_widgets['fps'].set_value(None, text="N/A")
        
        # Fan speeds
        fan_speeds = metrics.get('fan_speeds', [])
        cpu_fan_rpm = None
        gpu_fan_rpm = None
        for fan in fan_speeds:
            name = fan.get('name', '').upper()
            if name == 'CPU':
                cpu_fan_rpm = fan.get('rpm')
            elif name == 'GPU':
                gpu_fan_rpm = fan.get('rpm')
        
        if 'cpu_fan_gauge' in self.metric_widgets:
            self.metric_widgets['cpu_fan_gauge'].set_rpm(cpu_fan_rpm)
            # Set profile name
            try:
                from ..control.asusctl_interface import Profile
                current_profile = self.asusctl.get_current_profile() or Profile.BALANCED
                self.metric_widgets['cpu_fan_gauge'].set_profile_name(current_profile.value)
            except:
                pass
        
        if 'gpu_fan_gauge' in self.metric_widgets:
            self.metric_widgets['gpu_fan_gauge'].set_rpm(gpu_fan_rpm)
            try:
                from ..control.asusctl_interface import Profile
                current_profile = self.asusctl.get_current_profile() or Profile.BALANCED
                self.metric_widgets['gpu_fan_gauge'].set_profile_name(current_profile.value)
            except:
                pass
        
        # Update graph
        if hasattr(self, 'graph_widget'):
            self.graph_widget.update_data(history)

