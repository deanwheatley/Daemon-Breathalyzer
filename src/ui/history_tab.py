#!/usr/bin/env python3
"""
History Tab

Displays historical system monitoring data in a detailed table view.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QComboBox, QDateTimeEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QDateTime, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime, timedelta
from typing import Dict, List

from ..monitoring.system_monitor import SystemMonitor
from .game_style_theme import GAME_COLORS, GAME_STYLES


class HistoryTab(QWidget):
    """Tab for viewing historical system monitoring data."""
    
    def __init__(self, monitor: SystemMonitor, parent=None):
        super().__init__(parent)
        self.monitor = monitor
        
        self.setup_ui()
        
        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_table)
        self.update_timer.start(2000)  # Update every 2 seconds
        
        # Initial update
        self.update_table()
    
    def setup_ui(self):
        """Set up the UI."""
        # Apply game-style theme
        self.setStyleSheet(GAME_STYLES['widget'])
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("System History")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setWeight(QFont.Weight.DemiBold)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {GAME_COLORS['accent_blue']};")
        layout.addWidget(title)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Metric selector
        metric_label = QLabel("Metric:")
        metric_label.setStyleSheet(f"color: {GAME_COLORS['text_secondary']};")
        controls_layout.addWidget(metric_label)
        
        self.metric_combo = QComboBox()
        self.metric_combo.setStyleSheet(GAME_STYLES['combobox'])
        self.metric_combo.addItems([
            "CPU Usage (%)",
            "CPU Temperature (°C)",
            "Memory Usage (%)",
            "GPU Usage (%)",
            "GPU Temperature (°C)"
        ])
        self.metric_combo.currentTextChanged.connect(self.update_table)
        self.metric_combo.setMinimumWidth(200)
        controls_layout.addWidget(self.metric_combo)
        
        controls_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet(GAME_STYLES['button'])
        refresh_btn.clicked.connect(self.update_table)
        controls_layout.addWidget(refresh_btn)
        
        layout.addLayout(controls_layout)
        
        # History table
        table_group = QGroupBox("Historical Data")
        table_group.setStyleSheet(GAME_STYLES['groupbox'])
        table_layout = QVBoxLayout(table_group)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(["Timestamp", "Value", "Delta"])
        
        # Style the table with game-style theme
        self.history_table.setStyleSheet(f"""
            QTableWidget {{
                border: 2px solid {GAME_COLORS['border']};
                border-radius: 4px;
                background-color: {GAME_COLORS['bg_card']};
                gridline-color: {GAME_COLORS['border']};
                color: {GAME_COLORS['text_primary']};
            }}
            QTableWidget::item {{
                padding: 8px;
                color: {GAME_COLORS['text_primary']};
            }}
            QTableWidget::item:selected {{
                background-color: {GAME_COLORS['accent_blue']};
                color: {GAME_COLORS['text_primary']};
            }}
            QHeaderView::section {{
                background-color: {GAME_COLORS['bg_medium']};
                color: {GAME_COLORS['accent_blue']};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {GAME_COLORS['border']};
                font-weight: bold;
            }}
        """)
        
        # Configure table
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        table_layout.addWidget(self.history_table)
        layout.addWidget(table_group)
        
        # Statistics panel
        stats_layout = QHBoxLayout()
        
        self.stats_group = QGroupBox("Statistics")
        self.stats_group.setStyleSheet(GAME_STYLES['groupbox'])
        stats_inner = QVBoxLayout(self.stats_group)
        
        self.stats_label = QLabel("Statistics will appear here")
        self.stats_label.setStyleSheet(f"color: {GAME_COLORS['text_secondary']};")
        stats_inner.addWidget(self.stats_label)
        
        stats_layout.addWidget(self.stats_group)
        layout.addLayout(stats_layout)
    
    def update_table(self):
        """Update the history table with current data."""
        history = self.monitor.get_history()
        
        if not history or not history.get('timestamp'):
            self.history_table.setRowCount(0)
            return
        
        # Get selected metric
        metric_name = self.metric_combo.currentText()
        metric_key = self._get_metric_key(metric_name)
        
        # Get data
        timestamps = list(history.get('timestamp', []))
        values = list(history.get(metric_key, []))
        
        if not timestamps or not values:
            self.history_table.setRowCount(0)
            self.stats_label.setText(f"No {metric_name} data available")
            return
        
        # Ensure same length
        min_len = min(len(timestamps), len(values))
        timestamps = timestamps[-min_len:]
        values = values[-min_len:]
        
        # Update table
        self.history_table.setRowCount(min_len)
        
        # Fill table (show most recent first)
        for i in range(min_len):
            idx = min_len - 1 - i  # Reverse order (newest first)
            
            # Timestamp
            timestamp = timestamps[idx]
            dt = datetime.fromtimestamp(timestamp)
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            time_item = QTableWidgetItem(time_str)
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.history_table.setItem(i, 0, time_item)
            
            # Value
            value = values[idx]
            if value is not None:
                if 'Temperature' in metric_name or '°C' in metric_name:
                    value_str = f"{value:.1f}°C"
                elif '%' in metric_name:
                    value_str = f"{value:.1f}%"
                else:
                    value_str = f"{value:.2f}"
                
                value_item = QTableWidgetItem(value_str)
                value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.history_table.setItem(i, 1, value_item)
                
                # Delta (change from previous)
                if i < min_len - 1:
                    prev_idx = min_len - 1 - (i + 1)
                    prev_value = values[prev_idx]
                    if prev_value is not None and value is not None:
                        delta = value - prev_value
                        if abs(delta) > 0.01:  # Only show if significant change
                            delta_str = f"{delta:+.2f}"
                            if 'Temperature' in metric_name or '°C' in metric_name:
                                delta_str = f"{delta:+.1f}°C"
                            elif '%' in metric_name:
                                delta_str = f"{delta:+.1f}%"
                        else:
                            delta_str = "—"
                        delta_item = QTableWidgetItem(delta_str)
                        delta_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        # Color code delta
                        if delta > 0:
                            delta_item.setForeground(Qt.GlobalColor.red)
                        elif delta < 0:
                            delta_item.setForeground(Qt.GlobalColor.green)
                        self.history_table.setItem(i, 2, delta_item)
                    else:
                        self.history_table.setItem(i, 2, QTableWidgetItem("—"))
                else:
                    self.history_table.setItem(i, 2, QTableWidgetItem("—"))
            else:
                self.history_table.setItem(i, 1, QTableWidgetItem("N/A"))
                self.history_table.setItem(i, 2, QTableWidgetItem("—"))
        
        # Update statistics
        valid_values = [v for v in values if v is not None]
        if valid_values:
            avg = sum(valid_values) / len(valid_values)
            min_val = min(valid_values)
            max_val = max(valid_values)
            
            stats_text = (
                f"<b>Statistics for {metric_name}:</b><br>"
                f"Average: {avg:.2f} | Min: {min_val:.2f} | Max: {max_val:.2f}<br>"
                f"Data points: {len(valid_values)}"
            )
            self.stats_label.setText(stats_text)
        else:
            self.stats_label.setText(f"No valid {metric_name} data available")
    
    def _get_metric_key(self, metric_name: str) -> str:
        """Convert metric display name to history key."""
        mapping = {
            "CPU Usage (%)": "cpu_percent",
            "CPU Temperature (°C)": "cpu_temp",
            "Memory Usage (%)": "memory_percent",
            "GPU Usage (%)": "gpu_utilization",
            "GPU Temperature (°C)": "gpu_temp"
        }
        return mapping.get(metric_name, "cpu_percent")


