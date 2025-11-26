# Installer Splash Screen

The installer can display a splash image while installation is in progress.

## Image Location

Place your installer splash image in one of these locations (checked in order):

1. `img/installer_splash.png` (recommended)
2. `img/splash.png`
3. `img/icon.png` (fallback)

The installer will automatically detect and display the image if available.

## Image Requirements

- **Format**: PNG (recommended) or JPG
- **Size**: 400x400 pixels or larger (will be displayed at 400x400)
- **Location**: Place in the `img/` folder

## How It Works

When the installer starts:
1. It checks for a splash image in the locations listed above
2. If found, it displays the image in a window using:
   - `feh` (if available) - lightweight image viewer
   - `eog` (Eye of GNOME) - if feh is not available
   - `zenity` - as a fallback option
3. The splash window stays visible during installation
4. It automatically closes when installation completes

## Adding Your Splash Image

1. Save your image as `installer_splash.png`
2. Place it in the `img/` folder
3. Run the installer - it will automatically display the image

## Testing

To test the splash screen:
```bash
./install.sh
```

The splash image will appear in a window and stay visible during the installation process.

## Package Distribution

When building the distribution package, any splash images in the `img/` folder will be automatically included in the package.

