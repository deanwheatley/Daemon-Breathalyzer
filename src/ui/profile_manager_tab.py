#!/usr/bin/env python3
"""
Profile Manager Tab

UI for managing saved fan curve profiles.
"""

from typing import Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QLineEdit, QTextEdit,
    QDialog, QDialogButtonBox, QFormLayout, QFileDialog, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ..control.profile_manager import ProfileManager, SavedProfile
from ..control.asusctl_interface import FanCurve


class ProfileDialog(QDialog):
    """Dialog for creating/editing a profile."""
    
    def __init__(self, parent=None, profile: SavedProfile = None):
        super().__init__(parent)
        self.profile = profile
        
        if profile:
            self.setWindowTitle("Edit Profile")
        else:
            self.setWindowTitle("New Profile")
        
        self.setMinimumWidth(400)
        self._setup_ui()
        
        if profile:
            self.name_input.setText(profile.name)
            self.description_input.setPlainText(profile.description)
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter profile name")
        form.addRow("Name:", self.name_input)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        self.description_input.setPlaceholderText("Optional description")
        form.addRow("Description:", self.description_input)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_name(self) -> str:
        """Get the profile name."""
        return self.name_input.text().strip()
    
    def get_description(self) -> str:
        """Get the profile description."""
        return self.description_input.toPlainText().strip()


class ProfileManagerTab(QWidget):
    """Tab for managing fan curve profiles."""
    
    profile_selected = pyqtSignal(str)  # Emits profile name when selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.profile_manager = ProfileManager()
        self.current_cpu_curve: Optional[FanCurve] = None
        self.current_gpu_curve: Optional[FanCurve] = None
        
        self.setup_ui()
        self.refresh_profile_list()
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Profile Manager")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setWeight(QFont.Weight.DemiBold)
        title.setFont(title_font)
        title.setStyleSheet("color: #212121;")
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "Save and manage custom fan curve profiles. "
            "Profiles store CPU and GPU fan curves that you can quickly apply later."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666;")
        layout.addWidget(desc)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Profile list
        list_group = QGroupBox("Saved Profiles")
        list_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e8e8e8;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        list_layout = QVBoxLayout(list_group)
        
        self.profile_list = QListWidget()
        self.profile_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #E3F2FD;
                color: #1976D2;
            }
        """)
        self.profile_list.itemDoubleClicked.connect(self.on_profile_double_clicked)
        list_layout.addWidget(self.profile_list)
        
        # List actions
        list_actions = QHBoxLayout()
        
        self.load_btn = QPushButton("Load")
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
            }
        """)
        self.load_btn.clicked.connect(self.load_selected_profile)
        list_actions.addWidget(self.load_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_selected_profile)
        list_actions.addWidget(self.delete_btn)
        
        list_layout.addLayout(list_actions)
        
        content_layout.addWidget(list_group, 1)
        
        # Actions panel
        actions_group = QGroupBox("Actions")
        actions_group.setStyleSheet(list_group.styleSheet())
        actions_layout = QVBoxLayout(actions_group)
        
        self.new_profile_btn = QPushButton("Create New Profile from Scratch")
        self.new_profile_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
            }
        """)
        self.new_profile_btn.clicked.connect(self.create_new_profile)
        actions_layout.addWidget(self.new_profile_btn)
        
        self.save_btn = QPushButton("Save Current Curves")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
            }
        """)
        self.save_btn.clicked.connect(self.save_current_curves)
        actions_layout.addWidget(self.save_btn)
        
        self.export_btn = QPushButton("Export Profile")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 12px;
                border-radius: 6px;
            }
        """)
        self.export_btn.clicked.connect(self.export_profile)
        actions_layout.addWidget(self.export_btn)
        
        self.import_btn = QPushButton("Import Profile")
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 12px;
                border-radius: 6px;
            }
        """)
        self.import_btn.clicked.connect(self.import_profile)
        actions_layout.addWidget(self.import_btn)
        
        actions_layout.addStretch()
        
        content_layout.addWidget(actions_group, 1)
        
        layout.addLayout(content_layout)
    
    def set_current_curves(self, cpu_curve: Optional[FanCurve], gpu_curve: Optional[FanCurve]):
        """Set the current fan curves from the editor."""
        self.current_cpu_curve = cpu_curve
        self.current_gpu_curve = gpu_curve
    
    def refresh_profile_list(self):
        """Refresh the profile list."""
        self.profile_list.clear()
        
        profiles = self.profile_manager.list_profiles()
        for name in profiles:
            profile = self.profile_manager.get_profile(name)
            item = QListWidgetItem(name)
            if profile.description:
                item.setToolTip(profile.description)
            self.profile_list.addItem(item)
    
    def create_new_profile(self):
        """Create a new profile from scratch with default curves."""
        dialog = ProfileDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.get_name()
            if not name:
                QMessageBox.warning(self, "Invalid Name", "Profile name cannot be empty.")
                return
            
            if name in self.profile_manager.list_profiles():
                reply = QMessageBox.question(
                    self,
                    "Overwrite?",
                    f"Profile '{name}' already exists. Overwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # Create default balanced curves
            from ..control.asusctl_interface import get_preset_curve
            default_cpu_curve = get_preset_curve('balanced')
            default_gpu_curve = get_preset_curve('balanced')
            
            profile = SavedProfile(
                name=name,
                description=dialog.get_description(),
                cpu_fan_curve=default_cpu_curve,
                gpu_fan_curve=default_gpu_curve
            )
            
            if self.profile_manager.save_profile(profile):
                QMessageBox.information(
                    self,
                    "Created",
                    f"Profile '{name}' created with default balanced curves!\n\n"
                    "Switch to the Fan Curves tab to customize the curves, "
                    "then come back to save your changes."
                )
                self.refresh_profile_list()
                # Load the new profile so user can edit it
                self.load_profile_for_editing(name, default_cpu_curve, default_gpu_curve)
            else:
                QMessageBox.warning(self, "Error", "Failed to create profile.")
    
    def load_profile_for_editing(self, profile_name: str, cpu_curve, gpu_curve):
        """Load a profile for editing in the fan curve editor."""
        self.set_current_curves(cpu_curve, gpu_curve)
        self.profile_selected.emit(profile_name)
    
    def save_current_curves(self):
        """Save the current fan curves as a new profile."""
        if not self.current_cpu_curve and not self.current_gpu_curve:
            QMessageBox.warning(
                self,
                "No Curves",
                "Please configure fan curves in the Fan Curves tab first."
            )
            return
        
        dialog = ProfileDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.get_name()
            if not name:
                QMessageBox.warning(self, "Invalid Name", "Profile name cannot be empty.")
                return
            
            if name in self.profile_manager.list_profiles():
                reply = QMessageBox.question(
                    self,
                    "Overwrite?",
                    f"Profile '{name}' already exists. Overwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            profile = SavedProfile(
                name=name,
                description=dialog.get_description(),
                cpu_fan_curve=self.current_cpu_curve,
                gpu_fan_curve=self.current_gpu_curve
            )
            
            if self.profile_manager.save_profile(profile):
                QMessageBox.information(self, "Saved", f"Profile '{name}' saved successfully!")
                self.refresh_profile_list()
            else:
                QMessageBox.warning(self, "Error", "Failed to save profile.")
    
    def load_selected_profile(self):
        """Load the selected profile."""
        item = self.profile_list.currentItem()
        if not item:
            QMessageBox.information(self, "No Selection", "Please select a profile to load.")
            return
        
        profile_name = item.text()
        profile = self.profile_manager.get_profile(profile_name)
        
        if profile:
            self.set_current_curves(profile.cpu_fan_curve, profile.gpu_fan_curve)
            self.profile_selected.emit(profile_name)
            QMessageBox.information(
                self,
                "Loaded",
                f"Profile '{profile_name}' loaded. Switch to Fan Curve Designer tab to view and edit."
            )
        else:
            QMessageBox.warning(self, "Error", f"Failed to load profile '{profile_name}'.")
    
    def on_profile_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on profile."""
        self.load_selected_profile()
    
    def delete_selected_profile(self):
        """Delete the selected profile."""
        item = self.profile_list.currentItem()
        if not item:
            QMessageBox.information(self, "No Selection", "Please select a profile to delete.")
            return
        
        profile_name = item.text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete profile '{profile_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.profile_manager.delete_profile(profile_name):
                QMessageBox.information(self, "Deleted", f"Profile '{profile_name}' deleted.")
                self.refresh_profile_list()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete profile.")
    
    def export_profile(self):
        """Export a profile to a file."""
        item = self.profile_list.currentItem()
        if not item:
            QMessageBox.information(self, "No Selection", "Please select a profile to export.")
            return
        
        profile_name = item.text()
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Profile",
            f"{profile_name}.json",
            "JSON Files (*.json);;YAML Files (*.yaml);;All Files (*)"
        )
        
        if file_path:
            format = 'yaml' if file_path.endswith(('.yaml', '.yml')) else 'json'
            if self.profile_manager.export_profile(profile_name, Path(file_path), format):
                QMessageBox.information(self, "Exported", f"Profile exported to {file_path}")
            else:
                QMessageBox.warning(self, "Error", "Failed to export profile.")
    
    def import_profile(self):
        """Import a profile from a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Profile",
            "",
            "JSON Files (*.json);;YAML Files (*.yaml);;All Files (*)"
        )
        
        if file_path:
            profile = self.profile_manager.import_profile(Path(file_path))
            if profile:
                QMessageBox.information(
                    self,
                    "Imported",
                    f"Profile '{profile.name}' imported successfully!"
                )
                self.refresh_profile_list()
            else:
                QMessageBox.warning(self, "Error", "Failed to import profile.")

