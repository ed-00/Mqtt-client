# MQTT Event Listener

[![Tests](https://img.shields.io/github/actions/workflow/status/ed-00/Mqtt-client/test.yml?branch=main&label=tests&logo=github)](https://github.com/ed-00/Mqtt-client/actions)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)](./htmlcov/index.html)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](https://github.com/ed-00/Mqtt-client/releases/tag/v1.0.0)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](./LICENSE)
[![Code Quality](https://img.shields.io/badge/code%20quality-A-brightgreen.svg)](./scripts/build_package.sh)
[![Security](https://img.shields.io/badge/security-scanned-brightgreen.svg)](./Makefile)
[![Internal Use](https://img.shields.io/badge/distribution-internal-orange.svg)](./INTERNAL_DISTRIBUTION.md)

A Python library for MQTT event listening with comprehensive job tracking, configuration parsing, and error handling capabilities.

## Features

- **Asynchronous MQTT client** with job tracking capabilities
- **TOML message processing** with automatic parsing and validation
- **Job management system** with status tracking and duplicate detection
- **Configurable error handling** and logging
- **Safe configuration parsing** with validation
- **Comprehensive testing** with unit and integration tests

## Testing & Quality Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Test Coverage** | 85% | ✅ Good |
| **Unit Tests** | 45+ tests | ✅ Comprehensive |
| **Integration Tests** | 12+ tests | ✅ Complete |
| **Code Quality** | Grade A | ✅ Excellent |
| **Security Scan** | No issues | ✅ Secure |
| **Documentation** | 100% | ✅ Complete |
| **Type Hints** | Full coverage | ✅ Type safe |

### Test Categories
- 🧪 **Unit Tests**: Core functionality, configuration parsing, job management
- 🔗 **Integration Tests**: End-to-end workflows, MQTT client integration  
- 🚀 **Performance Tests**: Memory usage, async operations
- 🔒 **Security Tests**: Input validation, dependency scanning
- 📚 **Documentation Tests**: Code examples, API documentation

Run tests locally:
```bash
# Quick test run
make test

# Full test suite with coverage
make coverage

# Security and quality checks  
make lint && make security
```

## Installation

### From Git Repository

```bash
# Install directly from git (latest version)
pip install git+https://github.com/ed-00/Mqtt-client.git

# Install a specific branch or tag
pip install git+https://github.com/ed-00/Mqtt-client.git@main
pip install git+https://github.com/ed-00/Mqtt-client.git@v1.0.3
```

### From Local Clone

```bash
# Clone and install
git clone https://github.com/ed-00/Mqtt-client.git
cd Mqtt-client
pip install .

# Or install in editable mode for development
pip install -e .
```

### Development Installation

```bash
# For development with all testing tools
git clone https://github.com/ed-00/Mqtt-client.git
cd Mqtt-client
pip install -e .[dev]
```

### Internal Distribution

For distributing within your organization, you can:

1. **Share the wheel file directly:**
   ```bash
   # Build the package
   python -m build
   
   # Share the .whl file from dist/ directory
   pip install mqtt_event_listener-1.0.2-py3-none-any.whl
   ```

2. **Set up an internal package index** or use your organization's private repository

3. **Install directly from your internal git server:**
   ```bash
   pip install git+https://www.github.com/mqtt-client.git
   ```

## Quick Start

### Basic Usage

```python
import asyncio
from Listener import EventListener, EventListenerConfig

# Create configuration
config = EventListenerConfig(
    host="localhost",
    port=1883,
    username="your_username",
    password="your_password",
    topic="your/topic",
    client_id="my-listener"
)

# Initialize listener
listener = EventListener(config)

# Define your message processing function
def process_message(data, job_id):
    """Process incoming TOML messages"""
    print(f"Processing job {job_id}: {data}")
    
    # Your processing logic here
    # The result should be a dictionary that will be serialized to TOML
    result = {"status": "processed", "job_id": job_id}
    
    # Return results to be published back
    return ReturnType(
        data=result,
        topic="results/topic",
        qos=0,
        retain=False,
        message_id=1,
        timestamp=datetime.now(),
        job_id=job_id
    )

# Run the listener
async def main():
    await listener.run(process_message)

if __name__ == "__main__":
    asyncio.run(main())
```

### Advanced Configuration

```python
from Listener import EventListenerConfig, SafeConfigParser

# Advanced configuration with SSL and custom settings
config = EventListenerConfig(
    host="mqtt.example.com",
    port=8883,
    username="user",
    password="pass",
    topic="events/+",  # Wildcard topic
    client_id="advanced-listener",
    
    # SSL/TLS settings
    cafile="/path/to/ca.crt",
    
    # Job tracking settings
    max_jobs_in_memory=10000,
    job_cleanup_interval=3600,  # 1 hour
    allow_job_id_generation=True,
    duplicate_action="reprocess",
    
    # MQTT client settings
    keep_alive=60,
    auto_reconnect=True,
    reconnect_retries=5,
    cleansession=False,
    
    # Custom topics for different message types
    error_topic="errors",
    log_topic="logs", 
    results_topic="results"
)

# Use custom config parser
config_parser = SafeConfigParser()
listener = EventListener(config, config_parser)
```

## Configuration

The `EventListenerConfig` class provides comprehensive configuration options:

### Connection Settings
- `host`: MQTT broker hostname
- `port`: MQTT broker port
- `username`, `password`: Authentication credentials
- `client_id`: Unique client identifier

### Topic Settings  
- `topic`: Primary subscription topic
- `error_topic`: Topic for error messages
- `log_topic`: Topic for log messages
- `results_topic`: Topic for result publishing

### Job Tracking
- `max_jobs_in_memory`: Maximum jobs to keep in memory
- `job_cleanup_interval`: Cleanup interval for completed jobs
- `allow_job_id_generation`: Auto-generate job IDs if missing
- `duplicate_action`: How to handle duplicate jobs ("skip", "reprocess", "error")

### SSL/TLS Support
- `cafile`: Path to CA certificate file
- `capath`: Path to CA certificate directory  
- `cadata`: CA certificate data

## Job Management

The library provides comprehensive job tracking:

```python
# Get job status
job_info = await listener.get_job_status("job_123")
print(f"Job status: {job_info.status}")

# Check if job is running
is_running = await listener.is_job_running("job_123")

# Get all jobs by status
running_jobs = await listener.get_running_jobs()
completed_jobs = await listener.get_completed_jobs()
duplicate_jobs = await listener.get_duplicate_jobs()

# Cleanup old completed jobs
await listener.cleanup_old_jobs()
```

## Message Format

The library expects TOML-formatted messages:

```toml
job_id = "unique-job-123"
task_type = "data_processing"
priority = "high"

[data]
input_file = "/path/to/input.csv"
output_file = "/path/to/output.json"
parameters = { timeout = 300, retries = 3 }
```

## Error Handling

The library includes robust error handling:

- **Configuration validation** with detailed error messages
- **MQTT connection error handling** with automatic reconnection
- **Job processing errors** with error tracking and reporting
- **TOML parsing errors** with safe fallback handling

## Testing

Our comprehensive test suite ensures reliability and maintainability:

```bash
# Run all tests with coverage report
make test

# Run only unit tests (fast)
make test-unit  

# Run integration tests
make test-integration

# Generate detailed coverage report
make coverage

# Code quality and security checks
make lint
make security

# Quick development check
make quick
```

### Coverage Reports
- **Line Coverage**: 85% (target: 80%+)
- **Branch Coverage**: 82% 
- **Function Coverage**: 95%

View detailed coverage: `open htmlcov/index.html`

### Test Performance
- **Unit Tests**: ~2 seconds
- **Integration Tests**: ~8 seconds  
- **Full Suite**: ~12 seconds

## API Reference

### Main Classes

- **`EventListener`**: Main MQTT event listener with job tracking
- **`EventListenerConfig`**: Configuration dataclass for all settings
- **`SafeConfigParser`**: Safe TOML configuration parser
- **`JobInfo`**: Job information and status tracking
- **`ReturnType`**: Return type for processed messages

### Enums

- **`JobStatus`**: Job execution status (PENDING, RUNNING, COMPLETED, FAILED, DUPLICATE)

## Contributing

For internal development within the organization:

1. Clone the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and test thoroughly
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request for review

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Author

**Abed Hameed** (@ed-00)

## Version History

### Version 1.0.2
- Updated to use TOML for all published messages.
- Updated versioning and release process.

### Version 1.0.0
- Initial internal release
- MQTT event listening with job tracking
- TOML message processing
- Comprehensive configuration system
- Error handling and logging
- Test suite with coverage reporting

## Internal Release Management

To create a new version for internal distribution:

1. Update the version in `pyproject.toml` and `Listener/__init__.py`
2. Update this README with release notes
3. Commit and tag the release:
   ```bash
   git tag v1.0.3
   git push origin v1.0.3
   ```
4. Build the package using the provided script:
   ```bash
   ./scripts/build_package.sh
   ```
   Or manually:
   ```bash
   python -m build
   ```
5. Distribute the wheel file from `dist/` directory or instruct users to install from the git tag 