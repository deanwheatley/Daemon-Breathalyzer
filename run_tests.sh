#!/bin/bash
# Test runner script for Daemon Breathalyzer

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Daemon Breathalyzer - Test Suite"
echo "=========================================="
echo ""

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ] && [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if pytest is installed
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "⚠️  pytest not found. Installing test dependencies..."
    pip install -q pytest pytest-cov pytest-mock pytest-qt pytest-timeout
    echo ""
fi

echo "Running test suite..."
echo ""

# Run tests with coverage
pytest tests/ \
    -v \
    --tb=short \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-report=xml \
    -p no:warnings \
    "$@"

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
    echo ""
    echo "Coverage report generated in: htmlcov/index.html"
else
    echo "❌ Some tests failed (exit code: $EXIT_CODE)"
fi

exit $EXIT_CODE


