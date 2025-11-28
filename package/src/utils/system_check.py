#!/usr/bin/env python3
"""
System Check Utilities

Checks system configuration and provides helpful error messages.
"""

import sys
import subprocess
import shutil
from pathlib import Path
from typing import Tuple, Optional


def find_python_executable() -> Optional[str]:
    """Find the best Python executable to use."""
    # Try python3 first (most common on Linux)
    if shutil.which('python3'):
        try:
            result = subprocess.run(
                ['python3', '--version'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return 'python3'
        except Exception:
            pass
    
    # Fallback to python
    if shutil.which('python'):
        try:
            result = subprocess.run(
                ['python', '--version'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return 'python'
        except Exception:
            pass
    
    return None


def check_python_version() -> Tuple[bool, Optional[str]]:
    """
    Check if Python version is adequate.
    
    Returns:
        Tuple of (is_ok: bool, error_message: str)
    """
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        return False, f"Python 3.8+ is required, but found Python {version.major}.{version.minor}"
    
    return True, None


def check_venv_module() -> Tuple[bool, Optional[str]]:
    """
    Check if venv module is available.
    
    Returns:
        Tuple of (is_available: bool, error_message: str)
    """
    try:
        import venv
        return True, None
    except ImportError:
        # Try to determine the system
        try:
            with open('/etc/os-release', 'r') as f:
                os_release = f.read()
                
            if 'Ubuntu' in os_release or 'Debian' in os_release:
                python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
                return False, (
                    f"The python3-venv package is not installed.\n\n"
                    f"On Debian/Ubuntu systems, install it with:\n"
                    f"  sudo apt install python{python_version}-venv\n\n"
                    f"Then recreate the virtual environment."
                )
            else:
                return False, (
                    "The venv module is not available.\n\n"
                    "Please install the Python venv package for your distribution."
                )
        except Exception:
            return False, "The venv module is not available. Please install it for your distribution."


def check_virtual_environment() -> Tuple[bool, Optional[str], Optional[Path]]:
    """
    Check if we're in a virtual environment or if one exists.
    
    Returns:
        Tuple of (is_in_venv: bool, error_message: str, venv_path: Path)
    """
    # Check if we're already in a venv
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return True, None, None
    
    # Check if venv exists in project
    project_root = Path(__file__).parent.parent.parent
    venv_path = project_root / 'venv'
    
    if venv_path.exists() and (venv_path / 'bin' / 'activate').exists():
        return False, (
            "Virtual environment exists but is not activated.\n\n"
            f"Please activate it with:\n"
            f"  source {venv_path}/bin/activate\n\n"
            f"Then run the application again."
        ), venv_path
    
    # No venv found
    return False, (
        "No virtual environment found.\n\n"
        "Please create one with:\n"
        f"  python3 -m venv {project_root}/venv\n"
        f"  source {project_root}/venv/bin/activate\n\n"
        "Or let the setup script create it for you."
    ), None


def check_pip_available() -> Tuple[bool, Optional[str]]:
    """Check if pip is available."""
    try:
        import pip
        return True, None
    except ImportError:
        return False, (
            "pip is not available.\n\n"
            "Please install pip for your Python installation."
        )


def check_externally_managed() -> Tuple[bool, Optional[str]]:
    """
    Check if we're in an externally managed Python environment.
    
    Returns:
        Tuple of (is_managed: bool, error_message: str)
    """
    # Check if we're in a venv (if so, not externally managed)
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return False, None
    
    # Check for PEP 668 marker
    marker_files = [
        Path('/usr/lib/python3/dist-packages/EXTERNALLY-MANAGED'),
        Path(f'/usr/lib/python{sys.version_info.major}.{sys.version_info.minor}/EXTERNALLY-MANAGED'),
    ]
    
    for marker in marker_files:
        if marker.exists():
            return True, (
                "Python environment is externally managed (PEP 668).\n\n"
                "You must use a virtual environment to install packages.\n\n"
                "The application will help you set one up, or create it manually:\n"
                f"  python3 -m venv venv\n"
                f"  source venv/bin/activate\n\n"
                "Then run the application again."
            )
    
    return False, None


def run_system_checks() -> Tuple[bool, Optional[str]]:
    """
    Run all system checks and return overall status.
    
    Returns:
        Tuple of (all_checks_passed: bool, error_message: str)
    """
    # Check Python version
    ok, error = check_python_version()
    if not ok:
        return False, error
    
    # Check if we're in venv (if yes, we're good)
    in_venv, venv_error, venv_path = check_virtual_environment()
    if in_venv:
        return True, None
    
    # Not in venv - check if externally managed
    is_managed, managed_error = check_externally_managed()
    if is_managed:
        return False, managed_error
    
    # Check venv module availability
    venv_ok, venv_error = check_venv_module()
    if not venv_ok:
        return False, venv_error
    
    # Check pip
    pip_ok, pip_error = check_pip_available()
    if not pip_ok:
        return False, pip_error
    
    # If we got here and not in venv, suggest creating one
    return False, venv_error


if __name__ == '__main__':
    # Test the checks
    ok, error = run_system_checks()
    if ok:
        print("✅ All system checks passed!")
    else:
        print("❌ System check failed:")
        print(error)


