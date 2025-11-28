#!/usr/bin/env python3
"""
Dependency Installation Dialog

Modern, minimalist dialog for checking and installing dependencies.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QWidget, QProgressBar, QFrame,
    QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor

from ..utils.dependency_checker import DependencyChecker, Dependency


class InstallThread(QThread):
    """Thread for installing dependencies."""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    
    def __init__(self, dep: Dependency):
        super().__init__()
        self.dep = dep
        self.checker = DependencyChecker()
    
    def run(self):
        """Run the installation."""
        self.progress.emit(f"Installing {self.dep.name}...")
        success, message = self.checker.install_via_pip(self.dep)
        self.finished.emit(success, message)


class DependencyCard(QWidget):
    """A card widget for displaying a dependency."""
    
    def __init__(self, dep_info: dict, checker: DependencyChecker, parent=None):
        super().__init__(parent)
        self.dep_info = dep_info
        self.checker = checker
        self.dep = None
        self.install_thread = None
        
        # Find the actual dependency object
        for dep in checker.dependencies:
            if dep.name == dep_info['name']:
                self.dep = dep
                break
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI for the dependency card."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Status icon and name
        self.status_label = QLabel(self.dep_info['icon'])
        status_font = QFont()
        status_font.setPointSize(16)
        self.status_label.setFont(status_font)
        header_layout.addWidget(self.status_label)
        
        name_label = QLabel(self.dep_info['name'])
        name_font = QFont()
        name_font.setPointSize(13)
        name_font.setBold(True)
        name_label.setFont(name_font)
        header_layout.addWidget(name_label)
        
        header_layout.addStretch()
        
        # Optional badge
        if self.dep_info['is_optional']:
            optional_label = QLabel("Optional")
            optional_font = QFont()
            optional_font.setPointSize(9)
            optional_label.setFont(optional_font)
            optional_label.setStyleSheet("color: #666; background: #f0f0f0; padding: 4px 8px; border-radius: 4px;")
            header_layout.addWidget(optional_label)
        
        layout.addLayout(header_layout)
        
        # Description
        desc_label = QLabel(self.dep_info['description'])
        desc_font = QFont()
        desc_font.setPointSize(10)
        desc_label.setFont(desc_font)
        desc_label.setStyleSheet("color: #666;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Install button (if not installed and can be installed via pip)
        if (self.dep_info['status'] == 'not_installed' and 
            self.checker.can_install_via_pip(self.dep)):
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            self.install_button = QPushButton("Install via pip")
            self.install_button.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
                QPushButton:pressed {
                    background-color: #0D47A1;
                }
                QPushButton:disabled {
                    background-color: #ccc;
                }
            """)
            self.install_button.clicked.connect(self._install_dependency)
            button_layout.addWidget(self.install_button)
            
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 0)  # Indeterminate
            self.progress_bar.setVisible(False)
            button_layout.addWidget(self.progress_bar)
            
            layout.addLayout(button_layout)
        
        # Instructions (if not installed)
        if self.dep_info['status'] == 'not_installed':
            instructions_text = self.checker.get_install_instructions(self.dep)
            
            instructions_label = QTextEdit()
            instructions_label.setReadOnly(True)
            instructions_label.setPlainText(instructions_text)
            instructions_label.setStyleSheet("""
                QTextEdit {
                    background-color: #f5f5f5;
                    padding: 12px;
                    border-radius: 6px;
                    border: 1px solid #e0e0e0;
                    color: #333;
                    font-family: 'Monospace', 'Courier New', monospace;
                    font-size: 10pt;
                }
            """)
            instructions_label.setMaximumHeight(250)
            layout.addWidget(instructions_label)
        
        # Styling
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        self.setMinimumHeight(120)
    
    def _install_dependency(self):
        """Install the dependency."""
        if not self.dep or self.install_thread:
            return
        
        self.install_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        self.install_thread = InstallThread(self.dep)
        self.install_thread.progress.connect(self._on_progress)
        self.install_thread.finished.connect(self._on_install_finished)
        self.install_thread.start()
    
    def _on_progress(self, message: str):
        """Handle progress updates."""
        self.progress_bar.setFormat(message)
    
    def _on_install_finished(self, success: bool, message: str):
        """Handle installation completion."""
        self.install_thread = None
        self.progress_bar.setVisible(False)
        self.install_button.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Success", f"{self.dep_info['name']} installed successfully!\n\nPlease restart the application.")
            self.status_label.setText("✅")
            self.dep_info['status'] = 'installed'
            # Hide install button
            if hasattr(self, 'install_button'):
                self.install_button.setVisible(False)
        else:
            QMessageBox.warning(self, "Installation Failed", f"Failed to install {self.dep_info['name']}:\n\n{message}")


class DependencyDialog(QDialog):
    """Dialog for checking and installing dependencies."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.checker = DependencyChecker()
        self.setWindowTitle("Dependency Check")
        self.setMinimumSize(800, 600)
        
        self._setup_ui()
        self._check_dependencies()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Dependency Check")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            "The application needs the following dependencies to function properly. "
            "Some can be installed automatically, while others require manual installation."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; padding-bottom: 10px;")
        layout.addWidget(desc_label)
        
        # Status summary
        self.status_label = QLabel()
        status_font = QFont()
        status_font.setPointSize(11)
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("padding: 12px; background: #f5f5f5; border-radius: 6px;")
        layout.addWidget(self.status_label)
        
        # Scroll area for dependency cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(15)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        self.cards_container = scroll_layout
        scroll.setWidget(scroll_widget)
        
        layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        self.refresh_button.clicked.connect(self._check_dependencies)
        button_layout.addWidget(self.refresh_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def _check_dependencies(self):
        """Check all dependencies and update the UI."""
        results = self.checker.check_all()
        
        # Update status label
        required_count = len(results['missing_required'])
        optional_count = len(results['missing_optional'])
        
        if required_count == 0 and optional_count == 0:
            self.status_label.setText("✅ All dependencies are installed!")
            self.status_label.setStyleSheet("padding: 12px; background: #e8f5e9; border-radius: 6px; color: #2e7d32;")
        elif required_count == 0:
            self.status_label.setText(
                f"✅ All required dependencies are installed. "
                f"{optional_count} optional dependency(ies) missing."
            )
            self.status_label.setStyleSheet("padding: 12px; background: #fff3e0; border-radius: 6px; color: #f57c00;")
        else:
            self.status_label.setText(
                f"❌ {required_count} required dependency(ies) missing. "
                f"{optional_count} optional dependency(ies) missing."
            )
            self.status_label.setStyleSheet("padding: 12px; background: #ffebee; border-radius: 6px; color: #c62828;")
        
        # Clear existing cards
        while self.cards_container.count():
            item = self.cards_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add dependency cards
        # Required dependencies first
        for dep_info in results['details']:
            if not dep_info['is_optional']:
                card = DependencyCard(dep_info, self.checker, self)
                self.cards_container.addWidget(card)
        
        # Then optional dependencies
        for dep_info in results['details']:
            if dep_info['is_optional']:
                card = DependencyCard(dep_info, self.checker, self)
                self.cards_container.addWidget(card)
        
        # Add stretch at the end
        self.cards_container.addStretch()
    
    def can_continue(self) -> bool:
        """Check if all required dependencies are installed."""
        results = self.checker.check_all()
        return results['required_installed']

