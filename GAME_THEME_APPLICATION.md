# Game-Style Theme Application Guide

## Overview
The game-style dark theme with neon accents has been applied across the application. This document describes what has been done and what remains.

## ✅ Completed

### 1. Core Theme System
- `src/ui/game_style_theme.py` - Complete theme definitions
- Color palette with neon accents
- CSS styles for all widget types

### 2. Dashboard (System Monitor)
- Fully themed with game-style colors
- Animated widgets with particle effects
- Responsive layout
- Preferences system

### 3. Graph Widget
- Dark background with game-style colors
- Neon-colored plot lines
- Styled axes and legend

### 4. Particle Effects
- High-value indicators (>70%)
- Smooth particle animations
- Color-coded by intensity

### 5. Main Window
- Dark theme background
- Game-style tabs
- System tray integration

## 🚧 In Progress / To Complete

### Tabs Needing Full Theme Application

1. **Fan Curve Editor** (`src/ui/fan_curve_editor.py`)
   - Status: Partially themed (title done)
   - Need: Apply theme to dropdowns, buttons, graph, controls

2. **Fan Status Tab** (`src/ui/fan_status_tab.py`)
   - Status: Not yet themed
   - Need: Dark background, neon colors for graphs and metrics

3. **Test Fans Tab** (`src/ui/test_fans_tab.py`)
   - Status: Not yet themed
   - Need: Game-style tiles, buttons, sliders

4. **Log Viewer Tab** (`src/ui/log_viewer_tab.py`)
   - Status: Not yet themed
   - Need: Dark theme, neon accents for filter controls

5. **History Tab** (`src/ui/history_tab.py`)
   - Status: Not yet themed
   - Need: Dark theme for table, styled controls

## Application Pattern

To apply theme to a tab/widget:

1. Import theme:
```python
from .game_style_theme import GAME_COLORS, GAME_STYLES
```

2. Apply to widget:
```python
widget.setStyleSheet(GAME_STYLES['widget'])
```

3. Update colors:
- Replace `#333`, `#666` with `GAME_COLORS['text_primary']`, `GAME_COLORS['text_secondary']`
- Replace white backgrounds with `GAME_COLORS['bg_medium']` or `GAME_COLORS['bg_card']`
- Replace accent colors with game-style neon colors

4. Update buttons:
- Use `GAME_STYLES['button']` for consistent button styling

5. Update dropdowns/inputs:
- Use `GAME_STYLES['combobox']` and `GAME_STYLES['spinbox']`

6. Update graphs (PyQtGraph):
```python
graph.setBackground(pg.mkColor(GAME_COLORS['bg_card']))
plot.setPen(pg.mkPen(color=GAME_COLORS['accent_blue'], width=2.5))
```

## Color Reference

- Backgrounds: `bg_dark` (#0a0a0f), `bg_medium` (#1a1a2e), `bg_card` (#16213e)
- Text: `text_primary` (#ffffff), `text_secondary` (#b0b0b0)
- Accents: `accent_blue` (#00d4ff), `accent_red` (#ff3366), `accent_green` (#00ff88), etc.
- Borders: `border` (#2a2a4e)

## Notes

- All animations use PyQt6's built-in framework
- Particle effects activate at >70% values
- Preferences persist user visibility choices
- Responsive layout adapts to window size

