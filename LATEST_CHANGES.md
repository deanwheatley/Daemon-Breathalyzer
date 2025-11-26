# Latest Changes - Daemon Breathalyzer

## Recent Updates (Latest Session)

### ✅ Fan Curve Designer Redesign

#### Major UI/UX Overhaul
- ✅ Redesigned "Fan Curves" tab as dedicated "Fan Curve Designer"
- ✅ Removed "Apply" functionality (moved to separate screen - coming soon)
- ✅ Removed "Test Fan" functionality from designer
- ✅ Focused workflow: Design → Load → Save only
- ✅ Modern, intuitive UI with grouped Load/Save sections

#### Active Curve Protection
- ✅ Prevents saving over currently active (applied) curves
- ✅ Intelligent detection of active curves across all profiles
- ✅ User prompts: "Save As", "Discard", or "Cancel"
- ✅ Protects users from accidentally modifying curves in use

#### Enhanced Save Functionality
- ✅ "Save Curve" button for quick saves to loaded profile
- ✅ "Save As" button for creating new profiles
- ✅ Profile tracking - remembers currently loaded profile
- ✅ Automatic profile dropdown refresh after saves

#### Code Cleanup
- ✅ Removed 369 lines of unused code (Apply/Test functionality)
- ✅ Added 297 lines of focused, clean code
- ✅ Fixed all broken signal connections
- ✅ Removed orphaned methods and references

#### Documentation Updates
- ✅ Updated README.md and FEATURES.md
- ✅ Updated in-app help (help_tab.py, help_dialog.py)
- ✅ Updated profile manager messages
- ✅ All references to "Fan Curve Editor" changed to "Fan Curve Designer"

**Files Modified:**
- `src/ui/fan_curve_editor.py` - Complete redesign
- `src/ui/main_window.py` - Tab renamed, signal connections fixed
- `src/ui/help_tab.py` - Help content updated
- `src/ui/help_dialog.py` - Help content updated
- `src/ui/profile_manager_tab.py` - Messages updated
- `README.md` - Documentation updated
- `FEATURES.md` - Documentation updated

## Previous Updates

### ✅ All UI/UX Issues Fixed

#### 1. Fan Curve Visualization
- ✅ Horizontal line showing current fan speed percentage
- ✅ Glowing dot at intersection point with curve
- ✅ Curve profile name displayed in labels (e.g., "Fan Curve Visualization - Balanced")
- ✅ Curves now reload from persistent storage after clicking Apply
- ✅ Default Balanced curve loads if no curve is configured

#### 2. Fan Gauges (Dashboard)
- ✅ Applied game-style dark theme with neon accents
- ✅ GPU fan gauge now updates correctly with RPM values
- ✅ Both CPU and GPU fan gauges show correct profile names
- ✅ Visually striking styling matching the rest of the application

#### 3. Metric Cards
- ✅ Units now displayed inline with values (e.g., "12.8 Mbps" instead of separate lines)
- ✅ Removed horizontal bar unit labels that wasted space
- ✅ Cleaner, more compact display

#### 4. 60-Second Averaging System
- ✅ Network Sent, Recv, and Total show 60-second averages
- ✅ GPU Usage shows 60-second averages
- ✅ FPS shows 60-second averages
- ✅ Configurable via preferences dialog (0-300 seconds)
- ✅ Default: 60 seconds
- ✅ History tracking implemented for all averaged metrics

#### 5. Preferences Dialog
- ✅ Added averaging window configuration control
- ✅ Spinbox for setting averaging window (0-300 seconds)
- ✅ Clear description of what averaging affects
- ✅ Show/Hide meters toggle (existing feature)
- ✅ All settings persisted automatically to preferences.json

#### 6. UI/UX Improvements
- ✅ Test Fans screen fixed - readable and properly styled
- ✅ Removed redundant Help tab from main window
- ✅ Removed header bar whitespace at top of window
- ✅ Game-style theme applied consistently throughout

### Technical Improvements

#### Code Quality
- ✅ Consistent error handling
- ✅ Proper fallbacks for missing data
- ✅ Clean code structure
- ✅ All syntax checks passing

#### Preferences System
- ✅ PreferencesManager enhanced with averaging_window_seconds preference
- ✅ Default value: 60 seconds
- ✅ Stored in ~/.config/asus-control/preferences.json

#### System Monitor
- ✅ Added history tracking for network metrics
- ✅ Added history tracking for GPU utilization
- ✅ Added history tracking for FPS
- ✅ Implemented get_average_over_seconds() method
- ✅ Efficient deque-based history storage

### Files Modified

- `src/ui/responsive_dashboard.py` - Added averaging controls, metric card improvements
- `src/ui/fan_status_tab.py` - Fixed curve loading, added profile name to labels
- `src/ui/fan_speed_gauge.py` - Applied game-style theme
- `src/ui/animated_widgets.py` - Inline units in metric cards
- `src/ui/test_fans_tab.py` - Fixed styling issues
- `src/ui/main_window.py` - Removed redundant Help tab
- `src/monitoring/system_monitor.py` - Added averaging history tracking
- `src/utils/preferences_manager.py` - Added averaging_window_seconds preference

### Commits

Latest commits in this session:
- `1a377c0` - Add averaging window configuration to preferences dialog
- `cd89f31` - Fix all remaining UI issues
- `f59106d` - Fix multiple UI issues
- And more...

### Status

✅ **All features complete and production-ready**
✅ **All changes committed and pushed to GitHub**
✅ **Working tree clean**
✅ **Ready for use**

## Installation

Run the installer:
```bash
./install.sh
```

Or launch directly:
```bash
python3 run.py
```

## Preferences

Access preferences via:
- Dashboard → Preferences button (⚙ icon)

Configure:
- Averaging window (0-300 seconds, default: 60)
- Show/Hide individual meters

Settings are saved automatically to:
`~/.config/asus-control/preferences.json`

