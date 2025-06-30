# Testing Guide

This directory contains comprehensive tests for the MQTT Client project. The testing infrastructure includes unit tests, integration tests, code quality checks, and security analysis.

## 📁 Test Structure

```
tests/
├── __init__.py                 # Package initialization
├── conftest.py                 # Pytest configuration and shared fixtures
├── test_safe_config_parser.py  # Unit tests for configuration parser
├── test_event_listener.py      # Unit tests for event listener
├── test_integration.py         # Integration tests
└── README.md                   # This file
```

## 🚀 Quick Start

### Install Dependencies

```bash
# Install all dependencies including testing tools
make install
# or
pip install -r requirements.txt
```

### Run Tests

```bash
# Run all tests (recommended)
make test

# Run only unit tests (fast)
make test-unit

# Run integration tests
make test-integration

# Quick check (unit tests + linting)
make quick
```

## 🧪 Test Categories

### Unit Tests (`@pytest.mark.unit`)

Unit tests focus on individual components in isolation:

- **SafeConfigParser**: TOML parsing, validation, error handling
- **EventListener**: Job management, MQTT integration, async operations
- **Configuration classes**: Data structure validation

```bash
# Run unit tests with coverage
pytest tests/ -m unit --cov=Listener
```

### Integration Tests (`@pytest.mark.integration`)

Integration tests verify component interactions:

- Real file operations
- Configuration workflows
- MQTT client integration (mocked)
- End-to-end job processing

```bash
# Run integration tests
pytest tests/ -m integration
```

### Slow Tests (`@pytest.mark.slow`)

Tests that take longer to run:

- File I/O operations
- Complex workflows
- Memory management tests

```bash
# Exclude slow tests for faster development
pytest tests/ -m "not slow"
```

## 🔧 Test Configuration

### pytest.ini

The project uses pytest with the following configuration:

- **Coverage**: Minimum 80% coverage required
- **Async support**: Automatic async test detection
- **Markers**: Unit, integration, and slow test categories
- **Reporting**: Terminal, HTML, and XML coverage reports

### Fixtures

Shared test fixtures are defined in `conftest.py`:

- `sample_config`: Default EventListener configuration
- `mock_mqtt_client`: Mocked MQTT client for testing
- `event_listener`: EventListener instance with mocked dependencies
- `safe_config_parser`: SafeConfigParser instance
- `temp_toml_file`: Temporary TOML file for testing

## 🛠️ Testing Tools

### Code Quality

```bash
# Run linting
make lint
flake8 Listener/ tests/ --max-line-length=127
```

### Security Analysis

```bash
# Run security checks
make security
bandit -r Listener/          # Security analysis
safety check                 # Dependency vulnerability check
```

### Coverage Analysis

```bash
# Generate coverage report
make coverage
# View HTML report
open htmlcov/index.html
```

## 📊 Running Specific Tests

### By Module

```bash
# Test specific module
pytest tests/test_safe_config_parser.py
pytest tests/test_event_listener.py
```

### By Test Class

```bash
# Test specific class
pytest tests/test_safe_config_parser.py::TestSafeConfigParser
pytest tests/test_event_listener.py::TestJobManagement
```

### By Test Method

```bash
# Test specific method
pytest tests/test_safe_config_parser.py::TestSafeConfigParser::test_parse_config_from_dict
```

### By Marker

```bash
# Run tests by category
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m "unit and not slow"  # Fast unit tests only
```

## 🔍 Test Development Guidelines

### Writing Unit Tests

1. **Isolation**: Mock external dependencies
2. **Coverage**: Test both success and failure paths
3. **Clarity**: Use descriptive test names and docstrings
4. **Fixtures**: Use shared fixtures for common setup

```python
@pytest.mark.unit
class TestMyFeature:
    def test_feature_success_case(self, fixture_name):
        """Test the success path of my feature."""
        # Arrange
        input_data = {"key": "value"}
        
        # Act
        result = my_function(input_data)
        
        # Assert
        assert result == expected_result
```

### Writing Integration Tests

1. **Real scenarios**: Test actual usage patterns
2. **Mocking**: Mock only external services (MQTT brokers)
3. **Cleanup**: Ensure tests clean up resources
4. **Marking**: Use `@pytest.mark.integration`

### Writing Async Tests

```python
@pytest.mark.asyncio
async def test_async_function(event_listener):
    """Test async functionality."""
    result = await event_listener.async_method()
    assert result is not None
```

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running tests from the project root
2. **Async Test Failures**: Check that `pytest-asyncio` is installed
3. **Coverage Too Low**: Add tests for uncovered code paths
4. **Mock Issues**: Verify mock setup and assertions

### Debug Mode

```bash
# Run tests with verbose output and immediate failure
pytest tests/ -v -x --tb=short

# Run specific test with debugging
pytest tests/test_module.py::test_function -v -s
```

### Test Output

```bash
# Show print statements
pytest tests/ -s

# Show test duration
pytest tests/ --durations=10
```

## 📋 CI/CD Integration

Tests are automatically run on:

- **GitHub Actions**: On push/PR to main/develop branches
- **Multiple Python versions**: 3.9, 3.10, 3.11, 3.12
- **Security checks**: Bandit and Safety analysis
- **Coverage reporting**: Codecov integration

## 📈 Continuous Improvement

### Adding Tests

1. Add test files following the naming convention `test_*.py`
2. Use appropriate markers (`@pytest.mark.unit`, etc.)
3. Update coverage requirements if needed
4. Document any new testing patterns

### Updating Fixtures

1. Add new fixtures to `conftest.py`
2. Use appropriate scopes (`function`, `class`, `module`, `session`)
3. Document fixture purpose and usage

### Performance Testing

For future performance tests:

```bash
# Install pytest-benchmark
pip install pytest-benchmark

# Write benchmark tests
def test_performance(benchmark):
    result = benchmark(my_function, arg1, arg2)
    assert result == expected
```

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Safety Documentation](https://pyup.io/safety/) 