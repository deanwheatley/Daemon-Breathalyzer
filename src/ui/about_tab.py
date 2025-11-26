#!/usr/bin/env python3
"""
About Tab

Displays information about the application, links to GitHub, contact information, and LinkedIn.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QDesktopServices, QPixmap
from pathlib import Path
from typing import Optional

from .game_style_theme import GAME_COLORS, GAME_STYLES


class AboutTab(QWidget):
    """Tab displaying application information and links."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI."""
        # Apply game-style theme
        self.setStyleSheet(GAME_STYLES['widget'])
        
        layout = QVBoxLayout(self)
        layout.setSpacing(30)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Title
        title = QLabel("Daemon Breathalyzer")
        title_font = QFont()
        title_font.setPointSize(32)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {GAME_COLORS['accent_blue']}; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("ASUS Fan Control & System Monitor")
        subtitle_font = QFont()
        subtitle_font.setPointSize(16)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet(f"color: {GAME_COLORS['text_secondary']}; margin-bottom: 20px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Daemon image
        daemon_image_label = self._create_daemon_image()
        if daemon_image_label:
            layout.addWidget(daemon_image_label)
            layout.addSpacing(20)
        
        # Description
        description = QLabel(
            "A modern, game-style system monitoring and fan control application "
            "for ASUS laptops running Linux. Monitor CPU, GPU, memory, network, "
            "and control fan curves with an intuitive interface."
        )
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {GAME_COLORS['text_primary']}; font-size: 14px; padding: 20px;")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)
        
        layout.addSpacing(40)
        
        # Links section
        links_container = QWidget()
        links_layout = QVBoxLayout(links_container)
        links_layout.setSpacing(20)
        links_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # GitHub link
        github_layout = self._create_link_section(
            "GitHub Repository:",
            "https://github.com/deanwheatley/asus-control/",
            "View on GitHub"
        )
        links_layout.addLayout(github_layout)
        
        layout.addSpacing(20)
        
        # Contact section
        contact_container = QWidget()
        contact_layout = QVBoxLayout(contact_container)
        contact_layout.setSpacing(20)
        contact_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        contact_label = QLabel("Contact Information")
        contact_label.setStyleSheet(f"color: {GAME_COLORS['accent_blue']}; font-size: 18px; font-weight: bold;")
        contact_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        contact_layout.addWidget(contact_label)
        
        # Email
        email_layout = self._create_link_section(
            "Email:",
            "mailto:deanwheatley@hotmail.com",
            "deanwheatley@hotmail.com",
            display_name="Dean Wheatley"
        )
        contact_layout.addLayout(email_layout)
        
        layout.addSpacing(20)
        
        # LinkedIn link
        linkedin_layout = self._create_link_section(
            "LinkedIn:",
            "https://www.linkedin.com/in/dean-wheatley-8944511a/",
            "View LinkedIn Profile"
        )
        contact_layout.addLayout(linkedin_layout)
        
        links_layout.addWidget(contact_container)
        
        layout.addWidget(links_container)
        
        layout.addStretch()
        
        # Version/Copyright
        version_label = QLabel("Version 1.0.0")
        version_label.setStyleSheet(f"color: {GAME_COLORS['text_dim']}; font-size: 12px;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        copyright_label = QLabel("© 2025 Dean Wheatley")
        copyright_label.setStyleSheet(f"color: {GAME_COLORS['text_dim']}; font-size: 12px;")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright_label)
    
    def _create_link_section(self, label_text: str, url: str, button_text: str, display_name: Optional[str] = None) -> QHBoxLayout:
        """Create a horizontal layout with label and link button."""
        layout = QHBoxLayout()
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Label
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {GAME_COLORS['text_primary']}; font-size: 14px; min-width: 150px;")
        layout.addWidget(label)
        
        # Display name if provided
        if display_name:
            name_label = QLabel(display_name)
            name_label.setStyleSheet(f"color: {GAME_COLORS['text_secondary']}; font-size: 14px;")
            layout.addWidget(name_label)
        
        # Link button
        link_button = QPushButton(button_text)
        link_button.setStyleSheet(GAME_STYLES['button'])
        link_button.clicked.connect(lambda: self._open_url(url))
        layout.addWidget(link_button)
        
        return layout
    
    def _open_url(self, url: str):
        """Open a URL in the default browser."""
        QDesktopServices.openUrl(QUrl(url))
    
    def _create_daemon_image(self) -> Optional[QLabel]:
        """Create a QLabel displaying the daemon image."""
        # Find the project root (3 levels up from src/ui/about_tab.py)
        project_root = Path(__file__).parent.parent.parent
        daemon_image_path = project_root / "img" / "daemon.png"
        
        if not daemon_image_path.exists():
            return None
        
        # Create label for image
        image_label = QLabel()
        
        # Load and scale the pixmap
        pixmap = QPixmap(str(daemon_image_path))
        if pixmap.isNull():
            return None
        
        # Scale image to reasonable size (max 300x300, maintain aspect ratio)
        max_size = 300
        if pixmap.width() > max_size or pixmap.height() > max_size:
            pixmap = pixmap.scaled(
                max_size, max_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setStyleSheet("background: transparent; padding: 10px;")
        
        return image_label

