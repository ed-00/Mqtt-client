"""
pytest configuration and shared fixtures for the test suite.

Author: 
    - Abed Hameed (ed-00)
Date: 
    - 2025-06-30
"""

import os
import asyncio
import logging
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from Listener.event_listener import (
    EventListenerConfig,
    EventListener,
    JobInfo,
    JobStatus,
)
from Listener.safe_config_parser import SafeConfigParser


@pytest.fixture
def sample_config():
    """Provide a sample EventListenerConfig for testing."""
    return EventListenerConfig(
        host="test.mqtt.broker",
        port=1883,
        client_id="test-client",
        username="test_user",
        password="test_pass",
        topic="test/topic",
        keep_alive=30,
        default_qos=1,
        max_jobs_in_memory=1000,
        job_cleanup_interval=3600,
    )


@pytest.fixture
def mock_mqtt_client():
    """Provide a mocked MQTT client."""
    mock_client = AsyncMock()
    mock_client.connect = AsyncMock()
    mock_client.subscribe = AsyncMock()
    mock_client.deliver_message = AsyncMock()
    mock_client.publish = AsyncMock()
    mock_client.disconnect = AsyncMock()
    return mock_client


@pytest.fixture
def event_listener(config, mqtt_client_mock):
    """Provide an EventListener instance with mocked MQTT client."""
    listener = EventListener(config)
    listener.client = mqtt_client_mock
    return listener


@pytest.fixture
def safe_config_parser():
    """Provide a SafeConfigParser instance."""
    logger = logging.getLogger("test")
    return SafeConfigParser(logger)


@pytest.fixture
def sample_toml_config():
    """Provide sample TOML configuration data."""
    return {
        "connection": {
            "host": "mqtt.example.com",
            "port": 1883,
            "username": "user",
            "password": "pass",
        },
        "topics": {"main": "sensors/data", "error": "sensors/error"},
        "settings": {"keep_alive": 60, "qos": 1},
    }


@pytest.fixture
def temp_toml_file():
    """Create a temporary TOML file for testing."""
    toml_content = """[connection]
host = "mqtt.example.com"
port = 1883
username = "user"
password = "pass"

[topics]
main = "sensors/data"
error = "sensors/error"

[settings]
keep_alive = 60
qos = 1
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        temp_path = f.name

    yield Path(temp_path)

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def invalid_toml_file():
    """Create a temporary file with invalid TOML content."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write("invalid = toml content [\n")  # Invalid TOML syntax
        temp_path = f.name

    yield Path(temp_path)

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def sample_job_info():
    """Provide sample JobInfo for testing."""
    return JobInfo(
        job_id="test-job-123",
        status=JobStatus.PENDING,
        started_at=datetime.now(),
        input_data={"key": "value"},
    )


@pytest.fixture
def event_loop():
    """Provide event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration for each test."""
    yield
    # Clear any handlers that tests might have added
    for logger_name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.setLevel(logging.WARNING)
