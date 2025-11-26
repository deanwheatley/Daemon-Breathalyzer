#!/usr/bin/env python3
"""
Log Viewer Tab

UI component for displaying and filtering system logs.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QLineEdit, QPlainTextEdit, QGroupBox, QComboBox,
    QScrollArea, QMessageBox, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QTextCursor

from ..monitoring.log_monitor import LogMonitor, LogEntry, LogPriority
from .game_style_theme import GAME_COLORS, GAME_STYLES


class LogViewerTab(QWidget):
    """Tab for viewing and filtering system logs."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_monitor = LogMonitor(update_interval=1.0, max_entries=2000)
        self.log_monitor.on_new_entry = self._on_new_entry
        self.log_monitor.on_error = self._on_error
        
        self.setup_ui()
        self.log_monitor.start()
        
        # Refresh sources periodically
        self.source_refresh_timer = QTimer(self)
        self.source_refresh_timer.timeout.connect(self.refresh_source_list)
        self.source_refresh_timer.start(30000)  # Every 30 seconds
    
    def setup_ui(self):
        """Set up the UI."""
        # Apply game-style theme
        self.setStyleSheet(GAME_STYLES['widget'])
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("System Log Monitor")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setWeight(QFont.Weight.DemiBold)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {GAME_COLORS['accent_blue']};")
        layout.addWidget(title)
        
        # Main content area (split view)
        content_layout = QHBoxLayout()
        
        # Left panel: Filters
        filter_panel = self._create_filter_panel()
        filter_panel.setMaximumWidth(300)
        content_layout.addWidget(filter_panel)
        
        # Right panel: Log viewer
        viewer_panel = self._create_viewer_panel()
        content_layout.addWidget(viewer_panel, stretch=1)
        
        layout.addLayout(content_layout)
        
        # Error summary bar
        self.error_summary = self._create_error_summary()
        layout.addWidget(self.error_summary)
    
    def _create_filter_panel(self) -> QWidget:
        """Create the filter panel."""
        panel = QGroupBox("Filters")
        panel.setStyleSheet(GAME_STYLES['groupbox'])
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # Priority filters
        priority_label = QLabel("Priority:")
        priority_label.setStyleSheet(f"color: {GAME_COLORS['text_secondary']}; font-weight: bold;")
        layout.addWidget(priority_label)
        
        self.priority_checkboxes = {}
        for priority in LogPriority:
            checkbox = QCheckBox(priority.name)
            checkbox.setChecked(True)
            checkbox.setStyleSheet(f"""
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
            checkbox.stateChanged.connect(self._on_filter_changed)
            self.priority_checkboxes[priority] = checkbox
            layout.addWidget(checkbox)
        
        layout.addSpacing(10)
        
        # Source filters
        source_label = QLabel("Sources:")
        source_label.setStyleSheet(f"color: {GAME_COLORS['text_secondary']}; font-weight: bold;")
        layout.addWidget(source_label)
        
        self.source_combo = QComboBox()
        self.source_combo.setEditable(True)
        self.source_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.source_combo.setStyleSheet(GAME_STYLES['combobox'])
        self.source_combo.lineEdit().setPlaceholderText("All sources")
        self.source_combo.currentTextChanged.connect(self._on_filter_changed)
        layout.addWidget(self.source_combo)
        
        # Time range
        time_label = QLabel("Time Range:")
        time_label.setStyleSheet(f"color: {GAME_COLORS['text_secondary']}; font-weight: bold;")
        layout.addWidget(time_label)
        
        self.time_range_group = QButtonGroup(self)
        time_ranges = [
            ("Last hour", 1),
            ("Last 24 hours", 24),
            ("Last week", 168),
            ("All", None)
        ]
        
        for text, hours in time_ranges:
            radio = QRadioButton(text)
            if hours == 1:
                radio.setChecked(True)
            self.time_range_group.addButton(radio)
            radio.clicked.connect(self._on_time_range_changed)
            layout.addWidget(radio)
        
        layout.addSpacing(10)
        
        # Text search
        search_label = QLabel("Search:")
        search_label.setStyleSheet(f"color: {GAME_COLORS['text_secondary']}; font-weight: bold;")
        layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search log messages...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {GAME_COLORS['bg_card']};
                color: {GAME_COLORS['text_primary']};
                border: 2px solid {GAME_COLORS['border']};
                border-radius: 6px;
                padding: 4px;
            }}
            QLineEdit:hover {{
                border: 2px solid {GAME_COLORS['accent_blue']};
            }}
        """)
        self.search_input.textChanged.connect(self._on_filter_changed)
        layout.addWidget(self.search_input)
        
        layout.addSpacing(10)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("Clear Filters")
        self.clear_btn.setStyleSheet(GAME_STYLES['button'])
        self.clear_btn.clicked.connect(self._clear_filters)
        control_layout.addWidget(self.clear_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setStyleSheet(GAME_STYLES['button'])
        self.refresh_btn.clicked.connect(self._refresh_logs)
        control_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(control_layout)
        
        layout.addStretch()
        
        return panel
    
    def _create_viewer_panel(self) -> QWidget:
        """Create the log viewer panel."""
        panel = QGroupBox("Log Viewer")
        panel.setStyleSheet(GAME_STYLES['groupbox'])
        layout = QVBoxLayout(panel)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setCheckable(True)
        self.pause_btn.setStyleSheet(GAME_STYLES['button'])
        self.pause_btn.clicked.connect(self._toggle_pause)
        controls_layout.addWidget(self.pause_btn)
        
        self.autoscroll_btn = QPushButton("📜 Auto-scroll")
        self.autoscroll_btn.setCheckable(True)
        self.autoscroll_btn.setChecked(True)
        self.autoscroll_btn.setStyleSheet(GAME_STYLES['button'])
        controls_layout.addWidget(self.autoscroll_btn)
        
        self.clear_logs_btn = QPushButton("🗑️ Clear")
        self.clear_logs_btn.setStyleSheet(GAME_STYLES['button'])
        self.clear_logs_btn.clicked.connect(self._clear_logs)
        controls_layout.addWidget(self.clear_logs_btn)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Log display with game-style dark theme
        self.log_display = QPlainTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Monospace", 9))
        self.log_display.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {GAME_COLORS['bg_dark']};
                color: {GAME_COLORS['text_primary']};
                border: 2px solid {GAME_COLORS['border']};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(self.log_display)
        
        return panel
    
    def _create_error_summary(self) -> QWidget:
        """Create error summary bar."""
        panel = QWidget()
        panel.setStyleSheet(f"""
            background-color: {GAME_COLORS['bg_card']};
            border: 2px solid {GAME_COLORS['border']};
            border-radius: 6px;
            padding: 10px;
        """)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(15, 8, 15, 8)
        
        self.summary_label = QLabel("Error Summary: Loading...")
        self.summary_label.setStyleSheet(f"color: {GAME_COLORS['text_secondary']};")
        layout.addWidget(self.summary_label)
        
        layout.addStretch()
        
        # Update summary periodically
        self.summary_timer = QTimer(self)
        self.summary_timer.timeout.connect(self._update_error_summary)
        self.summary_timer.start(5000)  # Every 5 seconds
        self._update_error_summary()
        
        return panel
    
    def _on_new_entry(self, entry: LogEntry):
        """Handle new log entry."""
        if not self.pause_btn.isChecked():
            self._append_entry(entry)
            
            # Auto-scroll if enabled
            if self.autoscroll_btn.isChecked():
                scrollbar = self.log_display.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
    
    def _on_error(self, error_message: str):
        """Handle monitoring error."""
        QMessageBox.warning(self, "Log Monitoring Error", error_message)
    
    def _append_entry(self, entry: LogEntry):
        """Append a log entry to the display."""
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Format entry with color
        text = entry.to_display_string() + "\n"
        
        # Apply color based on priority
        format = QTextCharFormat()
        color = QColor(entry.priority.color_code())
        format.setForeground(color)
        
        # Background color for critical
        bg_color = entry.priority.bg_color_code()
        if bg_color:
            format.setBackground(QColor(bg_color))
            format.setForeground(QColor('#FFFFFF'))
        
        cursor.insertText(text, format)
        
        # Limit displayed entries
        document = self.log_display.document()
        block_count = document.blockCount()
        if block_count > self.log_monitor.max_entries:
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.KeepAnchor, block_count - self.log_monitor.max_entries)
            cursor.removeSelectedText()
    
    def _on_filter_changed(self):
        """Handle filter changes."""
        # Update priority filter
        priorities = [
            priority for priority, checkbox in self.priority_checkboxes.items()
            if checkbox.isChecked()
        ]
        self.log_monitor.set_priority_filter(priorities)
        
        # Update source filter
        source_text = self.source_combo.currentText()
        if source_text and source_text != "All sources":
            self.log_monitor.set_source_filter([source_text])
        else:
            self.log_monitor.set_source_filter([])
        
        # Update text filter
        search_text = self.search_input.text()
        self.log_monitor.set_text_filter(search_text)
        
        # Refresh display
        self._refresh_display()
    
    def _on_time_range_changed(self):
        """Handle time range filter change."""
        from datetime import datetime, timedelta
        
        checked_radio = self.time_range_group.checkedButton()
        if not checked_radio:
            return
        
        text = checked_radio.text()
        if text == "All":
            self.log_monitor.set_time_range_filter(None, None)
        elif text == "Last hour":
            start = datetime.now() - timedelta(hours=1)
            self.log_monitor.set_time_range_filter(start, None)
        elif text == "Last 24 hours":
            start = datetime.now() - timedelta(hours=24)
            self.log_monitor.set_time_range_filter(start, None)
        elif text == "Last week":
            start = datetime.now() - timedelta(hours=168)
            self.log_monitor.set_time_range_filter(start, None)
        
        self._refresh_display()
    
    def _toggle_pause(self, checked: bool):
        """Toggle pause state."""
        if checked:
            self.log_monitor.pause()
            self.pause_btn.setText("▶ Resume")
        else:
            self.log_monitor.resume()
            self.pause_btn.setText("⏸ Pause")
    
    def _clear_logs(self):
        """Clear log display."""
        self.log_display.clear()
    
    def _clear_filters(self):
        """Clear all filters."""
        # Reset checkboxes
        for checkbox in self.priority_checkboxes.values():
            checkbox.setChecked(True)
        
        self.source_combo.setCurrentIndex(0)
        self.search_input.clear()
        
        # Check "Last hour" radio
        for button in self.time_range_group.buttons():
            if button.text() == "Last hour":
                button.setChecked(True)
                break
        
        self.log_monitor.clear_filters()
        self._refresh_display()
    
    def _refresh_logs(self):
        """Refresh logs from monitor."""
        self.log_monitor._load_initial_logs()
        self._refresh_display()
    
    def _refresh_display(self):
        """Refresh the log display with filtered entries."""
        self.log_display.clear()
        
        entries = self.log_monitor.get_filtered_entries()
        for entry in entries[-1000:]:  # Show last 1000 filtered entries
            self._append_entry(entry)
        
        # Auto-scroll
        if self.autoscroll_btn.isChecked():
            scrollbar = self.log_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def _update_error_summary(self):
        """Update error summary display."""
        summary = self.log_monitor.get_error_summary()
        text = (
            f"Total Errors: {summary['total_errors']} | "
            f"Critical: {summary['recent_critical_1h']} (1h) | "
            f"Errors: {summary['recent_errors_1h']} (1h) | "
            f"Warnings: {summary['warnings']}"
        )
        self.summary_label.setText(text)
    
    def refresh_source_list(self):
        """Refresh the list of available sources."""
        sources = self.log_monitor.get_available_sources()
        current_text = self.source_combo.currentText()
        
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        self.source_combo.addItem("All sources")
        for source in sources:
            self.source_combo.addItem(source)
        
        # Restore selection
        index = self.source_combo.findText(current_text)
        if index >= 0:
            self.source_combo.setCurrentIndex(index)
        self.source_combo.blockSignals(False)
    
    def closeEvent(self, event):
        """Clean up on close."""
        self.log_monitor.stop()
        event.accept()

