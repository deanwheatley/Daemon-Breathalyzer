#!/usr/bin/env python3
"""
Daemon Breathalyzer - Main Entry Point

PyQt6-based GUI application for ASUS fan control with system monitoring and log analysis.
"""

import sys
import os
from pathlib import Path

# Check system configuration first (before importing PyQt6)
try:
    from src.utils.system_check import run_system_checks, check_venv_module
    
    # Run system checks
    checks_ok, system_error = run_system_checks()
    if not checks_ok:
        print("❌ System Configuration Error", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(system_error, file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print()
        
        # Check if venv module issue
        venv_ok, venv_error = check_venv_module()
        if not venv_ok:
            print("💡 Quick Fix:", file=sys.stderr)
            print("  Run: python3 setup_venv.py", file=sys.stderr)
            print("  This will help you set up the virtual environment.", file=sys.stderr)
        
        sys.exit(1)
except Exception as e:
    # If system checks fail, continue anyway (they're helpful but not critical)
    print(f"⚠️  Warning: Could not run system checks: {e}", file=sys.stderr)

# Now we can import PyQt6
try:
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtCore import Qt
except ImportError:
    print("❌ PyQt6 is not installed.", file=sys.stderr)
    print("   Please install it with: pip install PyQt6", file=sys.stderr)
    print("   Or run the setup helper: python3 setup_venv.py", file=sys.stderr)
    sys.exit(1)

from src.utils.dependency_checker import DependencyChecker
from src.ui.dependency_dialog import DependencyDialog
from src.ui.main_window import MainWindow


def check_dependencies_before_startup():
    """Check dependencies and show dialog if needed."""
    # First, check if PyQt6 is available (needed for the dialog itself)
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        from PyQt6.QtCore import Qt
        pyqt6_available = True
    except ImportError:
        pyqt6_available = False
        print("PyQt6 is not installed. Please install it first:")
        print("  pip install PyQt6")
        return False
    
    checker = DependencyChecker()
    results = checker.check_all()
    
    if not results['required_installed']:
        # Create minimal app for dialog
        app = QApplication(sys.argv)
        app.setApplicationName("ASUS Fan Control")
        app.setOrganizationName("ASUS Control")
        # High DPI scaling is enabled by default in PyQt6
    # AA_EnableHighDpiScaling was removed in PyQt6
        
        dialog = DependencyDialog()
        dialog.exec()
        
        # Re-check after dialog closes
        results = checker.check_all()
        
        if not results['required_installed']:
            QMessageBox.critical(
                None,
                "Missing Dependencies",
                "Required dependencies are still missing. Please install them before continuing.\n\n"
                "You can check dependencies again from the Help menu after installing."
            )
            # Allow user to continue anyway (maybe some optional deps missing)
            # Or exit - let's allow continuing but warn
            response = QMessageBox.question(
                None,
                "Continue Anyway?",
                "Some required dependencies are missing. The application may not work correctly.\n\n"
                "Do you want to continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if response == QMessageBox.StandardButton.No:
                return False
        
        app.quit()
    
    return True


def main():
    """Main entry point for the application."""
    # Check dependencies first (before creating full app)
    if not check_dependencies_before_startup():
        sys.exit(1)
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Daemon Breathalyzer")
    app.setOrganizationName("Daemon Breathalyzer")
    
    # Enable high DPI scaling
    # High DPI scaling is enabled by default in PyQt6
    # AA_EnableHighDpiScaling was removed in PyQt6
    
    # Apply modern, minimalist styling
    app.setStyleSheet("""
        QMainWindow {
            background-color: #fafafa;
        }
        QTabWidget::pane {
            border: none;
            background: white;
        }
        QTabBar::tab {
            background: #f5f5f5;
            color: #666;
            padding: 12px 24px;
            margin-right: 2px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }
        QTabBar::tab:selected {
            background: white;
            color: #2196F3;
            font-weight: bold;
        }
        QTabBar::tab:hover {
            background: #eeeeee;
        }
        QStatusBar {
            background-color: #f5f5f5;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }
    """)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

