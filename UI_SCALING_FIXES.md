# UI Scaling and Fan Status Fixes

## Changes Made

### 1. Fan Status Tab - Removed Profile Label from Graph Title
- **Removed**: "Fan Curve Visualization - Performance" label
- **Replaced with**: Simple "Fan Curve Visualization" title
- The "Apply Curve" combo box in the header now serves as the primary control
- Combo box always reflects the currently active fan curve
- Fan curves are persistent across reboots and app restarts

### 2. Fan Curve Persistence
- Fan curves are saved to persistent storage when applied
- On app startup, persistent curves are automatically restored
- Curves persist even when the app is closed
- Works across system reboots

### 3. UI Scaling Improvements

#### Main Window
- **Minimum size**: 800x600 (ensures all UI components are visible)
- **Initial size**: 1200x800
- **Aspect ratio**: 3:2 (width:height) - optional enforcement available
- Responsive scaling based on window size

#### Scaling Algorithm
- **Changed**: Scale factor now uses minimum of width/height scaling (was average)
- **Reason**: Ensures content fits in the smaller dimension
- **Min scale**: 0.5 (was 0.6) - allows more aggressive scaling down
- **Max scale**: 2.0 (unchanged)

#### Fan Status Tab
- Added scroll area to prevent content overflow
- Graphs have minimum sizes (200px height, 300px width)
- All components scale proportionally with window size
- Reduced margins and spacing for better space utilization

#### Component Scaling
- Title fonts: Scale from base 20pt
- Value fonts: Scale from base 18pt
- Label fonts: Scale from base 10pt
- Margins: Scale from base 15px
- Spacing: Scale from base 10px
- Graph heights: Scale from base 300px (min 200px)

### 4. Responsive Behavior
- All tabs update scaling on window resize
- Scroll bars appear only when needed
- No horizontal scroll bars (content wraps/scales)
- Vertical scroll bars appear when content exceeds window height

## Testing Recommendations

1. **Test at different window sizes**:
   - Minimum: 800x600
   - Standard: 1200x800
   - Large: 1920x1080
   - Maximized on various screen resolutions

2. **Test Fan Status tab**:
   - Verify "Apply Curve" combo box shows current curve
   - Apply different curves and verify persistence
   - Close app and reopen - curves should be restored
   - Reboot system - curves should persist

3. **Test scaling**:
   - Resize window and verify all text remains readable
   - Verify graphs scale appropriately
   - Verify no content is cut off
   - Verify scroll bars appear when needed

4. **Test all tabs**:
   - Dashboard
   - Fan Curve Builder
   - System Logs
   - History
   - Fan Status
   - Test Fans
   - About

## Files Modified

1. `src/ui/fan_status_tab.py`
   - Removed profile name from graph title
   - Added scroll area
   - Improved scaling support
   - Added minimum sizes for graphs

2. `src/ui/main_window.py`
   - Added minimum window size (800x600)
   - Added aspect ratio tracking
   - Improved resize event handling

3. `src/ui/ui_scaling.py`
   - Changed scale calculation to use minimum dimension
   - Reduced minimum scale to 0.5
   - Improved scaling algorithm

## Known Limitations

1. **Aspect ratio enforcement**: Currently disabled to allow free resize
   - Can be enabled by uncommenting code in `main_window.py` resizeEvent
   
2. **Very small windows**: Below 800x600, some content may still be cramped
   - Minimum size enforcement prevents this

3. **Very large windows**: Above 2x base size, some elements may appear oversized
   - Max scale of 2.0 prevents excessive scaling

## Future Improvements

1. Add user preference for UI scale factor
2. Add option to lock aspect ratio
3. Add responsive column layout for metric cards
4. Add font size preferences
5. Add compact/normal/large UI modes
