#!/usr/bin/env python3
"""
Apply Profiles Tab

UI for applying saved fan curve profiles to the system.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QGroupBox,
    QButtonGroup, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from ..control.profile_manager import ProfileManager
from ..control.asusctl_interface import AsusctlInterface, Profile, FanCurve
from .game_style_theme import GAME_COLORS, GAME_STYLES


class ApplyProfilesTab(QWidget):
    """Tab for applying fan curve profiles to the system."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.profile_manager = ProfileManager()
        self.asusctl = AsusctlInterface()
        
        self.current_asus_profile = Profile.BALANCED  # Default
        
        self.setup_ui()
        self.refresh_profile_list()
        self.refresh_current_status()
        
        # Timer to periodically refresh status
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.refresh_current_status)
        self.status_timer.start(2000)  # Update every 2 seconds
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Apply Profiles")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {GAME_COLORS['accent_blue']};")
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "Select a saved fan curve profile and apply it to your system. "
            "Choose which ASUS power profile (Balanced, Quiet, or Performance) "
            "to apply the curves to."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {GAME_COLORS['text_secondary']}; padding: 10px 0;")
        layout.addWidget(desc)
        
        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Left side - Profile selection
        left_panel = self._create_profile_selection_panel()
        content_layout.addWidget(left_panel, 1)
        
        # Right side - Apply controls and status
        right_panel = self._create_apply_panel()
        content_layout.addWidget(right_panel, 1)
        
        layout.addLayout(content_layout)
        layout.addStretch()
    
    def _create_profile_selection_panel(self) -> QGroupBox:
        """Create the profile selection panel."""
        panel = QGroupBox("Saved Profiles")
        panel.setStyleSheet(GAME_STYLES['groupbox'])
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Profile list
        self.profile_list = QListWidget()
        self.profile_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {GAME_COLORS['bg_card']};
                border: 2px solid {GAME_COLORS['border']};
                border-radius: 8px;
                padding: 5px;
                color: {GAME_COLORS['text_primary']};
                font-size: 11pt;
            }}
            QListWidget::item {{
                padding: 12px;
                border-bottom: 1px solid {GAME_COLORS['border']};
                border-radius: 4px;
                margin: 2px;
            }}
            QListWidget::item:hover {{
                background-color: {GAME_COLORS['bg_medium']};
            }}
            QListWidget::item:selected {{
                background-color: {GAME_COLORS['accent_blue']};
                color: {GAME_COLORS['bg_dark']};
                font-weight: bold;
            }}
        """)
        self.profile_list.itemSelectionChanged.connect(self._on_profile_selected)
        layout.addWidget(self.profile_list)
        
        # Profile info
        self.profile_info = QLabel("Select a profile to view details")
        self.profile_info.setWordWrap(True)
        self.profile_info.setStyleSheet(f"""
            QLabel {{
                background-color: {GAME_COLORS['bg_card']};
                border: 2px solid {GAME_COLORS['border']};
                border-radius: 8px;
                padding: 15px;
                color: {GAME_COLORS['text_secondary']};
                min-height: 80px;
            }}
        """)
        layout.addWidget(self.profile_info)
        
        return panel
    
    def _create_apply_panel(self) -> QGroupBox:
        """Create the apply controls panel."""
        panel = QGroupBox("Apply to System")
        panel.setStyleSheet(GAME_STYLES['groupbox'])
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        
        # ASUS Profile selection
        asus_profile_label = QLabel("ASUS Power Profile:")
        asus_profile_label.setStyleSheet(f"color: {GAME_COLORS['text_primary']}; font-weight: bold;")
        layout.addWidget(asus_profile_label)
        
        asus_profile_group = QHBoxLayout()
        asus_profile_group.setSpacing(10)
        
        self.asus_profile_group = QButtonGroup()
        
        self.balanced_btn = QPushButton("Balanced")
        self.quiet_btn = QPushButton("Quiet")
        self.performance_btn = QPushButton("Performance")
        
        for btn in [self.balanced_btn, self.quiet_btn, self.performance_btn]:
            btn.setCheckable(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {GAME_COLORS['bg_card']};
                    color: {GAME_COLORS['text_primary']};
                    border: 2px solid {GAME_COLORS['border']};
                    border-radius: 8px;
                    padding: 10px 16px;
                    font-weight: bold;
                    font-size: 11pt;
                }}
                QPushButton:hover {{
                    border: 2px solid {GAME_COLORS['accent_blue']};
                    background-color: {GAME_COLORS['bg_medium']};
                }}
                QPushButton:checked {{
                    background-color: {GAME_COLORS['accent_blue']};
                    color: {GAME_COLORS['bg_dark']};
                    border: 2px solid {GAME_COLORS['accent_blue']};
                }}
            """)
            self.asus_profile_group.addButton(btn)
        
        self.balanced_btn.setChecked(True)
        self.asus_profile_group.buttonClicked.connect(self._on_asus_profile_changed)
        
        asus_profile_group.addWidget(self.balanced_btn)
        asus_profile_group.addWidget(self.quiet_btn)
        asus_profile_group.addWidget(self.performance_btn)
        asus_profile_group.addStretch()
        
        layout.addLayout(asus_profile_group)
        
        # Apply button
        self.apply_btn = QPushButton("🚀 Apply Profile")
        self.apply_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {GAME_COLORS['accent_green']};
                color: {GAME_COLORS['bg_dark']};
                border: 2px solid {GAME_COLORS['accent_green']};
                border-radius: 10px;
                padding: 15px 30px;
                font-weight: bold;
                font-size: 14pt;
                min-height: 50px;
            }}
            QPushButton:hover {{
                box-shadow: 0 0 20px {GAME_COLORS['accent_green']};
                background-color: #00ff99;
            }}
            QPushButton:pressed {{
                background-color: #00cc77;
            }}
            QPushButton:disabled {{
                background-color: {GAME_COLORS['bg_medium']};
                color: {GAME_COLORS['text_dim']};
                border: 2px solid {GAME_COLORS['border']};
            }}
        """)
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._apply_profile)
        layout.addWidget(self.apply_btn)
        
        # Current status
        status_label = QLabel("Current Status:")
        status_label.setStyleSheet(f"color: {GAME_COLORS['text_primary']}; font-weight: bold; margin-top: 10px;")
        layout.addWidget(status_label)
        
        self.status_display = QLabel("Loading...")
        self.status_display.setWordWrap(True)
        self.status_display.setStyleSheet(f"""
            QLabel {{
                background-color: {GAME_COLORS['bg_card']};
                border: 2px solid {GAME_COLORS['border']};
                border-radius: 8px;
                padding: 15px;
                color: {GAME_COLORS['text_secondary']};
                min-height: 100px;
            }}
        """)
        layout.addWidget(self.status_display)
        
        layout.addStretch()
        
        return panel
    
    def refresh_profile_list(self):
        """Refresh the profile list."""
        self.profile_list.clear()
        
        self.profile_manager.load_all_profiles()
        profiles = self.profile_manager.list_profiles()
        
        if not profiles:
            item = QListWidgetItem("No profiles saved")
            item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make it non-selectable
            self.profile_list.addItem(item)
            self.profile_info.setText("Create profiles in the Profile Manager tab first.")
            return
        
        for name in profiles:
            profile = self.profile_manager.get_profile(name)
            item = QListWidgetItem(name)
            if profile and profile.description:
                item.setToolTip(profile.description)
            self.profile_list.addItem(item)
    
    def _on_profile_selected(self):
        """Handle profile selection."""
        item = self.profile_list.currentItem()
        if not item or not item.text() or item.text() == "No profiles saved":
            self.profile_info.setText("Select a profile to view details")
            self.apply_btn.setEnabled(False)
            return
        
        profile_name = item.text()
        profile = self.profile_manager.get_profile(profile_name)
        
        if not profile:
            self.profile_info.setText(f"Error: Could not load profile '{profile_name}'")
            self.apply_btn.setEnabled(False)
            return
        
        # Build info text
        info_lines = [f"<b>{profile_name}</b>"]
        if profile.description:
            info_lines.append(f"<i>{profile.description}</i>")
        info_lines.append("")
        info_lines.append("<b>Curves included:</b>")
        
        if profile.cpu_fan_curve:
            points = len(profile.cpu_fan_curve.points)
            info_lines.append(f"✓ CPU Fan ({points} points)")
        else:
            info_lines.append("✗ CPU Fan (not configured)")
        
        if profile.gpu_fan_curve:
            points = len(profile.gpu_fan_curve.points)
            info_lines.append(f"✓ GPU Fan ({points} points)")
        else:
            info_lines.append("✗ GPU Fan (not configured)")
        
        self.profile_info.setText("<br>".join(info_lines))
        self.apply_btn.setEnabled(True)
    
    def _on_asus_profile_changed(self, button: QPushButton):
        """Handle ASUS profile selection change."""
        if button == self.balanced_btn:
            self.current_asus_profile = Profile.BALANCED
        elif button == self.quiet_btn:
            self.current_asus_profile = Profile.QUIET
        elif button == self.performance_btn:
            self.current_asus_profile = Profile.PERFORMANCE
        
        self.refresh_current_status()
    
    def refresh_current_status(self):
        """Refresh the current status display."""
        try:
            current_profile = self.asusctl.get_current_profile() or Profile.BALANCED
            profile_name = current_profile.value.capitalize()
            
            # Get current curves
            curves = self.asusctl.get_fan_curves(current_profile)
            cpu_curve = curves.get("CPU")
            gpu_curve = curves.get("GPU")
            
            status_lines = [
                f"<b>Active ASUS Profile:</b> {profile_name}",
                ""
            ]
            
            if cpu_curve:
                status_lines.append(f"✓ CPU Fan: Curve applied ({len(cpu_curve.points)} points)")
            else:
                status_lines.append("✗ CPU Fan: No custom curve")
            
            if gpu_curve:
                status_lines.append(f"✓ GPU Fan: Curve applied ({len(gpu_curve.points)} points)")
            else:
                status_lines.append("✗ GPU Fan: No custom curve")
            
            # Check if fan curves are enabled
            try:
                enabled = self.asusctl.get_fan_curve_enabled(current_profile)
                status_lines.append("")
                if enabled is True:
                    status_lines.append("<b style='color: #00ff88;'>✓ Fan curves enabled</b>")
                elif enabled is False:
                    status_lines.append("<b style='color: #ff3366;'>✗ Fan curves disabled</b>")
                # If enabled is None, we can't determine status, so skip
            except:
                pass  # Skip if we can't check
            
            self.status_display.setText("<br>".join(status_lines))
        except Exception as e:
            self.status_display.setText(f"Error loading status: {e}")
    
    def _apply_profile(self):
        """Apply the selected profile to the system."""
        item = self.profile_list.currentItem()
        if not item or not item.text() or item.text() == "No profiles saved":
            QMessageBox.warning(
                self,
                "No Profile Selected",
                "Please select a profile to apply."
            )
            return
        
        profile_name = item.text()
        profile = self.profile_manager.get_profile(profile_name)
        
        if not profile:
            QMessageBox.warning(
                self,
                "Error",
                f"Could not load profile '{profile_name}'"
            )
            return
        
        # Check if profile has any curves
        if not profile.cpu_fan_curve and not profile.gpu_fan_curve:
            QMessageBox.warning(
                self,
                "No Curves",
                f"Profile '{profile_name}' has no fan curves configured."
            )
            return
        
        # Confirm application
        asus_profile_name = self.current_asus_profile.value.capitalize()
        curve_info = []
        if profile.cpu_fan_curve:
            curve_info.append("CPU fan")
        if profile.gpu_fan_curve:
            curve_info.append("GPU fan")
        
        reply = QMessageBox.question(
            self,
            "Apply Profile?",
            f"Apply profile '{profile_name}' to {asus_profile_name} profile?\n\n"
            f"This will set curves for: {', '.join(curve_info)}\n\n"
            f"Note: This will replace any existing curves for the selected ASUS profile.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Apply curves
        success_count = 0
        error_messages = []
        
        try:
            # Enable fan curves first
            enable_success, enable_msg = self.asusctl.enable_fan_curves(
                self.current_asus_profile, True
            )
            if not enable_success:
                error_messages.append(f"Failed to enable fan curves: {enable_msg}")
            
            # Apply CPU curve
            if profile.cpu_fan_curve:
                success, message = self.asusctl.set_fan_curve(
                    self.current_asus_profile,
                    "CPU",
                    profile.cpu_fan_curve,
                    save_persistent=True
                )
                if success:
                    success_count += 1
                else:
                    error_messages.append(f"CPU fan: {message}")
            
            # Apply GPU curve
            if profile.gpu_fan_curve:
                success, message = self.asusctl.set_fan_curve(
                    self.current_asus_profile,
                    "GPU",
                    profile.gpu_fan_curve,
                    save_persistent=True
                )
                if success:
                    success_count += 1
                else:
                    error_messages.append(f"GPU fan: {message}")
            
            # Show result
            if error_messages:
                QMessageBox.warning(
                    self,
                    "Partially Applied",
                    f"Profile applied with {success_count} curve(s) successful.\n\n"
                    f"Errors:\n" + "\n".join(error_messages)
                )
            else:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Profile '{profile_name}' applied successfully to {asus_profile_name} profile!\n\n"
                    f"Applied {success_count} curve(s)."
                )
            
            # Refresh status
            self.refresh_current_status()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to apply profile: {str(e)}"
            )

