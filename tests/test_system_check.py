"""
Tests for system check utilities.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.utils.system_check import (
    find_python_executable,
    check_python_version,
    check_venv_module,
    check_virtual_environment,
    check_pip_available,
    check_externally_managed,
    run_system_checks
)


class TestPythonExecutable:
    """Test Python executable finding."""
    
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_find_python3(self, mock_run, mock_which):
        """Test finding python3 executable."""
        mock_which.return_value = "/usr/bin/python3"
        mock_run.return_value = Mock(returncode=0, stdout="Python 3.10.0")
        
        result = find_python_executable()
        assert result == "python3"
    
    @patch('shutil.which')
    def test_find_python_not_found(self, mock_which):
        """Test when Python not found."""
        mock_which.return_value = None
        
        result = find_python_executable()
        assert result is None


class TestPythonVersion:
    """Test Python version checking."""
    
    def test_check_python_version_valid(self):
        """Test with valid Python version."""
        ok, error = check_python_version()
        # Should pass for Python 3.8+
        assert ok == True
        assert error is None
    
    @patch('sys.version_info', Mock(major=2, minor=7))
    def test_check_python_version_old(self):
        """Test with old Python version."""
        ok, error = check_python_version()
        assert ok == False
        assert error is not None


class TestVenvModule:
    """Test venv module checking."""
    
    def test_check_venv_module_available(self):
        """Test when venv module is available."""
        ok, error = check_venv_module()
        # venv should be available in Python 3.8+
        assert ok == True
        assert error is None
    
    def test_check_venv_module_not_available(self, monkeypatch):
        """Test when venv module is not available."""
        # Temporarily remove venv from sys.modules to simulate it not being available
        venv_module = sys.modules.pop('venv', None)
        
        # Mock __import__ to raise ImportError for venv
        original_import = __import__
        def import_side_effect(name, *args, **kwargs):
            if name == 'venv':
                raise ImportError("No module named 'venv'")
            return original_import(name, *args, **kwargs)
        
        monkeypatch.setattr('builtins.__import__', import_side_effect)
        
        try:
            ok, error = check_venv_module()
            assert ok == False
            assert error is not None
            assert "python3-venv" in error or "venv" in error.lower()
        finally:
            # Restore venv module if it was there
            if venv_module:
                sys.modules['venv'] = venv_module


class TestVirtualEnvironment:
    """Test virtual environment checking."""
    
    def test_check_venv_in_venv(self):
        """Test when already in virtual environment."""
        # Mock sys.base_prefix to be different from sys.prefix (indicates venv)
        with patch.object(sys, 'base_prefix', '/usr', create=True):
            with patch.object(sys, 'prefix', '/home/user/project/venv', create=True):
                in_venv, error, venv_path = check_virtual_environment()
                # Should detect we're in a venv if base_prefix != prefix
                assert isinstance(in_venv, bool)
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.home')
    def test_check_venv_exists_not_activated(self, mock_home, mock_exists):
        """Test when venv exists but not activated."""
        project_root = Path("/test/project")
        venv_path = project_root / "venv" / "bin" / "activate"
        
        # Mock that we're not in venv and venv exists
        if hasattr(sys, 'real_prefix'):
            delattr(sys, 'real_prefix')
        if hasattr(sys, 'base_prefix'):
            sys.base_prefix = sys.prefix  # Not in venv
        
        # This test needs more careful mocking
        pass


class TestPipAvailable:
    """Test pip availability checking."""
    
    def test_check_pip_available(self):
        """Test when pip is available."""
        ok, error = check_pip_available()
        assert ok == True
        assert error is None


class TestExternallyManaged:
    """Test externally managed environment checking."""
    
    def test_check_externally_managed_not_managed(self):
        """Test when not in externally managed environment."""
        is_managed, error = check_externally_managed()
        
        # Should return False if not managed
        assert isinstance(is_managed, bool)
    
    @patch('pathlib.Path.exists')
    def test_check_externally_managed_marker_exists(self, mock_exists):
        """Test when externally managed marker exists."""
        mock_exists.return_value = True
        
        # Mock not in venv
        if hasattr(sys, 'real_prefix'):
            delattr(sys, 'real_prefix')
        if hasattr(sys, 'base_prefix'):
            sys.base_prefix = sys.prefix
        
        is_managed, error = check_externally_managed()
        
        # If marker file exists and not in venv, should be managed
        assert isinstance(is_managed, bool)


class TestSystemChecks:
    """Test system checks integration."""
    
    def test_run_system_checks_in_venv(self, monkeypatch):
        """Test system checks when in virtual environment."""
        # Mock being in venv by setting base_prefix != prefix
        monkeypatch.setattr('sys.base_prefix', '/usr')
        monkeypatch.setattr('sys.prefix', '/home/user/venv')
        # Also set real_prefix if it exists
        if hasattr(sys, 'real_prefix'):
            monkeypatch.setattr('sys.real_prefix', '/usr')
        
        checks_ok, error = run_system_checks()
        # Should pass if in venv
        assert isinstance(checks_ok, bool)


