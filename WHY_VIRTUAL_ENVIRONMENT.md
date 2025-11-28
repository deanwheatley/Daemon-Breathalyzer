# Why Do We Use a Virtual Environment?

## Short Answer

**You don't need to create it manually!** The `install.sh` script creates it automatically. You only need to run:
```bash
./install.sh
```

The virtual environment is created automatically behind the scenes.

## Why Virtual Environments?

### 1. **Modern Linux Distributions Require It (PEP 668)**

Many Linux distributions (including newer versions of Ubuntu, Debian, and Linux Mint) mark system Python as **"externally managed"**. This means:
- You **cannot** install packages directly to system Python
- Trying to `pip install` without a venv will fail with an error
- This protects your system from breaking system packages

**Error you'd get without venv:**
```
error: externally-managed-environment
× This environment is externally managed
```

### 2. **Prevents Breaking Your System**

Installing packages directly to system Python can:
- Break system tools that depend on specific package versions
- Create conflicts between different applications
- Make it hard to uninstall or update packages

### 3. **Clean Application Installation**

With a virtual environment:
- All app dependencies are isolated in one folder (`venv/`)
- Easy to uninstall: just delete the `venv/` folder
- No conflicts with other Python applications
- Can have different versions for different projects

## But... Do You Need to Think About It?

**No!** The installer handles everything:

```bash
./install.sh
```

This automatically:
1. ✅ Creates the virtual environment
2. ✅ Installs all dependencies
3. ✅ Creates a launcher script that activates venv automatically
4. ✅ Adds the app to your menu

**When you launch the app** (from the menu or `./daemon-breathalyzer-launcher.sh`):
- The venv is activated automatically
- You don't need to think about it
- It just works!

## Alternative: System-Wide Installation (Not Recommended)

You *could* install packages system-wide, but:
- ❌ Requires `sudo` for every install
- ❌ Can break system packages
- ❌ Won't work on modern Linux (PEP 668)
- ❌ Harder to uninstall
- ❌ Conflicts with other apps

## The Bottom Line

**Virtual environments are:**
- ✅ Required by modern Linux distributions
- ✅ Automatically handled by the installer
- ✅ Transparent when using the launcher
- ✅ Best practice for Python applications

**You only interact with venv if:**
- You're developing/debugging
- You want to manually install packages
- You want to run from terminal (then you activate venv first)

**For normal users:** Just run `./install.sh` and forget about it! 🎉


