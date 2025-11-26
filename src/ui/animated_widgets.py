#!/usr/bin/env python3
"""
Animated Widgets

Game-style animated widgets with glow effects, smooth transitions, and particle effects.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QRectF, pyqtProperty
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QRadialGradient, QLinearGradient
from typing import Optional
import math

from .game_style_theme import GAME_COLORS
from .particle_effects import ParticleOverlay


class AnimatedMetricCard(QWidget):
    """Animated metric card with glow effects and smooth transitions."""
    
    def __init__(self, title: str, unit: str = "", color: str = GAME_COLORS['accent_blue']):
        super().__init__()
        self.title = title
        self.unit = unit
        self.color = color
        self.value = None
        self._animated_value = 0.0  # Private attribute to avoid recursion
        self._glow_intensity = 0.0
        
        # Animation properties
        self.value_animation = None
        self.glow_animation = None
        
        self._setup_ui()
        self._setup_animations()
    
    def _setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(5)
        
        # Title label
        self.title_label = QLabel(self.title)
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"color: {GAME_COLORS['text_secondary']};")
        layout.addWidget(self.title_label)
        
        # Value label
        self.value_label = QLabel("--")
        value_font = QFont()
        value_font.setPointSize(28)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setStyleSheet(f"color: {self.color};")
        layout.addWidget(self.value_label)
        
        # Unit label
        if self.unit:
            self.unit_label = QLabel(self.unit)
            unit_font = QFont()
            unit_font.setPointSize(9)
            self.unit_label.setFont(unit_font)
            self.unit_label.setStyleSheet(f"color: {GAME_COLORS['text_dim']};")
            layout.addWidget(self.unit_label)
        
        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Game-style styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {GAME_COLORS['bg_card']};
                border: 2px solid {GAME_COLORS['border']};
                border-radius: 12px;
            }}
        """)
        
        # Add particle overlay for high values
        self.particle_overlay = ParticleOverlay(self)
        self.particle_overlay.set_threshold(70.0)
        self.particle_overlay.set_max_value(100.0)
    
    def _setup_animations(self):
        """Set up value and glow animations."""
        # Value animation for smooth transitions
        self.value_animation = QPropertyAnimation(self, b"animated_value")
        self.value_animation.setDuration(500)
        self.value_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Glow animation
        self.glow_animation = QPropertyAnimation(self, b"glow_intensity")
        self.glow_animation.setDuration(1500)
        self.glow_animation.setLoopCount(-1)  # Infinite loop
        self.glow_animation.setStartValue(0.3)
        self.glow_animation.setEndValue(1.0)
        self.glow_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.glow_animation.start()
    
    def get_glow_intensity(self) -> float:
        """Get current glow intensity."""
        return self._glow_intensity
    
    def set_glow_intensity(self, intensity: float):
        """Set glow intensity."""
        self._glow_intensity = intensity
        self.update()  # Trigger repaint
    
    glow_intensity = pyqtProperty(float, get_glow_intensity, set_glow_intensity)
    
    def set_value(self, value: Optional[float], decimals: int = 1, text: str = None):
        """Update the displayed value with animation."""
        if text is not None:
            self.value_label.setText(text)
            self.value = None
            if self.value_animation:
                self.value_animation.stop()
            self._animated_value = 0
            if hasattr(self, 'particle_overlay'):
                self.particle_overlay.set_value(0)
            return
        
        if value is None:
            self.value_label.setText("--")
            self.value = None
            if self.value_animation:
                self.value_animation.stop()
            self._animated_value = 0
            if hasattr(self, 'particle_overlay'):
                self.particle_overlay.set_value(0)
            return
        
        # Animate value change
        old_value = self._animated_value if self.value is not None else value
        self.value = value
        
        if self.value_animation:
            self.value_animation.stop()
        
        self.value_animation.setStartValue(old_value)
        self.value_animation.setEndValue(value)
        self.value_animation.valueChanged.connect(self._on_value_animated)
        self.value_animation.start()
        
        # Update particle overlay immediately
        if hasattr(self, 'particle_overlay'):
            self.particle_overlay.set_value(abs(value))
    
    def get_animated_value(self) -> float:
        """Get current animated value."""
        return self._animated_value
    
    def set_animated_value(self, value: float):
        """Set animated value and update display."""
        self._animated_value = value
        if self.value is not None:
            # Determine decimals based on value
            decimals = 1 if abs(value) < 100 else 0
            self.value_label.setText(f"{value:.{decimals}f}")
            
            # Update particle effects for high values
            if hasattr(self, 'particle_overlay'):
                self.particle_overlay.set_value(abs(value))
        self.update()
    
    animated_value = pyqtProperty(float, get_animated_value, set_animated_value)
    
    def _on_value_animated(self, animated_val):
        """Update display as value animates (deprecated, use set_animated_value)."""
        self.set_animated_value(animated_val)
    
    def paintEvent(self, event):
        """Paint glow effect."""
        super().paintEvent(event)
        
        if self.value is None or self.value == 0:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw glow effect based on value
        glow_color = QColor(self.color)
        glow_color.setAlpha(int(50 * self._glow_intensity))
        
        pen = QPen(glow_color, 3)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Draw glowing border
        rect = self.rect().adjusted(2, 2, -2, -2)
        painter.drawRoundedRect(rect, 10, 10)


class AnimatedIcon(QWidget):
    """Animated application icon with rotation and pulse effects."""
    
    def __init__(self, icon_path: str, parent=None):
        super().__init__(parent)
        self.icon_path = icon_path
        self._rotation_angle = 0.0  # Private attribute to avoid recursion
        self._scale_factor = 1.0    # Private attribute to avoid recursion
        self._setup_animations()
    
    def _setup_animations(self):
        """Set up rotation and pulse animations."""
        # Rotation animation
        self.rotation_animation = QPropertyAnimation(self, b"rotation_angle")
        self.rotation_animation.setDuration(8000)  # 8 seconds per rotation
        self.rotation_animation.setStartValue(0)
        self.rotation_animation.setEndValue(360)
        self.rotation_animation.setLoopCount(-1)
        self.rotation_animation.setEasingCurve(QEasingCurve.Type.Linear)
        self.rotation_animation.start()
        
        # Pulse animation
        self.pulse_animation = QPropertyAnimation(self, b"scale_factor")
        self.pulse_animation.setDuration(2000)
        self.pulse_animation.setStartValue(0.95)
        self.pulse_animation.setEndValue(1.05)
        self.pulse_animation.setLoopCount(-1)
        self.pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.pulse_animation.start()
    
    def get_rotation_angle(self) -> float:
        return self._rotation_angle
    
    def set_rotation_angle(self, angle: float):
        self._rotation_angle = angle
        self.update()
    
    rotation_angle = pyqtProperty(float, get_rotation_angle, set_rotation_angle)
    
    def get_scale_factor(self) -> float:
        return self._scale_factor
    
    def set_scale_factor(self, scale: float):
        self._scale_factor = scale
        self.update()
    
    scale_factor = pyqtProperty(float, get_scale_factor, set_scale_factor)
    
    def paintEvent(self, event):
        """Paint animated icon."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Load and scale icon
        from PyQt6.QtGui import QPixmap
        pixmap = QPixmap(self.icon_path)
        if pixmap.isNull():
            return
        
        # Apply scale
        size = int(min(self.width(), self.height()) * self.scale_factor)
        pixmap = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
        
        # Center the pixmap
        x = (self.width() - pixmap.width()) // 2
        y = (self.height() - pixmap.height()) // 2
        
        # Apply rotation
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.rotation_angle)
        painter.translate(-self.width() / 2, -self.height() / 2)
        
        # Draw with glow effect
        glow_color = QColor(GAME_COLORS['accent_blue'])
        glow_color.setAlpha(30)
        painter.setPen(QPen(glow_color, 5))
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        painter.drawEllipse(x - 5, y - 5, pixmap.width() + 10, pixmap.height() + 10)
        
        painter.drawPixmap(x, y, pixmap)

