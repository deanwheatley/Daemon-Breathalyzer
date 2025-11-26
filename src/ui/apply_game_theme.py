#!/usr/bin/env python3
"""
Apply Game Theme Helper

Helper functions to apply game-style theme to all UI components.
"""

from PyQt6.QtWidgets import QWidget
from .game_style_theme import GAME_COLORS, GAME_STYLES


def apply_game_theme_to_widget(widget: QWidget):
    """Apply game-style theme to a widget."""
    widget.setStyleSheet(GAME_STYLES.get('widget', ''))
    return widget


def apply_game_theme_to_all_tabs():
    """Apply game-style theme to all tabs."""
    # This is called during tab creation
    pass

