.PHONY: help install test test-unit test-integration test-all lint security quick clean coverage

# Default target
help:
	@echo "MQTT Client Testing Commands"
	@echo "============================"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test          Run all tests (alias for test-all)"
	@echo "  make test-unit     Run unit tests only"
	@echo "  make test-integration  Run integration tests only"
	@echo "  make test-all      Run all tests with coverage"
	@echo "  make quick         Run unit tests + linting (fast check)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          Run code linting (flake8)"
	@echo "  make security      Run security checks (bandit, safety)"
	@echo "  make coverage      Generate HTML coverage report"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         Clean up generated files"

install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt

test: test-all

test-unit:
	@echo "🧪 Running unit tests..."
	python scripts/run_tests.py unit

test-integration:
	@echo "🔗 Running integration tests..."
	python scripts/run_tests.py integration

test-all:
	@echo "🚀 Running all tests..."
	python scripts/run_tests.py all

quick:
	@echo "⚡ Running quick check (unit tests + linting)..."
	python scripts/run_tests.py quick

lint:
	@echo "🔍 Running code linting..."
	python scripts/run_tests.py lint

security:
	@echo "🔒 Running security checks..."
	python scripts/run_tests.py security

coverage:
	@echo "📊 Generating coverage report..."
	pytest tests/ --cov=Listener --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/"

clean:
	@echo "🧹 Cleaning up..."
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf bandit-report.json
	rm -rf safety-report.json
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete 