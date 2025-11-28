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

from .ui_scaling import UIScaling


class FanSpeedGauge(QWidget):
    """A circular gauge widget for displaying fan speed in RPM."""
    
    def __init__(self, title: str = "Fan Speed", max_rpm: int = 7000, color: str = "#2196F3"):
        super().__init__()
        self.title = title
        self.max_rpm = max_rpm
        self.color = color
        self.current_rpm = 0
        self.profile_name = None  # Store profile name to display
        
        # Base sizes for scaling
        self._base_min_width = 180
        self._base_min_height = 200
        self._base_rpm_font_size = 18
        self._base_title_font_size = 10
        self._base_profile_font_size = 9
        
        self.setMinimumSize(self._base_min_width, self._base_min_height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.update_scaling()
        
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
    
    def update_scaling(self):
        """Update widget scaling based on window size."""
        window = self.window()
        if not window:
            return
        
        scale = UIScaling.get_scale_factor(window)
        self.setMinimumSize(
            UIScaling.scale_size(self._base_min_width, window, scale),
            UIScaling.scale_size(self._base_min_height, window, scale)
        )
    
    def resizeEvent(self, event):
        """Handle resize to update scaling."""
        super().resizeEvent(event)
        self.update_scaling()
        self.update()  # Repaint with new scaling
    
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
        
        # Draw center text - RPM value (scaled)
        window = self.window()
        scale = UIScaling.get_scale_factor(window) if window else 1.0
        font = UIScaling.scale_font(self._base_rpm_font_size, window, scale)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(text_primary)
        
        # Format RPM with comma separator for readability
        if self.current_rpm > 0:
            rpm_text = f"{self.current_rpm:,}"
        else:
            rpm_text = "--"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, rpm_text)
        
        # Draw "RPM" label below value (scaled)
        font_small = UIScaling.scale_font(8, window, scale)
        painter.setFont(font_small)
        painter.setPen(text_secondary)
        
        rpm_rect = QRectF(rect.x(), rect.y() + rect.height() * 0.6, rect.width(), rect.height() * 0.2)
        painter.drawText(rpm_rect, Qt.AlignmentFlag.AlignCenter, "RPM")
        
        # Draw title at top (scaled)
        title_font = UIScaling.scale_font(self._base_title_font_size, window, scale)
        painter.setFont(title_font)
        painter.setPen(text_secondary)
        
        title_rect = QRectF(0, y_offset - 20, width, 20)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.title)
        
        # Draw percentage label (scaled)
        if self.current_rpm > 0:
            percent_text = f"{percentage * 100:.0f}%"
            percent_font = UIScaling.scale_font(8, window, scale)
            painter.setFont(percent_font)
            percent_rect = QRectF(rect.x(), rect.y() - 25, rect.width(), 20)
            painter.setPen(text_secondary)
            painter.drawText(percent_rect, Qt.AlignmentFlag.AlignCenter, percent_text)
        
        # Draw profile name at bottom (scaled)
        if self.profile_name:
            profile_font = UIScaling.scale_font(self._base_profile_font_size, window, scale)
            profile_font.setBold(True)
            painter.setFont(profile_font)
            painter.setPen(accent_blue)
            
            profile_rect = QRectF(0, height - 25, width, 20)
            painter.drawText(profile_rect, Qt.AlignmentFlag.AlignCenter, self.profile_name)

