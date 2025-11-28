# Testing Guide

## Overview

The Daemon Breathalyzer application includes a comprehensive test suite that covers all major features and components.

## Quick Start

### Run All Tests

```bash
cd ~/projects/daemon-breathalyzer
source venv/bin/activate
./run_tests.sh
```

Or manually:

```bash
pytest tests/
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures and configuration
├── test_system_monitor.py         # System monitoring tests
├── test_dependency_checker.py     # Dependency checker tests
├── test_system_check.py           # System check utility tests
├── test_asusctl_interface.py      # asusctl interface tests
├── test_profile_manager.py        # Profile manager tests
├── test_ui_widgets.py             # UI widget tests
├── test_integration.py            # Integration tests
└── test_helpers.py                # Test helper utilities
```

## Test Coverage

### Unit Tests

- **System Monitoring** (`test_system_monitor.py`)
  - CPU metrics collection
  - Memory metrics collection
  - GPU metrics (mocked)
  - Temperature detection (multiple methods)
  - Fan speed detection
  - Historical data collection
  - Thread lifecycle

- **Dependency Checker** (`test_dependency_checker.py`)
  - Dependency status checking
  - Python package detection
  - System command detection
  - Installation instructions generation
  - Pip installation (mocked)

- **System Check** (`test_system_check.py`)
  - Python version checking
  - Venv module availability
  - Virtual environment detection
  - Externally managed environment detection
  - Pip availability

- **asusctl Interface** (`test_asusctl_interface.py`)
  - Fan curve point creation and validation
  - Fan curve creation and validation
  - Curve point manipulation (add/remove)
  - Curve serialization/deserialization
  - Preset curves
  - asusctl command execution (mocked)

- **Profile Manager** (`test_profile_manager.py`)
  - Profile creation and storage
  - Profile loading
  - Profile deletion
  - Profile export/import (JSON/YAML)
  - Profile list management

- **UI Widgets** (`test_ui_widgets.py`)
  - MetricCard widget
  - GraphWidget widget
  - Value updates
  - Widget creation

### Integration Tests

- **System Monitoring Integration** (`test_integration.py`)
  - Complete monitoring cycle
  - Multiple metric updates
  - History accumulation

- **Profile Workflow Integration** (`test_integration.py`)
  - Save/load cycle
  - Export/import cycle
  - Profile modification workflow

- **Fan Curve Workflow** (`test_integration.py`)
  - Preset to profile conversion
  - Curve modification and saving

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_system_monitor.py

# Run specific test
pytest tests/test_system_monitor.py::TestSystemMonitor::test_update_cpu_metrics

# Run with coverage
pytest --cov=src --cov-report=html

# View coverage report
# Open htmlcov/index.html
```

### Test Categories

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only UI tests
pytest -m ui

# Skip slow tests
pytest -m "not slow"

# Skip hardware-requiring tests
pytest -m "not requires_hardware"
```

### Test Output Options

```bash
# Short traceback
pytest --tb=short

# Long traceback (detailed)
pytest --tb=long

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Run last failed tests only
pytest --lf
```

## Test Configuration

Configuration is in `pytest.ini`:

- **Coverage**: Automatically generates HTML and XML reports
- **Markers**: Organize tests by category
- **Timeouts**: 30 second timeout per test
- **Output**: Verbose by default

## Mocking Strategy

### External Dependencies

All external dependencies are mocked to ensure tests run without:
- Actual hardware (GPU, sensors)
- System commands (asusctl, nvidia-smi)
- File system access (temporary directories used)
- Network access

### Mock Examples

**Subprocess calls:**
```python
@patch('subprocess.run')
def test_function(mock_run):
    mock_run.return_value = Mock(returncode=0, stdout="output")
```

**File system:**
```python
def test_with_files(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("content")
```

**Python imports:**
```python
@patch('psutil.cpu_percent')
def test_cpu(mock_cpu):
    mock_cpu.return_value = 50.0
```

## Writing New Tests

### Test Template

```python
import pytest
from unittest.mock import Mock, patch

from src.module import ClassName

class TestClassName:
    """Test ClassName."""
    
    def test_feature(self):
        """Test specific feature."""
        obj = ClassName()
        result = obj.method()
        assert result == expected_value
    
    @patch('external.dependency')
    def test_with_mock(self, mock_dep):
        """Test with mocked dependency."""
        mock_dep.return_value = Mock()
        # Test code
        assert True
```

### Best Practices

1. **Test one thing at a time**: Each test should verify one specific behavior
2. **Use descriptive names**: Test names should clearly describe what they test
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Mock external dependencies**: Don't rely on external systems
5. **Test edge cases**: Include boundary conditions and error cases
6. **Keep tests fast**: Avoid slow operations in unit tests

## Continuous Integration

Tests are designed for CI/CD:

- **No hardware required**: All hardware access is mocked
- **No GUI required**: UI tests use headless mode or mocks
- **Fast execution**: Most tests complete in milliseconds
- **Deterministic**: Tests produce consistent results
- **Isolated**: Tests don't depend on each other

## Coverage Goals

- **Unit Tests**: >80% coverage for core modules
- **Integration Tests**: Cover main workflows
- **Critical Paths**: 100% coverage for validation logic

## Troubleshooting Tests

### Common Issues

**Import errors:**
- Ensure you're in the virtual environment
- Run: `pip install -r requirements.txt`

**Test failures:**
- Run with `-vv` for detailed output
- Check that mocks are set up correctly
- Verify test data matches actual format

**Slow tests:**
- Use `-m "not slow"` to skip slow tests during development
- Profile tests with `pytest --durations=10`

**Coverage issues:**
- Check that source files are in `src/`
- Verify `pytest.ini` coverage settings

## Next Steps

- Add more edge case tests
- Increase integration test coverage
- Add performance benchmarks
- Add UI interaction tests (with pytest-qt)


