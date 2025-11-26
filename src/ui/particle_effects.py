#!/usr/bin/env python3
"""
Particle Effects

Particle effects for high CPU/GPU values with game-style visuals.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF, QPropertyAnimation, pyqtProperty, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from typing import List, Tuple
import random
import math

from .game_style_theme import GAME_COLORS


class Particle:
    """Single particle for effects."""
    
    def __init__(self, x: float, y: float, color: QColor):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-3, -1)
        self.life = 1.0
        self.decay = random.uniform(0.01, 0.03)
        self.color = color
        self.size = random.uniform(2, 5)
    
    def update(self):
        """Update particle position and life."""
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1  # Gravity
        self.life -= self.decay
        return self.life > 0
    
    def draw(self, painter: QPainter):
        """Draw the particle."""
        alpha = int(255 * self.life)
        color = QColor(self.color)
        color.setAlpha(alpha)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QPointF(self.x, self.y), self.size, self.size)


class ParticleSystem(QWidget):
    """Particle system for visual effects on high values."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles: List[Particle] = []
        self.active = False
        self.intensity = 0.0  # 0.0 to 1.0
        self.base_color = QColor(GAME_COLORS['accent_red'])
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_particles)
        self.timer.start(16)  # ~60 FPS
        
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
    
    def set_intensity(self, intensity: float):
        """Set particle intensity (0.0 to 1.0)."""
        self.intensity = max(0.0, min(1.0, intensity))
        self.active = self.intensity > 0.1
        if self.active and not self.timer.isActive():
            self.timer.start()
    
    def set_color(self, color: QColor):
        """Set particle color."""
        self.base_color = color
    
    def _update_particles(self):
        """Update all particles."""
        if not self.active:
            self.particles.clear()
            self.update()
            return
        
        # Emit new particles based on intensity
        if len(self.particles) < 50 * self.intensity:
            width = self.width()
            height = self.height()
            # Emit from top center
            x = width / 2 + random.uniform(-20, 20)
            y = height * 0.1 + random.uniform(-10, 10)
            
            # Vary color based on intensity
            color = QColor(self.base_color)
            hue_variation = random.randint(-20, 20)
            color.setHsv(
                (color.hue() + hue_variation) % 360,
                min(255, color.saturation() + random.randint(0, 50)),
                min(255, color.value() + random.randint(0, 50))
            )
            
            self.particles.append(Particle(x, y, color))
        
        # Update existing particles
        self.particles = [p for p in self.particles if p.update()]
        
        if self.particles or self.active:
            self.update()
    
    def paintEvent(self, event):
        """Paint particles."""
        if not self.particles:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        for particle in self.particles:
            particle.draw(painter)


class ParticleOverlay(QWidget):
    """Overlay widget that adds particle effects to parent widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.particle_system = ParticleSystem(self)
        self.value = 0.0
        self.threshold = 70.0  # Show particles above 70%
        self.max_value = 100.0
        
        # Set overlay to cover parent and make transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        if parent:
            parent.installEventFilter(self)
            self._resize_to_parent()
    
    def _resize_to_parent(self):
        """Resize to match parent widget."""
        if self.parent():
            self.setGeometry(0, 0, self.parent().width(), self.parent().height())
            if self.particle_system:
                self.particle_system.setGeometry(0, 0, self.parent().width(), self.parent().height())
    
    def eventFilter(self, obj, event):
        """Filter parent resize events."""
        if obj == self.parent() and event.type() == event.Type.Resize:
            self._resize_to_parent()
        return super().eventFilter(obj, event)
    
    def set_threshold(self, threshold: float):
        """Set the threshold for showing particles."""
        self.threshold = threshold
    
    def set_max_value(self, max_value: float):
        """Set the maximum value for intensity calculation."""
        self.max_value = max_value
    
    def set_value(self, value: float):
        """Update value and particle intensity."""
        self.value = value
        if value > self.threshold:
            intensity = (value - self.threshold) / (self.max_value - self.threshold)
            intensity = min(1.0, intensity)  # Clamp to 1.0
            self.particle_system.set_intensity(intensity)
            
            # Set color based on value
            if value > 90:
                color = QColor(GAME_COLORS['accent_red'])
            elif value > 80:
                color = QColor(GAME_COLORS['accent_orange'])
            else:
                color = QColor(GAME_COLORS['accent_orange'])
            
            self.particle_system.set_color(color)
        else:
            self.particle_system.set_intensity(0.0)
    
    def resizeEvent(self, event):
        """Handle resize."""
        super().resizeEvent(event)
        if self.particle_system:
            self.particle_system.setGeometry(0, 0, self.width(), self.height())

