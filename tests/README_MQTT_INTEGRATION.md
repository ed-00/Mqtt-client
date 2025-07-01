# MQTT Integration Testing

This document describes the MQTT integration testing setup for the MQTT Event Listener project.

## Overview

The MQTT integration tests connect to a real Mosquitto MQTT broker running in Docker to validate:

- **Connection handling**: Basic connections, authentication, timeouts
- **Message publishing and subscribing**: Various QoS levels, retained messages
- **Content validation**: JSON, TOML, and binary message content
- **EventListener integration**: Real-world message processing workflows
- **Error handling**: Network issues, invalid data, edge cases

## Architecture

```
┌─────────────────────┐    ┌──────────────────────┐
│   Test Container    │    │  Mosquitto Broker    │
│  (mqtt-client-dev)  │────│   (mosquitto)        │
│                     │    │                      │
│ - Python Tests      │    │ - Port 1883 (MQTT)   │
│ - EventListener     │    │ - Port 9001 (WS)     │
│ - Test Scripts      │    │ - Auth: user/password │
└─────────────────────┘    └──────────────────────┘
          │                          │
          └──── Docker Network ──────┘
                mqtt-network
```

## Environment Setup

### Docker Compose Services

1. **mqtt-client-dev**: Development container with Python environment
2. **mosquitto**: Eclipse Mosquitto MQTT broker

Both services run on the same Docker network (`mqtt-network`) for seamless communication.

### Environment Variables

The following environment variables are configured:

```bash
# MQTT Connection
MQTT_HOST=mosquitto                 # Broker hostname
MQTT_PORT=1883                     # MQTT port
MQTT_BROKER_PORT=1883              # Broker port
MQTT_BROKER_PORT_WEB=9001          # WebSocket port

# Authentication
MQTT_USERNAME=user                 # MQTT username
MQTT_PASSWORD=password             # MQTT password

# Listener Configuration
MQTT_LISTENER_PORT=1883            # Listener port
MQTT_LISTENER_IP=0.0.0.0          # Listener IP
MQTT_LISTENER_INTERFACE=           # Network interface
MQTT_LOG_DESTINATION=stdout        # Log destination
```

## Quick Start

### 1. Start the Environment

```bash
# Setup and start all services
./scripts/setup_dev_env.sh setup

# Or manually with Docker Compose
docker-compose up -d
```

### 2. Run MQTT Integration Tests

```bash
# Run all MQTT integration tests
./scripts/run_mqtt_tests.sh mqtt

# Run specific test categories
./scripts/run_mqtt_tests.sh unit         # Unit tests only
./scripts/run_mqtt_tests.sh integration  # Integration tests (no MQTT)
./scripts/run_mqtt_tests.sh all          # All tests

# Run just the MQTT test file
pytest tests/test_mqtt_integration.py -v
```

### 3. Monitor Services

```bash
# Check service status
./scripts/setup_dev_env.sh status

# View logs
docker-compose logs -f

# Enter development container
docker-compose exec mqtt-client-dev bash
```

## Test Categories

### Connection Tests (`TestMqttConnection`)

- **Basic Connection**: Connect/disconnect to broker
- **Authentication**: Connect with username/password
- **Timeout Handling**: Connection timeout scenarios

### Messaging Tests (`TestMqttMessaging`)

- **QoS Levels**: Test QoS 0, 1, and 2 message delivery
- **Retained Messages**: Publish and receive retained messages
- **JSON Content**: Validate JSON message serialization
- **Multiple Subscribers**: Test fan-out messaging

### EventListener Integration (`TestEventListenerMqttIntegration`)

- **Connection Testing**: EventListener MQTT connectivity
- **Message Processing**: End-to-end TOML message processing
- **Job Tracking**: Validate job creation and status tracking

### Error Handling (`TestMqttErrorHandling`)

- **Invalid Topics**: Handle malformed topic names
- **Large Messages**: Test message size limits
- **Connection Recovery**: Test reconnection scenarios

## Test Markers

Use pytest markers to run specific test types:

```bash
# Run only MQTT integration tests
pytest -m mqtt_integration

# Skip MQTT integration tests
pytest -m "not mqtt_integration"

# Run unit tests only
pytest -m "unit and not mqtt_integration"

# Run all integration tests including MQTT
pytest -m integration
```

## Development Workflow

### 1. Development Container

The development container includes:
- Python 3 with all dependencies
- MQTT client libraries (amqtt)
- Testing frameworks (pytest, pytest-asyncio)
- Development tools (black, pylint, mypy)

### 2. Hot Reloading

Code changes are automatically reflected in the container via volume mounts:

```yaml
volumes:
  - .:/app                    # Source code
  - /app/.pytest_cache        # Exclude cache
  - /app/__pycache__          # Exclude bytecode
```

### 3. Network Communication

Both containers communicate over the `mqtt-network` Docker network:
- Tests connect to `mosquitto:1883`
- No port mapping required for internal communication
- Ports 1883 and 9001 are exposed to host for external access

## Configuration Files

### Docker Compose (`docker-compose.yml`)

Defines the multi-service environment with proper networking and environment variables.

### Mosquitto Config (`mosquitto/config/mosquitto.conf`)

Configures the MQTT broker with:
- Anonymous access enabled (for development)
- Logging to both file and stdout
- WebSocket support on port 9001
- Persistence enabled

### DevContainer (`.devcontainer/devcontainer.json`)

VS Code DevContainer configuration for seamless development experience.

## Troubleshooting

### Services Not Starting

```bash
# Check Docker status
docker info

# Check service logs
docker-compose logs mosquitto
docker-compose logs mqtt-client-dev

# Restart services
./scripts/setup_dev_env.sh restart
```

### Connection Issues

```bash
# Test MQTT connection manually
docker-compose exec mosquitto mosquitto_pub -h localhost -p 1883 -t "test" -m "hello"

# Check network connectivity
docker-compose exec mqtt-client-dev ping mosquitto

# Verify ports are open
docker-compose exec mqtt-client-dev telnet mosquitto 1883
```

### Test Failures

```bash
# Run tests with verbose output
pytest tests/test_mqtt_integration.py -v -s

# Run specific test
pytest tests/test_mqtt_integration.py::TestMqttConnection::test_basic_connection -v

# Debug with pdb
pytest tests/test_mqtt_integration.py --pdb
```

### Container Issues

```bash
# Rebuild containers
docker-compose down
docker-compose up -d --build

# Clean slate
./scripts/setup_dev_env.sh clean
./scripts/setup_dev_env.sh setup
```

## Performance Considerations

### Test Execution Time

MQTT integration tests are slower than unit tests due to:
- Network communication overhead
- Docker container startup time
- MQTT connection establishment
- Message delivery confirmation

Typical execution times:
- Unit tests: ~5-15 seconds
- Integration tests: ~30-60 seconds
- MQTT integration tests: ~60-120 seconds

### Resource Usage

The test environment requires:
- **Memory**: ~256MB for Mosquitto + 512MB for Python container
- **CPU**: Minimal during testing, brief spikes during startup
- **Network**: Docker bridge network with port forwarding
- **Storage**: ~100MB for container images + logs

## Security Notes

### Development Only

The current configuration is designed for development and testing:

⚠️ **WARNING**: Do not use in production without security hardening!

- Anonymous MQTT access is enabled
- No TLS/SSL encryption
- Default credentials (user/password)
- All ports exposed to host

### Production Hardening

For production deployment:

1. **Enable TLS/SSL**:
   ```
   listener 8883
   cafile /mosquitto/config/ca.crt
   certfile /mosquitto/config/server.crt
   keyfile /mosquitto/config/server.key
   ```

2. **Disable Anonymous Access**:
   ```
   allow_anonymous false
   password_file /mosquitto/config/password_file
   ```

3. **Configure ACLs**:
   ```
   acl_file /mosquitto/config/acl_file
   ```

4. **Use Strong Credentials**:
   - Generate strong passwords
   - Use client certificates
   - Implement proper user management

## Contributing

When adding new MQTT integration tests:

1. **Use the `@pytest.mark.mqtt_integration` marker**
2. **Include proper cleanup in `finally` blocks**
3. **Test both success and failure scenarios**
4. **Use appropriate timeouts for async operations**
5. **Document any special setup requirements**

Example test structure:

```python
@pytest.mark.mqtt_integration
@pytest.mark.asyncio
async def test_my_feature(mqtt_host, mqtt_port):
    """Test description."""
    client = mqtt.MQTTClient(client_id="test-my-feature")
    
    try:
        await client.connect(f"mqtt://{mqtt_host}:{mqtt_port}")
        # Test implementation
        assert expected_result
    finally:
        await client.disconnect()
``` 