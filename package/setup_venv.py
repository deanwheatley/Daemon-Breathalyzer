#!/usr/bin/env python3
"""
Virtual Environment Setup Helper

Automatically creates and sets up the virtual environment.
"""

import sys
import subprocess
import os
from pathlib import Path

from src.utils.system_check import (
    find_python_executable,
    check_python_version,
    check_venv_module,
    check_virtual_environment
)


def create_venv(project_root: Path) -> bool:
    """Create virtual environment."""
    venv_path = project_root / 'venv'
    
    if venv_path.exists():
        print(f"⚠️  Virtual environment already exists at {venv_path}")
        response = input("Remove and recreate? (y/N): ").strip().lower()
        if response == 'y':
            import shutil
            shutil.rmtree(venv_path)
        else:
            print("Keeping existing virtual environment.")
            return True
    
    python_exe = find_python_executable()
    if not python_exe:
        print("❌ Error: Could not find Python executable.")
        print("   Please install Python 3.8+ and try again.")
        return False
    
    print(f"📦 Creating virtual environment using {python_exe}...")
    
    try:
        subprocess.run(
            [python_exe, '-m', 'venv', str(venv_path)],
            check=True,
            timeout=60
        )
        print(f"✅ Virtual environment created at {venv_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating virtual environment: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    """Main setup function."""
    project_root = Path(__file__).parent
    
    print("🔍 Checking system configuration...")
    print()
    
    # Check Python version
    ok, error = check_python_version()
    if not ok:
        print(f"❌ {error}")
        sys.exit(1)
    
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} found")
    
    # Check venv module
    ok, error = check_venv_module()
    if not ok:
        print()
        print(f"❌ {error}")
        print()
        print("After installing, run this script again.")
        sys.exit(1)
    
    print("✅ venv module available")
    print()
    
    # Check if venv already exists
    in_venv, venv_error, venv_path = check_virtual_environment()
    if in_venv:
        print("✅ Already in a virtual environment!")
        print("   You can run the application directly.")
        return
    
    # Create venv
    if create_venv(project_root):
        print()
        print("✅ Setup complete!")
        print()
        print("Next steps:")
        print(f"  1. Activate the virtual environment:")
        print(f"     source {project_root}/venv/bin/activate")
        print()
        print(f"  2. Run the application:")
        print(f"     python run.py")
        print()
        print("   Or install dependencies first:")
        print(f"     pip install -r requirements.txt")
        print(f"     python run.py")
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()


