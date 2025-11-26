#!/usr/bin/env python3
"""
Game Style Theme

Provides game-like styling with dark theme, neon accents, and animations.
"""

# Game-style color palette
GAME_COLORS = {
    'bg_dark': '#0a0a0f',
    'bg_medium': '#1a1a2e',
    'bg_card': '#16213e',
    'bg_glow': '#0f3460',
    'accent_blue': '#00d4ff',
    'accent_cyan': '#00ffea',
    'accent_purple': '#b300ff',
    'accent_pink': '#ff00d4',
    'accent_green': '#00ff88',
    'accent_red': '#ff3366',
    'accent_orange': '#ff8800',
    'text_primary': '#ffffff',
    'text_secondary': '#b0b0b0',
    'text_dim': '#666666',
    'border': '#2a2a4e',
    'border_glow': '#00d4ff',
}

# Game-style CSS styles
GAME_STYLES = {
    'main_window': f"""
        QMainWindow {{
            background-color: {GAME_COLORS['bg_dark']};
            color: {GAME_COLORS['text_primary']};
        }}
    """,
    
    'tab_widget': f"""
        QTabWidget::pane {{
            border: 2px solid {GAME_COLORS['border']};
            background: {GAME_COLORS['bg_medium']};
            border-radius: 8px;
        }}
        QTabBar::tab {{
            background: {GAME_COLORS['bg_card']};
            color: {GAME_COLORS['text_secondary']};
            padding: 12px 24px;
            margin-right: 2px;
            border: 1px solid {GAME_COLORS['border']};
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            font-size: 13px;
        }}
        QTabBar::tab:selected {{
            background: {GAME_COLORS['bg_medium']};
            color: {GAME_COLORS['accent_blue']};
            font-weight: bold;
            border-bottom: 2px solid {GAME_COLORS['accent_blue']};
            box-shadow: 0 0 10px {GAME_COLORS['accent_blue']};
        }}
        QTabBar::tab:hover:!selected {{
            background: {GAME_COLORS['bg_glow']};
            color: {GAME_COLORS['text_primary']};
        }}
    """,
    
    'metric_card': f"""
        QWidget {{
            background-color: {GAME_COLORS['bg_card']};
            border: 2px solid {GAME_COLORS['border']};
            border-radius: 12px;
        }}
        QWidget:hover {{
            border: 2px solid {GAME_COLORS['accent_blue']};
            box-shadow: 0 0 15px {GAME_COLORS['accent_blue']};
        }}
    """,
    
    'button': f"""
        QPushButton {{
            background-color: {GAME_COLORS['bg_card']};
            color: {GAME_COLORS['text_primary']};
            border: 2px solid {GAME_COLORS['accent_blue']};
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {GAME_COLORS['accent_blue']};
            box-shadow: 0 0 15px {GAME_COLORS['accent_blue']};
        }}
        QPushButton:pressed {{
            background-color: {GAME_COLORS['accent_cyan']};
        }}
    """,
    
    'widget': f"""
        QWidget {{
            background-color: {GAME_COLORS['bg_medium']};
            color: {GAME_COLORS['text_primary']};
        }}
    """,
    
    'groupbox': f"""
        QGroupBox {{
            background-color: {GAME_COLORS['bg_card']};
            color: {GAME_COLORS['text_primary']};
            border: 2px solid {GAME_COLORS['border']};
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            color: {GAME_COLORS['accent_blue']};
        }}
    """,
    
    'label': f"""
        QLabel {{
            color: {GAME_COLORS['text_primary']};
        }}
    """,
    
    'combobox': f"""
        QComboBox {{
            background-color: {GAME_COLORS['bg_card']};
            color: {GAME_COLORS['text_primary']};
            border: 2px solid {GAME_COLORS['border']};
            border-radius: 6px;
            padding: 6px 12px;
        }}
        QComboBox:hover {{
            border: 2px solid {GAME_COLORS['accent_blue']};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border: 1px solid {GAME_COLORS['accent_blue']};
            width: 8px;
            height: 8px;
        }}
    """,
    
    'spinbox': f"""
        QSpinBox {{
            background-color: {GAME_COLORS['bg_card']};
            color: {GAME_COLORS['text_primary']};
            border: 2px solid {GAME_COLORS['border']};
            border-radius: 6px;
            padding: 4px;
        }}
        QSpinBox:hover {{
            border: 2px solid {GAME_COLORS['accent_blue']};
        }}
    """,
    
    'scrollbar': f"""
        QScrollBar:vertical {{
            background: {GAME_COLORS['bg_card']};
            width: 12px;
            border: none;
        }}
        QScrollBar::handle:vertical {{
            background: {GAME_COLORS['accent_blue']};
            min-height: 20px;
            border-radius: 6px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {GAME_COLORS['accent_cyan']};
        }}
    """,
}

