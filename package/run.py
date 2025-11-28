#!/usr/bin/env python3
"""
Launch script for Daemon Breathalyzer

This script ensures the project root is in the Python path
so imports work correctly regardless of where it's run from.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Check if we're in a virtual environment
venv_path = project_root / 'venv'
in_venv = (
    hasattr(sys, 'real_prefix') or 
    (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
)

# If not in venv and venv exists, provide helpful message
if not in_venv and venv_path.exists():
    activate_script = venv_path / 'bin' / 'activate'
    if activate_script.exists():
        print("⚠️  Warning: Virtual environment exists but is not activated.")
        print()
        print("Please activate it first:")
        print(f"  source {venv_path}/bin/activate")
        print()
        print("Or run the setup helper:")
        print(f"  python3 setup_venv.py")
        print()
        sys.exit(1)

# Run system checks and import main
try:
    from src.main import main
except ImportError as e:
    if 'venv' in str(e).lower() or 'EXTERNALLY-MANAGED' in str(e):
        print("❌ Error: Python environment is externally managed.")
        print()
        print("You need to use a virtual environment. Options:")
        print()
        print("1. Run the setup helper:")
        print(f"   python3 setup_venv.py")
        print()
        print("2. Or create manually:")
        print(f"   python3 -m venv {venv_path}")
        print(f"   source {venv_path}/bin/activate")
        print(f"   python run.py")
        print()
        sys.exit(1)
    else:
        raise

if __name__ == '__main__':
    main()

