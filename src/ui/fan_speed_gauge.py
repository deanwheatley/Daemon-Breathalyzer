#!/usr/bin/env python3
"""
Fan Speed Gauge Widget

A circular gauge widget for displaying fan speeds.
"""

from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from typing import Optional
import math


class FanSpeedGauge(QWidget):
    """A circular gauge widget for displaying fan speed in RPM."""
    
    def __init__(self, title: str = "Fan Speed", max_rpm: int = 7000, color: str = "#2196F3"):
        super().__init__()
        self.title = title
        self.max_rpm = max_rpm
        self.color = color
        self.current_rpm = 0
        self.profile_name = None  # Store profile name to display
        self.setMinimumSize(180, 200)  # Increased height for profile name
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Game-style styling
        from .game_style_theme import GAME_COLORS
        self.game_colors = GAME_COLORS
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {GAME_COLORS['bg_card']};
                border: 2px solid {GAME_COLORS['border']};
                border-radius: 12px;
            }}
        """)
    
    def set_rpm(self, rpm: Optional[int]):
        """Set the current RPM value."""
        if rpm is None:
            self.current_rpm = 0
        else:
            self.current_rpm = max(0, min(rpm, self.max_rpm))
        self.update()  # Trigger repaint
    
    def set_profile_name(self, profile_name: Optional[str]):
        """Set the profile name to display."""
        self.profile_name = profile_name
        self.update()  # Trigger repaint
    
    def paintEvent(self, event):
        """Paint the gauge."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get widget dimensions
        width = self.width()
        height = self.height()
        size = min(width, height) - 20
        x_offset = (width - size) // 2
        y_offset = (height - size) // 2
        
        # Draw background circle
        rect = QRectF(x_offset, y_offset, size, size)
        
        # Get game colors
        from .game_style_theme import GAME_COLORS
        bg_color = QColor(GAME_COLORS['bg_medium'])
        border_color = QColor(GAME_COLORS['border'])
        text_primary = QColor(GAME_COLORS['text_primary'])
        text_secondary = QColor(GAME_COLORS['text_secondary'])
        accent_blue = QColor(GAME_COLORS['accent_blue'])
        
        # Background arc
        pen = QPen(border_color, 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 45 * 16, 270 * 16)  # 270 degrees starting at 45
        
        # Calculate percentage
        percentage = (self.current_rpm / self.max_rpm) if self.max_rpm > 0 else 0
        percentage = min(1.0, max(0.0, percentage))
        
        # Draw active arc with game-style color
        active_color = QColor(self.color)
        pen = QPen(active_color, 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Draw arc from 45 degrees, covering percentage of 270 degrees
        span_angle = int(270 * percentage * 16)
        painter.drawArc(rect, 45 * 16, span_angle)
        
        # Draw center text - RPM value
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(text_primary)
        
        # Format RPM with comma separator for readability
        if self.current_rpm > 0:
            rpm_text = f"{self.current_rpm:,}"
        else:
            rpm_text = "--"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, rpm_text)
        
        # Draw "RPM" label below value
        font_small = QFont()
        font_small.setPointSize(8)
        painter.setFont(font_small)
        painter.setPen(text_secondary)
        
        rpm_rect = QRectF(rect.x(), rect.y() + rect.height() * 0.6, rect.width(), rect.height() * 0.2)
        painter.drawText(rpm_rect, Qt.AlignmentFlag.AlignCenter, "RPM")
        
        # Draw title at top
        title_font = QFont()
        title_font.setPointSize(10)
        painter.setFont(title_font)
        painter.setPen(text_secondary)
        
        title_rect = QRectF(0, y_offset - 20, width, 20)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.title)
        
        # Draw percentage label
        if self.current_rpm > 0:
            percent_text = f"{percentage * 100:.0f}%"
            percent_rect = QRectF(rect.x(), rect.y() - 25, rect.width(), 20)
            painter.setPen(text_secondary)
            painter.drawText(percent_rect, Qt.AlignmentFlag.AlignCenter, percent_text)
        
        # Draw profile name at bottom
        if self.profile_name:
            profile_font = QFont()
            profile_font.setPointSize(9)
            profile_font.setBold(True)
            painter.setFont(profile_font)
            painter.setPen(accent_blue)
            
            profile_rect = QRectF(0, height - 25, width, 20)
            painter.drawText(profile_rect, Qt.AlignmentFlag.AlignCenter, self.profile_name)

