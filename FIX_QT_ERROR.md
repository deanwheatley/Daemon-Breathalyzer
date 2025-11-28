# Fix Qt Platform Plugin Error

## Problem

When launching the app, you may see:
```
qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin.
qt.qpa.plugin: Could not load the Qt platform plugin "xcb"
```

## Solution

Install the missing XCB cursor library:

```bash
sudo apt install libxcb-cursor0
```

## Why This Happens

Qt6 (specifically from version 6.5.0) requires additional XCB libraries for proper cursor handling on Linux. These libraries are not always installed by default.

## After Installing

1. Restart the application
2. It should launch normally

## Check Log File

If the app still doesn't start, check the log file:
```bash
cat ~/.local/share/daemon-breathalyzer/launcher.log
```

This will show detailed error messages.

## Other Qt Dependencies

If you still have issues, you may also need:
```bash
sudo apt install libxcb-xinerama0 libxcb-xinput0
```

These are usually installed by default, but can help if Qt has plugin loading issues.


