# Makefile for Daemon Breathalyzer
#
# Usage:
#   make package        - Build distribution package
#   make bin-package    - Build install package in bin/ folder
#   make clean          - Clean build artifacts
#   make install        - Install the application
#   make test           - Run tests
#   make update-package - Update package folder (keeps it in sync)

.PHONY: package bin-package clean install test update-package help

# Default target
help:
	@echo "Daemon Breathalyzer - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make package        - Build distribution package in package/ folder"
	@echo "  make bin-package    - Build install package in bin/ folder (compressed archive)"
	@echo "  make update-package - Update package folder (sync with current code)"
	@echo "  make clean          - Clean build artifacts and package folder"
	@echo "  make install        - Run installation script"
	@echo "  make test           - Run test suite"
	@echo "  make help           - Show this help message"
	@echo ""

# Build distribution package
package:
	@echo "Building distribution package..."
	@./build_package.sh

# Build install package in bin/ folder
bin-package: package
	@echo "Building install package in bin/ folder..."
	@./build_bin_package.sh

# Update package folder - keeps package/ in sync with current code
# This is the rule that should be run whenever the app changes
update-package: package
	@echo "✅ Package folder updated!"
	@echo "💡 Run 'make update-package' whenever you make changes to the app"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf package/*
	@rm -rf bin/*
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo "✅ Clean complete!"

# Install application
install:
	@echo "Running installation..."
	@./install.sh

# Run tests
test:
	@echo "Running tests..."
	@if [ -f "venv/bin/pytest" ]; then \
		./venv/bin/pytest; \
	else \
		echo "⚠️  Virtual environment not found. Run ./install.sh first"; \
	fi

