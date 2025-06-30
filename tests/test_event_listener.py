"""
Unit tests for the EventListener module.
"""
import pytest

from Listener.event_listener import (
    EventListener,
    EventListenerConfig,
    JobStatus,
)


@pytest.mark.unit
class TestJobStatus:
    """Test JobStatus enumeration."""

    def test_job_status_values(self):
        """Test that JobStatus contains expected values."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.DUPLICATE.value == "duplicate"


@pytest.mark.unit
class TestEventListenerConfig:
    """Test EventListenerConfig dataclass."""

    def test_config_defaults(self):
        """Test that config has reasonable defaults."""
        config = EventListenerConfig()

        assert config.host == "localhost"
        assert config.port == 1883
        assert config.client_id == "event-listener"
        assert config.username == "test"
        assert config.password == "test"
        assert config.topic == "test"
        assert config.keep_alive == 10
        assert config.default_qos == 0
        assert config.max_jobs_in_memory == 5000


@pytest.mark.unit
class TestEventListenerInit:
    """Test EventListener initialization."""

    def test_init_with_config(self, sample_config):
        """Test initialization with configuration."""
        listener = EventListener(sample_config)

        assert listener.config == sample_config
        assert listener.jobs == {}
        assert listener.is_running is False
