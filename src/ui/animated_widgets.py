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
from .ui_scaling import UIScaling


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
        
        # Base sizes for scaling
        self._base_title_font_size = 10
        self._base_value_font_size = 28
        self._base_margin = 20
        self._base_min_height = 140
        
        self._setup_ui()
        self._setup_animations()
        self.update_scaling()
    
    def _setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(5)
        self._base_layout_margins = (20, 15, 20, 15)
        
        # Title label
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet(f"color: {GAME_COLORS['text_secondary']};")
        layout.addWidget(self.title_label)
        
        # Value label
        self.value_label = QLabel("--")
        self.value_label.setStyleSheet(f"color: {self.color};")
        layout.addWidget(self.value_label)
        
        # Unit label (hidden - units shown inline with value)
        if self.unit:
            self.unit_label = QLabel(self.unit)
            unit_font = QFont()
            unit_font.setPointSize(9)
            self.unit_label.setFont(unit_font)
            self.unit_label.setStyleSheet(f"color: {GAME_COLORS['text_dim']};")
            self.unit_label.hide()  # Hide - units shown inline
            layout.addWidget(self.unit_label)
        
        self.setMinimumHeight(self._base_min_height)
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
    
    def update_scaling(self):
        """Update widget scaling based on window size."""
        window = self.window()
        if not window:
            return
        
        scale = UIScaling.get_scale_factor(window)
        
        # Update fonts
        title_font = UIScaling.scale_font(self._base_title_font_size, window, scale)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        
        value_font = UIScaling.scale_font(self._base_value_font_size, window, scale)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        
        # Update layout margins
        layout = self.layout()
        if layout:
            margins = tuple(UIScaling.scale_size(m, window, scale) for m in self._base_layout_margins)
            layout.setContentsMargins(*margins)
        
        # Update minimum height
        self.setMinimumHeight(UIScaling.scale_size(self._base_min_height, window, scale))
    
    def resizeEvent(self, event):
        """Handle resize to update scaling."""
        super().resizeEvent(event)
        self.update_scaling()
    
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
        
        # Store decimals preference for animated updates
        self._display_decimals = decimals
        
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
            # Use stored decimals preference, default to 1
            decimals = getattr(self, '_display_decimals', 1)
            # Combine value and unit on same line
            if self.unit:
                self.value_label.setText(f"{value:.{decimals}f} {self.unit}")
            else:
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
        self._glow_intensity = 0.5  # Glow intensity for neon pulsation
        
        # Fan speed tracking (0-100% or RPM)
        self.cpu_fan_rpm = 0
        self.gpu_fan_rpm = 0
        self.max_rpm = 7000  # Maximum expected RPM for percentage calculation
        
        self._setup_animations()
    
    def _setup_animations(self):
        """Set up rotation and pulse animations."""
        # Rotation animation - will be updated based on CPU fan speed
        self.rotation_animation = QPropertyAnimation(self, b"rotation_angle")
        self.rotation_animation.setDuration(8000)  # Default: 8 seconds per rotation
        self.rotation_animation.setStartValue(0)
        self.rotation_animation.setEndValue(360)
        self.rotation_animation.setLoopCount(-1)
        self.rotation_animation.setEasingCurve(QEasingCurve.Type.Linear)
        self.rotation_animation.start()
        
        # Pulse animation for scale - will be updated based on GPU fan speed
        self.pulse_animation = QPropertyAnimation(self, b"scale_factor")
        self.pulse_animation.setDuration(2000)  # Default: 2 seconds
        self.pulse_animation.setStartValue(0.95)
        self.pulse_animation.setEndValue(1.05)
        self.pulse_animation.setLoopCount(-1)
        self.pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.pulse_animation.start()
        
        # Glow intensity animation for neon pulsation - based on GPU fan speed
        self.glow_animation = QPropertyAnimation(self, b"glow_intensity")
        self.glow_animation.setDuration(2000)  # Default: 2 seconds
        self.glow_animation.setStartValue(0.3)
        self.glow_animation.setEndValue(1.0)
        self.glow_animation.setLoopCount(-1)
        self.glow_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.glow_animation.start()
    
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
    
    def get_glow_intensity(self) -> float:
        """Get current glow intensity."""
        return self._glow_intensity
    
    def set_glow_intensity(self, intensity: float):
        """Set glow intensity (0.0 to 1.0)."""
        self._glow_intensity = max(0.0, min(1.0, intensity))
        self.update()
    
    glow_intensity = pyqtProperty(float, get_glow_intensity, set_glow_intensity)
    
    def set_fan_speeds(self, cpu_rpm: Optional[int] = None, gpu_rpm: Optional[int] = None):
        """
        Update fan speeds and adjust animations accordingly.
        
        Args:
            cpu_rpm: CPU fan speed in RPM (affects rotation speed)
            gpu_rpm: GPU fan speed in RPM (affects pulsation/glow speed)
        """
        if cpu_rpm is not None:
            self.cpu_fan_rpm = cpu_rpm
            self._update_rotation_speed()
        
        if gpu_rpm is not None:
            self.gpu_fan_rpm = gpu_rpm
            self._update_pulsation_speed()
            self._update_glow_speed()
    
    def _update_rotation_speed(self):
        """Update rotation animation speed based on CPU fan speed."""
        # Calculate CPU fan speed percentage (0-100%)
        cpu_pct = min(100, (self.cpu_fan_rpm / self.max_rpm) * 100) if self.max_rpm > 0 else 0
        
        # Rotation speed: faster fan = faster rotation
        # Base duration: 8 seconds at 0%, scaling down to 1 second at 100%
        # Formula: duration = 8 - (cpu_pct / 100) * 7
        # So at 0%: 8s, at 100%: 1s
        min_duration = 1000  # 1 second minimum (very fast)
        max_duration = 8000  # 8 seconds maximum (slow)
        duration = max(min_duration, max_duration - (cpu_pct / 100.0) * (max_duration - min_duration))
        
        # Update animation
        if self.rotation_animation:
            current_angle = self._rotation_angle
            self.rotation_animation.setDuration(int(duration))
            # Restart animation to apply new duration
            self.rotation_animation.stop()
            self.rotation_animation.start()
    
    def _update_pulsation_speed(self):
        """Update pulsation animation speed based on GPU fan speed."""
        # Calculate GPU fan speed percentage (0-100%)
        gpu_pct = min(100, (self.gpu_fan_rpm / self.max_rpm) * 100) if self.max_rpm > 0 else 0
        
        # Pulsation speed: faster fan = faster pulsation
        # Base duration: 3 seconds at 0%, scaling down to 0.5 seconds at 100%
        min_duration = 500   # 0.5 seconds minimum (very fast)
        max_duration = 3000  # 3 seconds maximum (slow)
        duration = max(min_duration, max_duration - (gpu_pct / 100.0) * (max_duration - min_duration))
        
        # Update animation
        if self.pulse_animation:
            self.pulse_animation.setDuration(int(duration))
            # Restart animation to apply new duration
            self.pulse_animation.stop()
            self.pulse_animation.start()
    
    def _update_glow_speed(self):
        """Update glow pulsation speed based on GPU fan speed."""
        # Calculate GPU fan speed percentage (0-100%)
        gpu_pct = min(100, (self.gpu_fan_rpm / self.max_rpm) * 100) if self.max_rpm > 0 else 0
        
        # Glow pulsation speed: faster fan = faster glow
        # Same speed as scale pulsation for consistency
        min_duration = 500   # 0.5 seconds minimum (very fast)
        max_duration = 3000  # 3 seconds maximum (slow)
        duration = max(min_duration, max_duration - (gpu_pct / 100.0) * (max_duration - min_duration))
        
        # Update animation
        if self.glow_animation:
            self.glow_animation.setDuration(int(duration))
            # Restart animation to apply new duration
            self.glow_animation.stop()
            self.glow_animation.start()
    
    def paintEvent(self, event):
        """Paint animated icon with neon glow effect."""
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
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        # Calculate glow size based on intensity (pulsating neon glow)
        base_glow_size = max(pixmap.width(), pixmap.height()) * 0.15
        glow_size = base_glow_size * (0.5 + self._glow_intensity * 0.5)
        
        # Draw multiple glow layers for neon effect
        glow_colors = [
            (GAME_COLORS['accent_blue'], 255 * self._glow_intensity * 0.8),
            (GAME_COLORS['accent_cyan'], 255 * self._glow_intensity * 0.6),
            (GAME_COLORS['accent_blue'], 255 * self._glow_intensity * 0.4),
        ]
        
        for i, (color_hex, alpha) in enumerate(glow_colors):
            glow_color = QColor(color_hex)
            glow_color.setAlpha(int(alpha))
            
            # Create radial gradient for smooth glow
            gradient = QRadialGradient(center_x, center_y, glow_size * (i + 1))
            gradient.setColorAt(0.0, glow_color)
            gradient.setColorAt(0.5, QColor(color_hex, int(alpha * 0.5)))
            gradient.setColorAt(1.0, QColor(color_hex, 0))
            
            pen_width = int(3 + i * 2)
            painter.setPen(QPen(QBrush(gradient), pen_width))
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            
            # Draw glow circles
            glow_rect_x = center_x - (pixmap.width() / 2 + glow_size * (i + 1))
            glow_rect_y = center_y - (pixmap.height() / 2 + glow_size * (i + 1))
            glow_rect_size = pixmap.width() + glow_size * 2 * (i + 1)
            painter.drawEllipse(
                int(glow_rect_x),
                int(glow_rect_y),
                int(glow_rect_size),
                int(glow_rect_size)
            )
        
        # Apply rotation
        painter.translate(center_x, center_y)
        painter.rotate(self.rotation_angle)
        painter.translate(-center_x, -center_y)
        
        # Draw the icon
        painter.drawPixmap(x, y, pixmap)

