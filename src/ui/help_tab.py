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
from .ui_scaling import UIScaling


class HelpTab(QWidget):
    """Tab displaying comprehensive help documentation."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Base sizes for scaling
        self._base_title_font_size = 24
        self._base_layout_margins = (30, 30, 30, 30)
        self._base_layout_spacing = 20
        self.setup_ui()
        self.update_scaling()
    
    def setup_ui(self):
        """Set up the UI."""
        # Apply game-style theme
        self.setStyleSheet(GAME_STYLES['widget'])
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        self.title_label = QLabel("Help & Documentation")
        self.title_label.setStyleSheet(f"color: {GAME_COLORS['accent_blue']}; margin-bottom: 10px;")
        layout.addWidget(self.title_label)
        
        # Create internal tab widget for help sections
        tabs = QTabWidget()
        tabs.setStyleSheet(GAME_STYLES['tab_widget'])
        
        # Add help content tabs
        tabs.addTab(self._create_getting_started_tab(), "Getting Started")
        tabs.addTab(self._create_dashboard_help_tab(), "Dashboard")
        tabs.addTab(self._create_fan_curves_help_tab(), "Fan Curves")
        tabs.addTab(self._create_apply_profiles_help_tab(), "Apply Profiles")
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
    
    def update_scaling(self):
        """Update widget scaling based on window size."""
        window = self.window()
        if not window:
            return
        
        scale = UIScaling.get_scale_factor(window)
        
        # Update title font
        if hasattr(self, 'title_label'):
            title_font = UIScaling.scale_font(self._base_title_font_size, window, scale)
            title_font.setBold(True)
            self.title_label.setFont(title_font)
        
        # Update layout margins and spacing
        layout = self.layout()
        if layout:
            margins = tuple(UIScaling.scale_size(m, window, scale) for m in self._base_layout_margins)
            layout.setContentsMargins(*margins)
            layout.setSpacing(UIScaling.scale_size(self._base_layout_spacing, window, scale))
    
    def resizeEvent(self, event):
        """Handle resize to update scaling."""
        super().resizeEvent(event)
        self.update_scaling()
    
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
            <li>Apply profiles to different ASUS power profiles (Balanced, Quiet, Performance)</li>
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
            <li><strong>Fan Curve Designer:</strong> Design, load, and save fan curve configurations</li>
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
        <h2 style="color: #00BCD4;">Fan Curve Designer</h2>
        
        <h3>🌡️ What is a Fan Curve?</h3>
        <p>A fan curve defines how fast your laptop fans should spin at different temperatures. 
        The graph shows temperature (X-axis) vs fan speed percentage (Y-axis).</p>
        
        <h3>🎨 Designer Workflow</h3>
        <p>The Fan Curve Designer is focused on <strong>designing, loading, and saving</strong> fan curves. 
        To apply designed curves to your system, use a different screen (coming soon).</p>
        
        <h3>🎛️ Using the Designer</h3>
        
        <h4>1. Selecting a Fan</h4>
        <p>Use the buttons at the top to select which fan you want to design for:</p>
        <ul>
            <li><strong>CPU Fan:</strong> Controls the CPU cooling fan</li>
            <li><strong>GPU Fan:</strong> Controls the graphics card fan</li>
        </ul>
        
        <h4>2. Loading Curves</h4>
        <p><strong>Load Presets:</strong> Click "Quiet", "Balanced", or "Performance" buttons to load preset curves</p>
        <p><strong>Load Saved Profile:</strong> Select a profile from the "Saved Profile" dropdown to load a previously saved curve</p>
        <p><strong>Reset:</strong> Click "Reset to Original" to restore the curve to when it was first loaded</p>
        
        <h4>3. Editing Points</h4>
        <p><strong>To select a point:</strong> Click on any control point (blue circles) on the graph</p>
        <p><strong>To add a new point:</strong> Enter temperature and fan speed values, then click "Add Point"</p>
        <p><strong>To update a point:</strong> Select it, change values, then click "Update Selected"</p>
        <p><strong>To remove a point:</strong> Select it and click "Remove Selected" (must have at least 2 points)</p>
        
        <h3>💾 Saving Curves</h3>
        <p><strong>Save Curve:</strong> Saves to the currently loaded profile (if one is loaded)</p>
        <p><strong>Save As:</strong> Always prompts for a new profile name to save your curve</p>
        
        <h3>🔒 Active Curve Protection</h3>
        <p>If you try to save over a curve that is currently applied to your system, you'll be prompted to:</p>
        <ul>
            <li><strong>Save As:</strong> Save with a new name (recommended)</li>
            <li><strong>Discard:</strong> Discard your changes and restore the original curve</li>
            <li><strong>Cancel:</strong> Cancel the save operation</li>
        </ul>
        <p>This prevents accidentally modifying curves that are currently in use.</p>
        
        <h3>📐 Curve Validation</h3>
        <p>The designer automatically validates your curves:</p>
        <ul>
            <li>Fan speeds must increase as temperature increases (monotonic)</li>
            <li>You must have at least 2 points in the curve</li>
            <li>Temperature range: 30-90°C</li>
            <li>Fan speed range: 0-100%</li>
        </ul>
        """
        return self._create_scrollable_content(content)
    
    def _create_apply_profiles_help_tab(self) -> QWidget:
        """Create apply profiles help content."""
        content = """
        <h2 style="color: #00BCD4;">Apply Profiles</h2>
        
        <h3>🎯 What is Apply Profiles?</h3>
        <p>The Apply Profiles screen allows you to apply saved fan curve profiles to your system. 
        After designing curves in the Fan Curve Designer, you can apply them to specific ASUS power profiles 
        (Balanced, Quiet, or Performance).</p>
        
        <h3>📋 How to Apply a Profile</h3>
        <ol>
            <li><strong>Select a Profile:</strong> Choose a saved profile from the list on the left</li>
            <li><strong>Choose ASUS Profile:</strong> Select which ASUS power profile (Balanced, Quiet, or Performance) to apply the curves to</li>
            <li><strong>Review Details:</strong> Check the profile info to see which curves (CPU/GPU) are included</li>
            <li><strong>Apply:</strong> Click the "Apply Profile" button to apply the curves to your system</li>
        </ol>
        
        <h3>⚙️ ASUS Power Profiles</h3>
        <p>ASUS laptops have three power profiles, each with separate fan curve settings:</p>
        <ul>
            <li><strong>Balanced:</strong> Default profile for general use</li>
            <li><strong>Quiet:</strong> Optimized for low noise (slower fans)</li>
            <li><strong>Performance:</strong> Optimized for maximum cooling (faster fans)</li>
        </ul>
        <p>You can apply different fan curve profiles to each ASUS power profile. The curves will activate when you switch to that power profile.</p>
        
        <h3>📊 Current Status Display</h3>
        <p>The status panel shows:</p>
        <ul>
            <li>Currently active ASUS power profile</li>
            <li>Which fan curves are currently applied (CPU and GPU)</li>
            <li>Whether fan curves are enabled or disabled</li>
        </ul>
        <p>The status updates automatically every 2 seconds to show the current system state.</p>
        
        <h3>⚠️ Important Notes</h3>
        <ul>
            <li>Applying a profile will replace any existing curves for the selected ASUS profile</li>
            <li>Fan curves must be enabled for the ASUS profile (done automatically when applying)</li>
            <li>You need to switch to the target ASUS power profile for the curves to take effect</li>
            <li>Changes are saved persistently and will survive reboots</li>
        </ul>
        
        <h3>💡 Workflow</h3>
        <p><strong>Complete workflow:</strong></p>
        <ol>
            <li>Design curves in <strong>Fan Curve Designer</strong></li>
            <li>Save your design as a profile</li>
            <li>Switch to <strong>Apply Profiles</strong> tab</li>
            <li>Select your profile and choose an ASUS power profile</li>
            <li>Click "Apply Profile" to activate the curves</li>
            <li>Switch your ASUS power profile to the target profile to use the curves</li>
        </ol>
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

