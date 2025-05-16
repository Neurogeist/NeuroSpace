.PHONY: test test-watch test-coverage test-lint clean install install-dev

# Python environment
PYTHON := python
PYTEST := pytest
COVERAGE := coverage
PIP := pip

# Test directories
TEST_DIR := api/tests

# Installation commands
install:
	$(PIP) install -r requirements.txt

install-dev: install
	$(PIP) install -e .

# Test commands
test:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(PYTHON) -m $(PYTEST) $(TEST_DIR)

test-watch:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(PYTHON) -m $(PYTEST) $(TEST_DIR) -f

test-coverage:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(PYTHON) -m $(COVERAGE) run -m $(PYTEST) $(TEST_DIR)
	$(PYTHON) -m $(COVERAGE) report
	$(PYTHON) -m $(COVERAGE) html

test-lint:
	flake8 api/
	black --check api/
	mypy api/

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".coverage" -exec rm -r {} +
	find . -type d -name "htmlcov" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

# Help
help:
	@echo "Available commands:"
	@echo "  make install      - Install all dependencies"
	@echo "  make install-dev  - Install dependencies and package in dev mode"
	@echo "  make test         - Run all tests"
	@echo "  make test-watch   - Run tests in watch mode (re-runs on file changes)"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo "  make test-lint    - Run linting checks"
	@echo "  make clean        - Clean up cache files"
	@echo "  make help         - Show this help message" 