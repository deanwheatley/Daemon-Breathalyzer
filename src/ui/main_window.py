#!/usr/bin/env python3
"""
Main Application Window

PyQt6 main window with dashboard for system monitoring.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QTabWidget, QPushButton, QStatusBar, QMenuBar, QMenu,
    QSystemTrayIcon, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QAction, QIcon, QPixmap, QPainter
from pathlib import Path

from ..monitoring.system_monitor import SystemMonitor
from .dashboard_widgets import MetricCard, GraphWidget
from .fan_speed_gauge import FanSpeedGauge
from .dependency_dialog import DependencyDialog
from .fan_curve_editor import FanCurveEditor
from .profile_manager_tab import ProfileManagerTab
from .about_tab import AboutTab
from ..control.asusctl_interface import AsusctlInterface, Profile
from ..control.profile_manager import ProfileManager
from .ui_scaling import UIScaling


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signal emitted when scale factor changes
    scale_changed = pyqtSignal(float)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Daemon Breathalyzer")
        self.setGeometry(100, 100, 1200, 800)
        self._current_scale = 1.0
        
        # Set window icon
        self._set_window_icon()
        
        # Game-style window styling (will be applied via theme)
        from .game_style_theme import GAME_STYLES
        self.setStyleSheet(GAME_STYLES['main_window'])
        
        # Initialize system monitor
        self.monitor = SystemMonitor(update_interval=1.0)
        self.monitor.start()
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create tab widget with game-style theming (no header bar - removed dead whitespace)
        self.tabs = QTabWidget()
        from .game_style_theme import GAME_STYLES
        self.tabs.setStyleSheet(GAME_STYLES['tab_widget'])
        main_layout.addWidget(self.tabs)
        
        # Initialize asusctl interface
        self.asusctl = AsusctlInterface()
        
        # Restore persistent fan curves on startup
        self._restore_persistent_curves()
        
        # Create dashboard tab
        self.dashboard_tab = self._create_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        
        # Create fan curve builder tab
        self.fan_curve_builder_tab = self._create_fan_curve_builder_tab()
        self.tabs.addTab(self.fan_curve_builder_tab, "Fan Curve Builder")
        
        # Profile manager (no separate tab - profiles accessed via dropdown in fan curve editor)
        self.profile_manager = ProfileManager()
        
        # Create log viewer tab
        self.log_viewer_tab = self._create_log_viewer_tab()
        self.tabs.addTab(self.log_viewer_tab, "System Logs")
        
        # Create history tab
        self.history_tab = self._create_history_tab()
        self.tabs.addTab(self.history_tab, "History")
        
        # Create fan status tab
        self.fan_status_tab = self._create_fan_status_tab()
        self.tabs.addTab(self.fan_status_tab, "Fan Status")
        
        # Create test fans tab
        self.test_fans_tab = self._create_test_fans_tab()
        self.tabs.addTab(self.test_fans_tab, "Test Fans")
        
        # Apply profiles tab removed
        
        # Create about tab
        self.about_tab = AboutTab(self)
        self.tabs.addTab(self.about_tab, "About")
        
        # Status bar with modern styling
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #f5f5f5;
                color: #666;
                border-top: 1px solid #e0e0e0;
                padding: 4px;
            }
        """)
        self.statusBar().showMessage("Monitoring active")
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_dashboard)
        self.update_timer.start(1000)  # Update every second
        
        # System tray
        self._create_system_tray()
        
        # Initial update
        self.update_dashboard()
        
        # Initialize scaling
        self._update_scaling()
    
    def resizeEvent(self, event):
        """Handle window resize to update scaling."""
        super().resizeEvent(event)
        self._update_scaling()
    
    def _update_scaling(self):
        """Update scaling factor and notify all widgets."""
        new_scale = UIScaling.get_scale_factor(self)
        if abs(new_scale - self._current_scale) > 0.01:  # Only update if significant change
            self._current_scale = new_scale
            self.scale_changed.emit(new_scale)
            
            # Also update all child widgets directly
            self._apply_scaling_to_children(self, new_scale)
    
    def _apply_scaling_to_children(self, widget: QWidget, scale: float):
        """Recursively apply scaling to all child widgets."""
        # If widget has update_scaling method, call it
        if hasattr(widget, 'update_scaling'):
            widget.update_scaling()
        
        # Recursively apply to children
        for child in widget.children():
            if isinstance(child, QWidget):
                self._apply_scaling_to_children(child, scale)
    
    def get_scale_factor(self) -> float:
        """Get current scale factor."""
        return self._current_scale
    
    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: white;
                color: #333;
                border-bottom: 1px solid #e0e0e0;
                padding: 4px;
            }
            QMenuBar::item {
                padding: 8px 16px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #f0f0f0;
            }
        """)
        
        # Help menu (simplified - Help is now a tab)
        help_menu = menubar.addMenu("Help")
        
        help_action = QAction("Help Documentation", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(lambda: self.tabs.setCurrentWidget(self.help_tab))
        help_menu.addAction(help_action)
        
        help_menu.addSeparator()
        
        dependency_action = QAction("Check Dependencies", self)
        dependency_action.triggered.connect(self._show_dependency_dialog)
        help_menu.addAction(dependency_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("About", self)
        about_action.triggered.connect(lambda: self.tabs.setCurrentWidget(self.about_tab))
        help_menu.addAction(about_action)
    
    def _show_dependency_dialog(self):
        """Show the dependency check dialog."""
        dialog = DependencyDialog(self)
        dialog.exec()
        # Refresh check after dialog closes
        self._refresh_after_dependency_check()
    
    def _refresh_after_dependency_check(self):
        """Refresh the application after dependency check."""
        # Could restart monitoring or check for newly available features
        pass
    
    
    def _show_about(self):
        """Show about dialog."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "About Daemon Breathalyzer",
            "<h2>Daemon Breathalyzer</h2>"
            "<p>Version 0.1.0</p>"
            "<p>A modern GUI application for managing ASUS laptop fan curves "
            "with real-time system monitoring and log analysis.</p>"
            "<p>© 2024</p>"
            "<p>Press <b>F1</b> for help documentation</p>"
        )
    
    def _create_dashboard_tab(self) -> QWidget:
        """Create the responsive game-style dashboard tab."""
        from .responsive_dashboard import ResponsiveDashboard
        return ResponsiveDashboard(self.monitor, self.asusctl, self)
    
    def _create_dashboard_tab_old(self) -> QWidget:
        """OLD - Create the dashboard tab with metrics and graphs."""
        widget = QWidget()
        widget.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        # Ensure enough right margin for the icon (icon is ~44px with padding, add extra space)
        layout.setContentsMargins(30, 30, 50, 30)  # Increased right margin from 30 to 50 to accommodate icon
        
        # Title section with minimal design - includes icon on the right
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title_layout.setContentsMargins(0, 0, 0, 0)  # No margins to maximize space
        title_layout.setSpacing(15)  # Space between title and icon
        
        title = QLabel("System Monitor")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setWeight(QFont.Weight.DemiBold)
        title.setFont(title_font)
        title.setStyleSheet("color: #212121; margin-bottom: 10px;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # Add icon on the right, vertically aligned with text
        icon_path = self._find_icon_path()
        if icon_path:
            icon_label = QLabel()
            icon_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Load icon and resize - ensure it's fully visible and matches text height
            pixmap = QPixmap(str(icon_path))
            # Size icon to align nicely with 20pt text - slightly smaller to ensure it fits
            icon_size = 40  # Reduced from 48 to ensure it's fully visible
            pixmap = pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, 
                                  Qt.TransformationMode.SmoothTransformation)
            
            icon_label.setPixmap(pixmap)
            icon_label.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    border: none;
                    padding: 2px;
                    margin: 0px;
                }
            """)
            # Set size with small padding to ensure icon is fully visible
            icon_label.setMinimumSize(icon_size + 4, icon_size + 4)  # Extra 4px padding to prevent clipping
            icon_label.setMaximumSize(icon_size + 4, icon_size + 4)
            
            title_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        layout.addLayout(title_layout)
        
        # Metrics grid
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(15)
        
        # CPU metrics
        self.cpu_percent_card = MetricCard("CPU Usage", "%", color="#2196F3")
        self.cpu_temp_card = MetricCard("CPU Temperature", "°C", color="#F44336")
        self.cpu_freq_card = MetricCard("CPU Frequency", "MHz", color="#4CAF50")
        
        # Memory metrics
        self.memory_card = MetricCard("Memory", "%", color="#FF9800")
        self.memory_used_card = MetricCard("Memory Used", "GB", color="#9C27B0")
        
        # GPU metrics
        self.gpu_util_card = MetricCard("GPU Usage", "%", color="#00BCD4")
        self.gpu_temp_card = MetricCard("GPU Temperature", "°C", color="#E91E63")
        self.gpu_memory_card = MetricCard("GPU Memory", "%", color="#3F51B5")
        
        # Add to grid
        row = 0
        metrics_grid.addWidget(self.cpu_percent_card, row, 0)
        metrics_grid.addWidget(self.cpu_temp_card, row, 1)
        metrics_grid.addWidget(self.cpu_freq_card, row, 2)
        
        row = 1
        metrics_grid.addWidget(self.memory_card, row, 0)
        metrics_grid.addWidget(self.memory_used_card, row, 1)
        metrics_grid.addWidget(self.gpu_util_card, row, 2)
        
        row = 2
        metrics_grid.addWidget(self.gpu_temp_card, row, 0)
        metrics_grid.addWidget(self.gpu_memory_card, row, 1)
        
        # Network metrics
        self.network_sent_card = MetricCard("Network Sent", "Mbps", color="#FF5722")
        self.network_recv_card = MetricCard("Network Received", "Mbps", color="#4CAF50")
        self.network_total_card = MetricCard("Network Total", "Mbps", color="#2196F3")
        
        row = 3
        metrics_grid.addWidget(self.network_sent_card, row, 0)
        metrics_grid.addWidget(self.network_recv_card, row, 1)
        metrics_grid.addWidget(self.network_total_card, row, 2)
        
        # FPS metric
        self.fps_card = MetricCard("FPS", "fps", color="#E91E63")
        
        row = 4
        metrics_grid.addWidget(self.fps_card, row, 0)
        
        layout.addLayout(metrics_grid)
        
        # Graphs
        self.graph_widget = GraphWidget()
        layout.addWidget(self.graph_widget)
        
        # Stretch
        layout.addStretch()
        
        return widget
    
    def _create_fan_curve_tab(self) -> QWidget:
        """Create the fan curve editor tab."""
        widget = QWidget()
        widget.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Check if asusctl is available
        if not self.asusctl.is_available():
            warning_widget = QWidget()
            warning_layout = QVBoxLayout(warning_widget)
            warning_layout.setContentsMargins(30, 30, 30, 30)
            
            warning_label = QLabel(
                "⚠️ asusctl is not available on this system.\n\n"
                "Fan curve editing requires asusctl to be installed.\n"
                "Please install asusctl to use this feature.\n\n"
                "See Help → Check Dependencies for installation instructions."
            )
            warning_label.setStyleSheet("""
                QLabel {
                    color: #666;
                    font-size: 12pt;
                    padding: 20px;
                    background-color: #fff3e0;
                    border-radius: 8px;
                    border: 1px solid #ffcc80;
                }
            """)
            warning_label.setWordWrap(True)
            warning_layout.addWidget(warning_label)
            warning_layout.addStretch()
            
            layout.addWidget(warning_widget)
            return widget
        
        # Create fan curve editor
        self.fan_curve_editor = FanCurveEditor()
        layout.addWidget(self.fan_curve_editor)
        
        return widget
    
    def _create_log_viewer_tab(self) -> QWidget:
        """Create the log viewer tab."""
        from .log_viewer_tab import LogViewerTab
        return LogViewerTab(self)
    
    def _create_history_tab(self) -> QWidget:
        """Create the history tab."""
        from .history_tab import HistoryTab
        return HistoryTab(self.monitor, self)
    
    def _create_fan_status_tab(self) -> QWidget:
        """Create the fan status tab."""
        from .fan_status_tab import FanStatusTab
        return FanStatusTab(self.monitor, self.asusctl, self)
    
    def _create_test_fans_tab(self) -> QWidget:
        """Create the test fans tab."""
        from .test_fans_tab import TestFansTab
        return TestFansTab(self.monitor, self.asusctl, self)
    
    def _create_apply_profiles_tab(self) -> QWidget:
        """Create the apply profiles tab."""
        from .apply_profiles_tab import ApplyProfilesTab
        return ApplyProfilesTab(self)
    
    def _create_fan_curve_builder_tab(self) -> QWidget:
        """Create the fan curve builder tab."""
        from .fan_curve_builder import FanCurveBuilderWidget
        return FanCurveBuilderWidget(self)
    
    def _restore_persistent_curves(self):
        """Restore persistent fan curves on startup."""
        try:
            from ..control.fan_curve_persistence import FanCurvePersistence
            
            persistence = FanCurvePersistence()
            
            # Get current profile
            current_profile = self.asusctl.get_current_profile() or Profile.BALANCED
            
            # Load saved curves for current profile
            saved_curves = persistence.load_active_curves(current_profile)
            
            if saved_curves:
                # Restore each curve
                for fan_name, curve in saved_curves.items():
                    try:
                        # Ensure fan curves are enabled
                        if not self.asusctl.get_fan_curve_enabled(current_profile):
                            self.asusctl.enable_fan_curves(current_profile, True)
                        
                        # Restore the curve (pass save_persistent=False to avoid re-saving)
                        success, message = self.asusctl.set_fan_curve(
                            current_profile,
                            fan_name,
                            curve,
                            save_persistent=False  # Don't re-save on restore
                        )
                        if success:
                            print(f"✓ Restored fan curve for {fan_name}")
                        else:
                            print(f"⚠ Warning: Could not restore curve for {fan_name}: {message}")
                    except Exception as e:
                        print(f"⚠ Error restoring curve for {fan_name}: {e}")
        except Exception as e:
            print(f"⚠ Warning: Could not restore persistent curves: {e}")
    
    def update_dashboard(self):
        """Update all dashboard widgets with latest metrics."""
        metrics = self.monitor.get_metrics()
        history = self.monitor.get_history()
        
        # Check if using responsive dashboard
        if hasattr(self, 'dashboard_tab') and hasattr(self.dashboard_tab, 'update_metrics'):
            # Use responsive dashboard update method
            self.dashboard_tab.update_metrics(metrics, history)
        else:
            # Fallback to old dashboard widgets (backward compatibility)
            if hasattr(self, 'cpu_percent_card'):
                self.cpu_percent_card.set_value(metrics['cpu_percent'])
            if hasattr(self, 'cpu_temp_card'):
                if metrics['cpu_temp']:
                    self.cpu_temp_card.set_value(metrics['cpu_temp'])
                else:
                    self.cpu_temp_card.set_value(None, text="N/A")
            if hasattr(self, 'cpu_freq_card'):
                self.cpu_freq_card.set_value(metrics['cpu_freq'])
            
            if hasattr(self, 'memory_card'):
                self.memory_card.set_value(metrics['memory_percent'])
            if hasattr(self, 'memory_used_card'):
                self.memory_used_card.set_value(metrics['memory_used_gb'], decimals=2)
            
            # GPU utilization
            if hasattr(self, 'gpu_util_card'):
                if metrics['gpu_utilization'] is not None:
                    self.gpu_util_card.set_value(metrics['gpu_utilization'])
                else:
                    self.gpu_util_card.set_value(None, text="N/A")
            
            if hasattr(self, 'gpu_temp_card'):
                if metrics['gpu_temp'] is not None:
                    self.gpu_temp_card.set_value(metrics['gpu_temp'])
                else:
                    self.gpu_temp_card.set_value(None, text="N/A")
            
            if hasattr(self, 'gpu_memory_card'):
                if metrics['gpu_memory_percent'] is not None:
                    self.gpu_memory_card.set_value(metrics['gpu_memory_percent'])
                else:
                    self.gpu_memory_card.set_value(None, text="N/A")
            
            # Fan gauges removed from System Monitor
            
            # Update network metrics
            if hasattr(self, 'network_sent_card'):
                self.network_sent_card.set_value(metrics.get('network_sent_mbps', 0.0), decimals=2)
            if hasattr(self, 'network_recv_card'):
                self.network_recv_card.set_value(metrics.get('network_recv_mbps', 0.0), decimals=2)
            if hasattr(self, 'network_total_card'):
                self.network_total_card.set_value(metrics.get('network_total_mbps', 0.0), decimals=2)
            
            # Update FPS
            if hasattr(self, 'fps_card'):
                fps = metrics.get('fps')
                if fps is not None and fps > 0:
                    self.fps_card.set_value(fps, decimals=0)
                else:
                    self.fps_card.set_value(None, text="N/A")
            
            # Update graphs
            if hasattr(self, 'graph_widget'):
                self.graph_widget.update_data(history)
        
        # Update status bar
        status_msg = f"Monitoring active | "
        if metrics['cpu_temp']:
            status_msg += f"CPU: {metrics['cpu_temp']:.1f}°C | "
        if metrics['gpu_temp']:
            status_msg += f"GPU: {metrics['gpu_temp']:.1f}°C | "
        status_msg += f"CPU: {metrics['cpu_percent']:.1f}% | Memory: {metrics['memory_percent']:.1f}%"
        self.statusBar().showMessage(status_msg)
        
        # Update system tray tooltip with system metrics
        self._update_tray_tooltip(metrics)
    
    def _set_window_icon(self):
        """Set the application window icon."""
        icon_path = self._find_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(str(icon_path)))
    
    def _find_icon_path(self):
        """Find the icon file path."""
        project_root = Path(__file__).parent.parent.parent
        icon_paths = [
            project_root / "img" / "icon.png",
            project_root / "img" / "icon.jpg",
            Path.home() / ".local" / "share" / "icons" / "hicolor" / "256x256" / "apps" / "asus-control.png",
            Path.home() / ".local" / "share" / "icons" / "hicolor" / "256x256" / "apps" / "asus-control.jpg",
        ]
        
        for icon_path in icon_paths:
            if icon_path.exists():
                return icon_path
        return None
    
    def _create_system_tray(self):
        """Create system tray icon and menu."""
        # Check if system tray is available
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("Daemon Breathalyzer")
        
        # Set icon
        icon_path = self._find_icon_path()
        if icon_path:
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            # Fallback to default icon
            self.tray_icon.setIcon(self.style().standardIcon(
                self.style().StandardPixmap.SP_ComputerIcon
            ))
        
        # Create tray menu
        tray_menu = QMenu(self)
        
        # Show window action
        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self.show_window_from_tray)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        # Quit action
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # Connect double-click to show window
        self.tray_icon.activated.connect(self._tray_icon_activated)
        
        # Show tray icon
        self.tray_icon.show()
        
        # Show notification when first shown
        self.tray_icon.showMessage(
            "Daemon Breathalyzer",
            "Application is running in system tray",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
    
    def _update_tray_tooltip(self, metrics):
        """Update system tray tooltip with system metrics summary."""
        if not hasattr(self, 'tray_icon') or not self.tray_icon.isVisible():
            return
        
        # Build tooltip text with CPU, GPU, FPS, Network summaries
        tooltip_lines = ["Daemon Breathalyzer", "━━━━━━━━━━━━━━━━"]
        
        # CPU Load
        cpu_load = metrics.get('cpu_percent', 0.0)
        tooltip_lines.append(f"CPU: {cpu_load:.1f}%")
        
        # GPU Load
        gpu_load = metrics.get('gpu_utilization', 0.0)
        if gpu_load is not None:
            tooltip_lines.append(f"GPU: {gpu_load:.1f}%")
        else:
            tooltip_lines.append("GPU: N/A")
        
        # FPS
        fps = metrics.get('fps')
        if fps is not None:
            tooltip_lines.append(f"FPS: {fps:.0f}")
        else:
            tooltip_lines.append("FPS: N/A")
        
        # Network Load (total)
        network_total = metrics.get('network_total_mbps', 0.0)
        tooltip_lines.append(f"Network: {network_total:.2f} Mbps")
        
        tooltip_text = "\n".join(tooltip_lines)
        self.tray_icon.setToolTip(tooltip_text)
    
    def _tray_icon_activated(self, reason):
        """Handle tray icon activation (double-click, etc.)."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_from_tray()
    
    def show_window_from_tray(self):
        """Show window from system tray."""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def quit_application(self):
        """Quit the application."""
        # Restore fan curves from test mode if any
        if hasattr(self, 'test_fans_tab'):
            self.test_fans_tab.cleanup()
        self.monitor.stop()
        QApplication.quit()
    
    def changeEvent(self, event):
        """Handle window state changes (minimize, etc.)."""
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized():
                # Hide to system tray instead of minimizing
                if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
                    self.hide()
                    self.tray_icon.showMessage(
                        "Daemon Breathalyzer",
                        "Application minimized to system tray",
                        QSystemTrayIcon.MessageIcon.Information,
                        2000
                    )
        super().changeEvent(event)
    
    def closeEvent(self, event):
        """Handle window close event."""
        # If system tray is available, hide to tray instead of closing
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Daemon Breathalyzer",
                "Application is running in system tray. Double-click the tray icon to show the window.",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
        else:
            # No system tray, cleanup and quit
            # Restore fan curves from test mode if any
            if hasattr(self, 'test_fans_tab'):
                self.test_fans_tab.cleanup()
            self.monitor.stop()
            event.accept()

