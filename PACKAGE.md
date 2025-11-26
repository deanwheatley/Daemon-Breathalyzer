# Distribution Package

This document explains how to create and maintain the distribution package for Daemon Breathalyzer.

## 📦 Package Overview

The `package/` folder contains everything a new user needs to install and run the application. This includes:

- ✅ All source code (`src/`)
- ✅ Installation scripts (`install.sh`, `setup_venv.py`)
- ✅ Launcher scripts (`asus-control-launcher.sh`)
- ✅ Desktop entry file (`asus-control.desktop`)
- ✅ Requirements file (`requirements.txt`)
- ✅ Icons (`img/`)
- ✅ Documentation (`README.md`)
- ✅ Driver installation helpers
- ✅ System error fixers

## 🔧 Building the Package

### Automatic (Recommended)

Use the Makefile:

```bash
make package
```

Or use the build script directly:

```bash
./build_package.sh
```

### Manual

The package is automatically built when you commit changes (via git pre-commit hook), or you can build it manually:

1. Run `./build_package.sh`
2. The package will be created in the `package/` directory

## 🔄 Keeping the Package Up to Date

### Option 1: Automatic Update (Recommended)

The package folder is automatically updated on every git commit via a pre-commit hook. This ensures the package always reflects the current code state.

### Option 2: Manual Update

Run this command whenever you make changes:

```bash
make update-package
```

Or:

```bash
./build_package.sh
```

## 📋 Package Contents

After building, the `package/` folder contains:

```
package/
├── src/                          # Source code
├── img/                          # Icons and images
├── install.sh                    # Main installer
├── asus-control-launcher.sh      # Launcher script
├── asus-control.desktop          # Desktop entry
├── requirements.txt              # Python dependencies
├── README.md                     # Full documentation
├── PACKAGE_README.md            # Package-specific README
├── INSTALL.txt                  # Quick install instructions
├── check_and_install_drivers.py # Driver installer
├── fix_system_log_errors.sh     # System error fixer
├── setup_venv.py                # Virtual environment setup
├── run.py                       # Application launcher
└── VERSION                      # Package version
```

## 📦 Creating Distribution Archives

To create a distributable archive:

```bash
cd package
tar -czf ../daemon-breathalyzer-$(date +%Y%m%d).tar.gz .
```

Or use the Makefile:

```bash
make package
cd package
tar -czf ../daemon-breathalyzer-$(date +%Y%m%d).tar.gz .
```

## 🚀 Distribution Workflow

1. **During Development:**
   - The package is automatically updated on commit
   - Or run `make update-package` manually after changes

2. **Before Distribution:**
   - Run `make package` to ensure package is up-to-date
   - Test the package by extracting it and running `./install.sh`
   - Create a tarball for distribution

3. **Sending to Users:**
   - Send the entire `package/` folder, or
   - Send a `.tar.gz` archive created from the package folder
   - Users extract and run `./install.sh`

## ⚙️ Makefile Targets

- `make package` - Build/update the distribution package
- `make update-package` - Update package folder (same as package)
- `make clean` - Clean the package folder and build artifacts

## 🔍 Package Size

The package is designed to be lightweight:
- **Typical size:** ~700KB
- **Files:** ~35 files
- **No virtual environment:** Users create their own during installation
- **No compiled files:** Only source code

## 📝 Versioning

The package includes a `VERSION` file with the build date (YYYYMMDD format). This helps track when the package was created.

## 🆘 Troubleshooting

**Package not updating automatically?**
- Check that `.git/hooks/pre-commit` exists and is executable
- Run `make package` manually

**Package too large?**
- The package excludes:
  - Virtual environments
  - Test files
  - Build artifacts
  - Cache files (`__pycache__`, `.pytest_cache`, etc.)

**Need to exclude files from package?**
- Edit `build_package.sh` to modify what gets copied

## 📚 Related Files

- `build_package.sh` - Package builder script
- `Makefile` - Make targets for package management
- `.git/hooks/pre-commit` - Auto-update hook
- `package/PACKAGE_README.md` - Instructions for package recipients

