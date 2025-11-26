#!/usr/bin/env python3
"""
Help Tab

Comprehensive help documentation as a tab widget matching the game-style UI.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QTabWidget, QScrollArea
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QDesktopServices
from typing import Optional

from .game_style_theme import GAME_COLORS, GAME_STYLES


class HelpTab(QWidget):
    """Tab displaying comprehensive help documentation."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI."""
        # Apply game-style theme
        self.setStyleSheet(GAME_STYLES['widget'])
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Help & Documentation")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {GAME_COLORS['accent_blue']}; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Create internal tab widget for help sections
        tabs = QTabWidget()
        tabs.setStyleSheet(GAME_STYLES['tab_widget'])
        
        # Add help content tabs
        tabs.addTab(self._create_getting_started_tab(), "Getting Started")
        tabs.addTab(self._create_dashboard_help_tab(), "Dashboard")
        tabs.addTab(self._create_fan_curves_help_tab(), "Fan Curves")
        tabs.addTab(self._create_troubleshooting_tab(), "Troubleshooting")
        
        layout.addWidget(tabs)
    
    def _create_scrollable_content(self, content: str) -> QWidget:
        """Create a scrollable content widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(content)
        text_edit.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {GAME_COLORS['border']};
                border-radius: 8px;
                background-color: {GAME_COLORS['bg_card']};
                color: {GAME_COLORS['text_primary']};
                font-size: 12pt;
                padding: 15px;
            }}
        """)
        
        layout.addWidget(text_edit)
        return widget
    
    def _create_getting_started_tab(self) -> QWidget:
        """Create getting started help content."""
        content = """
        <h2 style="color: #00BCD4;">Welcome to Daemon Breathalyzer</h2>
        
        <h3>📋 What is This Application?</h3>
        <p>Daemon Breathalyzer is a modern GUI application that helps you:</p>
        <ul>
            <li>Monitor your system's CPU, GPU, memory, and temperatures in real-time</li>
            <li>Configure custom fan curves for your ASUS laptop</li>
            <li>Save and manage fan curve profiles</li>
        </ul>
        
        <h3>🚀 First Launch</h3>
        <p>When you first launch the application:</p>
        <ol>
            <li><strong>Dependency Check:</strong> The app automatically checks for required dependencies</li>
            <li><strong>Installation Guide:</strong> If anything is missing, a dialog will show with installation instructions</li>
            <li><strong>Auto-Install:</strong> Many dependencies can be installed automatically with one click</li>
        </ol>
        
        <h3>📊 Main Window Overview</h3>
        <p>The application has several tabs:</p>
        <ul>
            <li><strong>Dashboard:</strong> View real-time system metrics and graphs</li>
            <li><strong>Fan Curves:</strong> Edit and apply fan curve configurations</li>
            <li><strong>Fan Status:</strong> Visual representation of fan curves and current status</li>
            <li><strong>Test Fans:</strong> Manually test and control individual fans</li>
            <li><strong>System Logs:</strong> View and filter system logs</li>
            <li><strong>History:</strong> View historical system monitoring data</li>
        </ul>
        
        <h3>💡 Quick Tips</h3>
        <ul>
            <li>All metrics update automatically every second</li>
            <li>Click on control points in the fan curve editor to select them</li>
            <li>Use preset buttons for quick fan curve configurations</li>
            <li>Enable Test Mode in Test Fans tab to manually control fan speeds</li>
        </ul>
        """
        return self._create_scrollable_content(content)
    
    def _create_dashboard_help_tab(self) -> QWidget:
        """Create dashboard help content."""
        content = """
        <h2 style="color: #00BCD4;">Dashboard - System Monitoring</h2>
        
        <h3>📊 Real-Time Metrics</h3>
        <p>The Dashboard tab displays live information about your system:</p>
        
        <h4>CPU Metrics</h4>
        <ul>
            <li><strong>CPU Usage:</strong> Overall CPU utilization percentage</li>
            <li><strong>CPU Temperature:</strong> Current CPU temperature in Celsius</li>
            <li><strong>CPU Frequency:</strong> Current CPU clock speed in MHz</li>
        </ul>
        
        <h4>Memory Metrics</h4>
        <ul>
            <li><strong>Memory:</strong> RAM usage percentage</li>
            <li><strong>Memory Used:</strong> Amount of RAM currently in use (GB)</li>
        </ul>
        
        <h4>GPU Metrics (if available)</h4>
        <ul>
            <li><strong>GPU Usage:</strong> Graphics card utilization percentage</li>
            <li><strong>GPU Temperature:</strong> Graphics card temperature in Celsius</li>
            <li><strong>GPU Memory:</strong> Graphics memory usage percentage</li>
        </ul>
        
        <h4>Network Metrics</h4>
        <ul>
            <li><strong>Network Sent:</strong> Data sent in Mbps</li>
            <li><strong>Network Received:</strong> Data received in Mbps</li>
            <li><strong>Network Total:</strong> Total network bandwidth in Mbps</li>
        </ul>
        
        <h3>📈 Historical Graphs</h3>
        <p>The graph shows historical data for system metrics over time. You can resize and show/hide the chart using the preferences button.</p>
        
        <h3>⚙ Preferences</h3>
        <p>Click the Preferences button to show or hide specific meters on the dashboard. Your preferences are saved automatically.</p>
        """
        return self._create_scrollable_content(content)
    
    def _create_fan_curves_help_tab(self) -> QWidget:
        """Create fan curves help content."""
        content = """
        <h2 style="color: #00BCD4;">Fan Curves - Configuration Editor</h2>
        
        <h3>🌡️ What is a Fan Curve?</h3>
        <p>A fan curve defines how fast your laptop fans should spin at different temperatures. 
        The graph shows temperature (X-axis) vs fan speed percentage (Y-axis).</p>
        
        <h3>🎛️ Using the Editor</h3>
        
        <h4>1. Selecting a Fan</h4>
        <p>Use the buttons at the top to select which fan you want to configure:</p>
        <ul>
            <li><strong>CPU Fan:</strong> Controls the CPU cooling fan</li>
            <li><strong>GPU Fan:</strong> Controls the graphics card fan</li>
        </ul>
        
        <h4>2. Editing Points</h4>
        <p><strong>To select a point:</strong> Click on any control point (blue circles) on the graph</p>
        <p><strong>To add a new point:</strong> Enter temperature and fan speed values, then click "Add Point"</p>
        <p><strong>To update a point:</strong> Select it, change values, then click "Update Selected"</p>
        <p><strong>To remove a point:</strong> Select it and click "Remove Selected" (must have at least 2 points)</p>
        
        <h3>🎯 Preset Curves</h3>
        <p>Quick apply buttons for common configurations:</p>
        <ul>
            <li><strong>Balanced:</strong> Balanced cooling and noise (default)</li>
            <li><strong>Loudmouth:</strong> Maximum fan speed at low temperatures</li>
            <li><strong>Shush:</strong> Very quiet, low fan speeds</li>
        </ul>
        
        <h3>✅ Applying Changes</h3>
        <p>Click the "Apply" button to save and apply your fan curve configuration. The curve will persist across reboots.</p>
        
        <h3>🧪 Testing Fans</h3>
        <p>Use the "Test Fan" button to temporarily set fan speed to 100% for 5 seconds to verify fan operation.</p>
        """
        return self._create_scrollable_content(content)
    
    def _create_troubleshooting_tab(self) -> QWidget:
        """Create troubleshooting help content."""
        content = """
        <h2 style="color: #00BCD4;">Troubleshooting</h2>
        
        <h3>🔧 Dependency Issues</h3>
        <p>From the Help menu, select "Check Dependencies" to see what's installed and what's missing.</p>
        
        <h3>🌡️ Temperature Not Showing</h3>
        <p><strong>Solution:</strong> Install lm-sensors</p>
        <code>sudo apt install lm-sensors</code><br/>
        <code>sudo sensors-detect</code>
        
        <h3>🎮 GPU Metrics Not Showing</h3>
        <p><strong>Solution:</strong> Verify NVIDIA drivers are installed</p>
        <code>nvidia-smi</code>
        
        <h3>🌪️ Fan Curves Not Working</h3>
        <p><strong>Check asusctl:</strong></p>
        <code>asusctl --version</code><br/>
        <code>sudo systemctl status asusd</code><br/>
        <code>sudo systemctl enable --now asusd</code>
        
        <h3>🆘 Still Having Issues?</h3>
        <p>Check Help → Check Dependencies to verify all requirements are installed.</p>
        """
        return self._create_scrollable_content(content)

