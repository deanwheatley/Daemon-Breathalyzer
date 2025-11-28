# Test Suite

Comprehensive test suite for the Daemon Breathalyzer application.

## Running Tests

### Run All Tests

```bash
cd ~/projects/daemon-breathalyzer
source venv/bin/activate
pytest
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # On macOS
xdg-open htmlcov/index.html  # On Linux
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# UI tests (require Qt)
pytest -m ui

# Skip slow tests
pytest -m "not slow"
```

### Run Specific Test Files

```bash
# Test system monitoring
pytest tests/test_system_monitor.py

# Test dependency checker
pytest tests/test_dependency_checker.py

# Test asusctl interface
pytest tests/test_asusctl_interface.py
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Detailed Output

```bash
pytest -vv -s
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_system_monitor.py   # System monitoring tests
├── test_log_monitor.py      # Log monitoring tests
├── test_log_viewer_tab.py   # Log viewer UI tests
├── test_dependency_checker.py  # Dependency checker tests
├── test_system_check.py     # System check utility tests
├── test_asusctl_interface.py  # asusctl interface tests
├── test_profile_manager.py  # Profile manager tests
└── test_ui_widgets.py       # UI widget tests
```

## Test Coverage

The test suite covers:

- ✅ System monitoring functionality
- ✅ Log monitoring with journalctl integration
- ✅ Log viewer UI components
- ✅ Log filtering and error tracking
- ✅ Dependency checking and installation
- ✅ System configuration checks
- ✅ asusctl interface (with mocks)
- ✅ Profile management (save/load/export/import)
- ✅ Fan curve data models and validation
- ✅ UI widgets (basic functionality)

## Writing New Tests

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Example Test

```python
import pytest
from src.module import ClassName

class TestClassName:
    def test_feature(self):
        obj = ClassName()
        result = obj.method()
        assert result == expected_value
```

### Using Fixtures

```python
def test_with_fixture(tmp_path):
    # tmp_path is a temporary directory fixture
    file_path = tmp_path / "test.txt"
    file_path.write_text("test")
```

### Mocking External Dependencies

```python
from unittest.mock import patch

@patch('subprocess.run')
def test_with_mock(mock_run):
    mock_run.return_value = Mock(returncode=0)
    # Test code here
```

## Continuous Integration

Tests are designed to run in CI environments:

- No external hardware required (mocked)
- No GUI required for most tests (mocked Qt)
- Fast execution
- Deterministic results

## Known Limitations

- UI tests require Qt and may be slower
- Some tests require mocking external commands
- Hardware-specific features are mocked


