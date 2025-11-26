#!/usr/bin/env python3
"""
Help Documentation Dialog

Comprehensive help documentation accessible from the Help menu.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QTabWidget, QWidget, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class HelpDialog(QDialog):
    """Help documentation dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help - Daemon Breathalyzer")
        self.setMinimumSize(900, 700)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                background: white;
            }
            QTabBar::tab {
                background: #f5f5f5;
                color: #666;
                padding: 10px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background: white;
                color: #2196F3;
                font-weight: bold;
            }
        """)
        
        # Getting Started tab
        tabs.addTab(self._create_getting_started_tab(), "Getting Started")
        
        # Dashboard tab
        tabs.addTab(self._create_dashboard_help_tab(), "Dashboard")
        
        # Fan Curves tab
        tabs.addTab(self._create_fan_curves_help_tab(), "Fan Curves")
        
        # Profiles tab
        tabs.addTab(self._create_profiles_help_tab(), "Profiles")
        
        # Troubleshooting tab
        tabs.addTab(self._create_troubleshooting_tab(), "Troubleshooting")
        
        layout.addWidget(tabs)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px 24px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        layout.setContentsMargins(0, 0, 10, 10)
    
    def _create_scrollable_content(self, content: str) -> QWidget:
        """Create a scrollable content widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(content)
        text_edit.setStyleSheet("""
            QTextEdit {
                border: none;
                background: white;
                font-size: 11pt;
            }
        """)
        
        layout.addWidget(text_edit)
        return widget
    
    def _create_getting_started_tab(self) -> QWidget:
        """Create getting started help content."""
        content = """
        <h2>Welcome to Daemon Breathalyzer</h2>
        
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
        <p>The application has four main tabs:</p>
        <ul>
            <li><strong>Dashboard:</strong> View real-time system metrics and graphs</li>
            <li><strong>Fan Curve Designer:</strong> Design, load, and save fan curve configurations</li>
            <li><strong>Profiles:</strong> Save and manage your fan curve profiles</li>
            <li><strong>Settings:</strong> Application preferences (coming soon)</li>
        </ul>
        
        <h3>💡 Quick Tips</h3>
        <ul>
            <li>All metrics update automatically every second</li>
            <li>Click on control points in the fan curve editor to select them</li>
            <li>Use preset buttons for quick fan curve configurations</li>
            <li>Double-click a profile in the Profiles tab to load it</li>
        </ul>
        
        <h3>🆘 Need More Help?</h3>
        <p>Check the other tabs in this help dialog for detailed information about each feature.</p>
        """
        return self._create_scrollable_content(content)
    
    def _create_dashboard_help_tab(self) -> QWidget:
        """Create dashboard help content."""
        content = """
        <h2>Dashboard - System Monitoring</h2>
        
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
        
        <h3>📈 Historical Graphs</h3>
        <p>The graph at the bottom shows historical data for:</p>
        <ul>
            <li>CPU usage percentage over time</li>
            <li>CPU temperature over time</li>
            <li>Memory usage percentage over time</li>
            <li>GPU usage and temperature (if available)</li>
        </ul>
        <p><strong>Data retention:</strong> The graph shows the last 5 minutes of data (300 data points collected every second).</p>
        
        <h3>🎨 Understanding the Display</h3>
        <ul>
            <li><strong>Metric Cards:</strong> Color-coded cards show key metrics at a glance</li>
            <li><strong>Status Bar:</strong> Bottom bar shows a summary of current system state</li>
            <li><strong>Real-Time Updates:</strong> All metrics update every second automatically</li>
        </ul>
        
        <h3>⚠️ Missing Data</h3>
        <p>If some metrics show "N/A":</p>
        <ul>
            <li><strong>Temperature:</strong> May require installing <code>lm-sensors</code></li>
            <li><strong>GPU Metrics:</strong> Requires NVIDIA drivers and GPU monitoring tools</li>
            <li>Check the Troubleshooting tab for solutions</li>
        </ul>
        """
        return self._create_scrollable_content(content)
    
    def _create_fan_curves_help_tab(self) -> QWidget:
        """Create fan curves help content."""
        content = """
        <h2>Fan Curve Designer</h2>
        
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
        <p><strong>To select a point:</strong></p>
        <ul>
            <li>Click on any control point (blue circles) on the graph</li>
            <li>The point will be highlighted, and its values shown in the control panel</li>
        </ul>
        
        <p><strong>To add a new point:</strong></p>
        <ol>
            <li>Enter temperature and fan speed values in the control panel</li>
            <li>Click "Add Point" button</li>
            <li>The point will appear on the curve</li>
        </ol>
        
        <p><strong>To update a point:</strong></p>
        <ol>
            <li>Select an existing point</li>
            <li>Change the temperature or fan speed values</li>
            <li>Click "Update Selected" button</li>
        </ol>
        
        <p><strong>To remove a point:</strong></p>
        <ol>
            <li>Select the point you want to remove</li>
            <li>Click "Remove Selected" button</li>
            <li>Note: You must have at least 2 points in the curve</li>
        </ol>
        
        <h3>💾 Saving Curves</h3>
        <p><strong>Save Curve:</strong> Saves to the currently loaded profile (if one is loaded). If no profile is loaded, prompts for "Save As".</p>
        <p><strong>Save As:</strong> Always prompts for a new profile name to save your curve with.</p>
        
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
    
    def _create_profiles_help_tab(self) -> QWidget:
        """Create profiles help content."""
        content = """
        <h2>Profiles - Fan Curve Management</h2>
        
        <h3>💾 What are Profiles?</h3>
        <p>Profiles let you save and quickly switch between different fan curve configurations. 
        This is useful for different scenarios like gaming, office work, or battery saving.</p>
        
        <h3>💾 Saving Profiles</h3>
        <ol>
            <li>Go to the <strong>Fan Curve Designer</strong> tab</li>
            <li>Design your desired fan curves</li>
            <li>Click "Save Curve" or "Save As" to save your design</li>
            <li>Enter a profile name and optional description</li>
            <li>Click "OK" to save</li>
        </ol>
        <p><strong>Note:</strong> You can also save directly in the Fan Curve Designer using the Save buttons.</p>
        
        <h3>📂 Loading Profiles</h3>
        <p><strong>Method 1: From Fan Curve Designer</strong></p>
        <ul>
            <li>Go to the Fan Curve Designer tab</li>
            <li>Select a profile from the "Saved Profile" dropdown</li>
            <li>The curve will be loaded into the designer</li>
        </ul>
        
        <p><strong>Method 2: From Profile Manager</strong></p>
        <ul>
            <li>Double-click any profile in the list, or</li>
            <li>Select a profile and click "Load"</li>
            <li>The profile will be loaded into the Fan Curve Designer</li>
        </ul>
        
        <p><strong>Note:</strong> Loading a profile loads it into the designer. To apply it to your system, use a different screen (coming soon).</p>
        
        <h3>🗑️ Deleting Profiles</h3>
        <ol>
            <li>Select the profile you want to delete</li>
            <li>Click "Delete" button</li>
            <li>Confirm the deletion</li>
        </ol>
        <p><strong>Warning:</strong> This action cannot be undone!</p>
        
        <h3>📤 Exporting Profiles</h3>
        <p>Export profiles to share with others or create backups:</p>
        <ol>
            <li>Select the profile you want to export</li>
            <li>Click "Export Profile" button</li>
            <li>Choose save location and format (JSON or YAML)</li>
            <li>Click "Save"</li>
        </ol>
        
        <h3>📥 Importing Profiles</h3>
        <p>Import profiles from files:</p>
        <ol>
            <li>Click "Import Profile" button</li>
            <li>Select the profile file (JSON or YAML format)</li>
            <li>The profile will be imported and added to your list</li>
        </ol>
        
        <h3>📁 Profile Storage</h3>
        <p>Profiles are stored in:</p>
        <code>~/.config/asus-control/profiles/</code>
        <p>Each profile is saved as a JSON file. You can manually edit these files if needed, 
        but it's recommended to use the application's interface.</p>
        
        <h3>💡 Profile Tips</h3>
        <ul>
            <li>Use descriptive names like "Gaming Mode" or "Quiet Office"</li>
            <li>Add descriptions to remember what each profile is for</li>
            <li>Export important profiles as backups</li>
            <li>You can import profiles shared by others</li>
        </ul>
        """
        return self._create_scrollable_content(content)
    
    def _create_troubleshooting_tab(self) -> QWidget:
        """Create troubleshooting help content."""
        content = """
        <h2>Troubleshooting</h2>
        
        <h3>🔧 Dependency Issues</h3>
        
        <h4>Check Dependencies</h4>
        <p>From the Help menu, select "Check Dependencies" to see what's installed and what's missing.</p>
        
        <h4>Missing Python Packages</h4>
        <p>If Python packages are missing:</p>
        <ol>
            <li>Open Help → Check Dependencies</li>
            <li>Click "Install via pip" buttons for automatic installation</li>
            <li>Or install manually: <code>pip install -r requirements.txt</code></li>
        </ol>
        
        <h3>🌡️ Temperature Not Showing</h3>
        <p><strong>Problem:</strong> CPU or GPU temperature shows "N/A"</p>
        
        <p><strong>Solution 1: Install lm-sensors</strong></p>
        <ol>
            <li>Install: <code>sudo apt install lm-sensors</code></li>
            <li>Detect sensors: <code>sudo sensors-detect</code></li>
            <li>Answer "yes" to all questions</li>
            <li>Restart the application</li>
        </ol>
        
        <p><strong>Solution 2: Check thermal zones</strong></p>
        <p>Check if thermal sensors are available:</p>
        <code>ls /sys/class/thermal/</code>
        
        <h3>🎮 GPU Metrics Not Showing</h3>
        <p><strong>Problem:</strong> GPU usage, temperature, or memory shows "N/A"</p>
        
        <p><strong>Solution 1: Check NVIDIA drivers</strong></p>
        <ol>
            <li>Verify drivers are installed: <code>nvidia-smi</code></li>
            <li>If not installed, install NVIDIA drivers from your distribution's package manager</li>
        </ol>
        
        <p><strong>Solution 2: Install py3nvml (optional)</strong></p>
        <p>The app will fall back to nvidia-smi command, but py3nvml provides better integration:</p>
        <code>pip install py3nvml</code>
        
        <h3>🌪️ Fan Curves Not Working</h3>
        <p><strong>Problem:</strong> Can't edit fan curves or apply them</p>
        
        <p><strong>Check asusctl:</strong></p>
        <ol>
            <li>Verify asusctl is installed: <code>asusctl --version</code></li>
            <li>Check asusd service: <code>sudo systemctl status asusd</code></li>
            <li>Enable service if needed: <code>sudo systemctl enable --now asusd</code></li>
        </ol>
        
        <p><strong>Install asusctl:</strong></p>
        <p>See: <a href="https://asus-linux.org/asusctl/">https://asus-linux.org/asusctl/</a></p>
        <p>Or check Help → Check Dependencies for installation instructions</p>
        
        <h3>💾 Profile Issues</h3>
        
        <h4>Profiles Not Saving</h4>
        <ul>
            <li>Check that the profile name is not empty</li>
            <li>Ensure you have write permissions in your home directory</li>
            <li>Check disk space availability</li>
        </ul>
        
        <h4>Can't Import Profile</h4>
        <ul>
            <li>Verify the file is valid JSON or YAML format</li>
            <li>Check file permissions</li>
            <li>Ensure the profile file isn't corrupted</li>
        </ul>
        
        <h3>🖥️ Application Won't Start</h3>
        
        <p><strong>Check Python:</strong></p>
        <code>python3 --version</code>
        <p>Requires Python 3.8 or higher</p>
        
        <p><strong>Check Virtual Environment:</strong></p>
        <ul>
            <li>If using launcher script, it should handle this automatically</li>
            <li>If running manually, ensure venv is activated: <code>source venv/bin/activate</code></li>
        </ul>
        
        <p><strong>Check Dependencies:</strong></p>
        <p>Run Help → Check Dependencies to see what's missing</p>
        
        <h3>📊 Graphs Not Updating</h3>
        <p><strong>Problem:</strong> Graphs show no data or don't update</p>
        
        <p><strong>Solutions:</strong></p>
        <ul>
            <li>Wait a few seconds - graphs need data to accumulate</li>
            <li>Check that system monitoring is running (status bar should show "Monitoring active")</li>
            <li>Restart the application</li>
        </ul>
        
        <h3>🆘 Still Having Issues?</h3>
        <p>If you continue to experience problems:</p>
        <ul>
            <li>Check the error messages in the status bar</li>
            <li>Run Help → Check Dependencies to verify all requirements</li>
            <li>Check application logs (if available)</li>
            <li>Verify your system meets the prerequisites</li>
        </ul>
        """
        return self._create_scrollable_content(content)
    

