#!/usr/bin/env python3
"""
UI Scaling Utility

Provides utilities for scaling UI elements (fonts, sizes, margins) based on window size.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QSize
from typing import Tuple, Optional
import math


class UIScaling:
    """Utility class for UI scaling based on window size."""
    
    # Base window size (reference size for 1.0 scale)
    BASE_WIDTH = 1200
    BASE_HEIGHT = 800
    
    # Minimum and maximum scale factors
    MIN_SCALE = 0.6
    MAX_SCALE = 2.0
    
    @staticmethod
    def get_scale_factor(window: Optional[QWidget] = None, width: Optional[int] = None, height: Optional[int] = None) -> float:
        """
        Calculate scale factor based on window size.
        
        Args:
            window: QWidget to get size from
            width: Window width (if window not provided)
            height: Window height (if window not provided)
        
        Returns:
            Scale factor (1.0 = base size, >1.0 = larger, <1.0 = smaller)
        """
        if window:
            size = window.size()
            width = size.width()
            height = size.height()
        
        if not width or not height:
            return 1.0
        
        # Calculate scale based on average of width and height scaling
        width_scale = width / UIScaling.BASE_WIDTH
        height_scale = height / UIScaling.BASE_HEIGHT
        scale = (width_scale + height_scale) / 2.0
        
        # Clamp to min/max
        scale = max(UIScaling.MIN_SCALE, min(UIScaling.MAX_SCALE, scale))
        
        return scale
    
    @staticmethod
    def scale_font(base_point_size: float, window: Optional[QWidget] = None, scale: Optional[float] = None) -> QFont:
        """
        Create a scaled font.
        
        Args:
            base_point_size: Base font point size at reference window size
            window: Window widget to calculate scale from
            scale: Pre-calculated scale factor (optional)
        
        Returns:
            QFont with scaled point size
        """
        if scale is None:
            scale = UIScaling.get_scale_factor(window)
        
        font = QFont()
        scaled_size = int(base_point_size * scale)
        font.setPointSize(max(6, scaled_size))  # Minimum 6pt
        return font
    
    @staticmethod
    def scale_size(base_size: int, window: Optional[QWidget] = None, scale: Optional[float] = None) -> int:
        """
        Scale a size value (width, height, etc.).
        
        Args:
            base_size: Base size at reference window size
            window: Window widget to calculate scale from
            scale: Pre-calculated scale factor (optional)
        
        Returns:
            Scaled size
        """
        if scale is None:
            scale = UIScaling.get_scale_factor(window)
        
        return int(base_size * scale)
    
    @staticmethod
    def scale_margin(base_margin: int, window: Optional[QWidget] = None, scale: Optional[float] = None) -> int:
        """
        Scale a margin/padding value.
        
        Args:
            base_margin: Base margin at reference window size
            window: Window widget to calculate scale from
            scale: Pre-calculated scale factor (optional)
        
        Returns:
            Scaled margin
        """
        return UIScaling.scale_size(base_margin, window, scale)
    
    @staticmethod
    def get_scaled_stylesheet(base_stylesheet: str, window: Optional[QWidget] = None, scale: Optional[float] = None) -> str:
        """
        Scale font sizes in a stylesheet string.
        
        Args:
            base_stylesheet: Stylesheet with base sizes
            window: Window widget to calculate scale from
            scale: Pre-calculated scale factor (optional)
        
        Returns:
            Stylesheet with scaled font sizes
        """
        if scale is None:
            scale = UIScaling.get_scale_factor(window)
        
        # This is a simple implementation - for more complex needs, use regex
        # For now, we'll rely on dynamic font setting rather than stylesheet font-size
        return base_stylesheet


class ScalableWidget:
    """Mixin class for widgets that need to scale with window size."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._base_font_sizes = {}
        self._base_sizes = {}
        self._window_reference = None
    
    def set_window_reference(self, window: QWidget):
        """Set the reference window for scaling calculations."""
        self._window_reference = window
    
    def get_window_reference(self) -> Optional[QWidget]:
        """Get the reference window, traversing up the parent chain if needed."""
        if self._window_reference:
            return self._window_reference
        
        # Try to find main window by traversing parent chain
        widget = self
        for _ in range(10):  # Max 10 levels up
            widget = widget.parent()
            if widget is None:
                break
            if hasattr(widget, 'window') and widget.window():
                return widget.window()
            if widget.isWindow():
                return widget
        
        return None
    
    def update_scaling(self):
        """Update all scaled elements based on current window size."""
        window = self.get_window_reference()
        if not window:
            return
        
        scale = UIScaling.get_scale_factor(window)
        self._apply_scaling(scale)
    
    def _apply_scaling(self, scale: float):
        """Apply scaling to this widget. Override in subclasses."""
        pass
    
    def resizeEvent(self, event):
        """Handle resize events to update scaling."""
        super().resizeEvent(event)
        # Update scaling when widget or window resizes
        self.update_scaling()

