"""
Unit tests for the EventListener module.
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock

from Listener.event_listener import (
    EventListener,
    EventListenerConfig,
    JobStatus,
    JobInfo,
    ReturnType,
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
class TestJobInfo:
    """Test JobInfo dataclass."""

    def test_job_info_creation(self):
        """Test JobInfo creation with required fields."""
        start_time = datetime.now()
        job_info = JobInfo(
            job_id="test-job-123",
            status=JobStatus.PENDING,
            started_at=start_time
        )
        
        assert job_info.job_id == "test-job-123"
        assert job_info.status == JobStatus.PENDING
        assert job_info.started_at == start_time
        assert job_info.completed_at is None
        assert job_info.input_data is None
        assert job_info.result is None
        assert job_info.error is None

    def test_job_info_with_all_fields(self):
        """Test JobInfo creation with all fields."""
        start_time = datetime.now()
        complete_time = datetime.now()
        input_data = {"test": "data"}
        result = {"output": "success"}
        
        job_info = JobInfo(
            job_id="complete-job",
            status=JobStatus.COMPLETED,
            started_at=start_time,
            completed_at=complete_time,
            input_data=input_data,
            result=result,
            error=None
        )
        
        assert job_info.job_id == "complete-job"
        assert job_info.status == JobStatus.COMPLETED
        assert job_info.completed_at == complete_time
        assert job_info.input_data == input_data
        assert job_info.result == result


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
        assert config.allow_job_id_generation is False
        assert config.duplicate_action == "skip"

    def test_config_custom_values(self):
        """Test configuration with custom values."""
        config = EventListenerConfig(
            host="custom.mqtt.broker",
            port=8883,
            client_id="custom-client",
            topic="custom/topic",
            max_jobs_in_memory=1000,
            allow_job_id_generation=True,
            duplicate_action="reprocess"
        )
        
        assert config.host == "custom.mqtt.broker"
        assert config.port == 8883
        assert config.client_id == "custom-client"
        assert config.topic == "custom/topic"
        assert config.max_jobs_in_memory == 1000
        assert config.allow_job_id_generation is True
        assert config.duplicate_action == "reprocess"


@pytest.mark.unit
class TestReturnType:
    """Test ReturnType dataclass."""

    def test_return_type_creation(self):
        """Test ReturnType creation with all fields."""
        timestamp = datetime.now()
        return_data = ReturnType(
            data={"result": "success"},
            topic="test/results",
            qos=1,
            retain=False,
            message_id=123,
            timestamp=timestamp,
            job_id="test-job"
        )
        
        assert return_data.data == {"result": "success"}
        assert return_data.topic == "test/results"
        assert return_data.qos == 1
        assert return_data.retain is False
        assert return_data.message_id == 123
        assert return_data.timestamp == timestamp
        assert return_data.job_id == "test-job"


@pytest.mark.unit
class TestEventListenerInit:
    """Test EventListener initialization."""

    def test_init_with_config(self, sample_config):
        """Test initialization with configuration."""
        listener = EventListener(sample_config)

        assert listener.config == sample_config
        assert listener.jobs == {}
        assert listener.is_running is False
        assert listener.client is not None
        assert listener.logger is not None

    def test_init_with_custom_config_parser(self, sample_config):
        """Test initialization with custom config parser."""
        mock_parser = Mock()
        listener = EventListener(sample_config, config_parser=mock_parser)
        
        assert listener.config_parser == mock_parser


@pytest.mark.unit
@pytest.mark.asyncio
class TestEventListenerJobManagement:
    """Test EventListener job management functionality."""

    async def test_extract_job_id_found(self, sample_config):
        """Test extracting job ID when present in data."""
        listener = EventListener(sample_config)
        
        toml_data = {"job_id": "test-123", "action": "test"}
        job_id = listener.extract_job_id(toml_data)
        
        assert job_id == "test-123"

    async def test_extract_job_id_not_found(self, sample_config):
        """Test extracting job ID when not present in data."""
        listener = EventListener(sample_config)
        
        toml_data = {"action": "test", "data": "value"}
        job_id = listener.extract_job_id(toml_data)
        
        assert job_id is None

    async def test_generate_job_id_allowed(self, sample_config):
        """Test job ID generation when allowed."""
        config = EventListenerConfig(
            host=sample_config.host,
            port=sample_config.port,
            client_id=sample_config.client_id,
            allow_job_id_generation=True
        )
        listener = EventListener(config)
        
        job_id = listener.generate_job_id()
        
        assert job_id is not None
        assert len(job_id) > 0
        assert isinstance(job_id, str)

    async def test_generate_job_id_disabled(self, sample_config):
        """Test job ID generation when disabled."""
        config = EventListenerConfig(
            host=sample_config.host,
            port=sample_config.port,
            client_id=sample_config.client_id,
            allow_job_id_generation=False
        )
        listener = EventListener(config)
        
        job_id = listener.generate_job_id()
        
        assert job_id is None

    async def test_create_job_success(self, sample_config):
        """Test successful job creation."""
        listener = EventListener(sample_config)
        
        job_id = "test-job"
        input_data = {"test": "data"}
        
        success = await listener._create_job(job_id, input_data)
        
        assert success is True
        assert await listener.job_exists(job_id)
        
        job_info = await listener.get_job_status(job_id)
        assert job_info is not None
        assert job_info.job_id == job_id
        assert job_info.status == JobStatus.PENDING
        assert job_info.input_data == input_data

    async def test_create_job_duplicate(self, sample_config):
        """Test creating duplicate job."""
        listener = EventListener(sample_config)
        
        job_id = "duplicate-job"
        input_data = {"test": "data"}
        
        # Create first job
        success1 = await listener._create_job(job_id, input_data)
        assert success1 is True
        
        # Try to create duplicate
        success2 = await listener._create_job(job_id, input_data)
        assert success2 is False

    async def test_update_job_status(self, sample_config):
        """Test updating job status."""
        listener = EventListener(sample_config)
        
        job_id = "status-test"
        await listener._create_job(job_id, {})
        
        # Update to running
        await listener._update_job_status(job_id, JobStatus.RUNNING)
        
        job_info = await listener.get_job_status(job_id)
        assert job_info is not None
        assert job_info.status == JobStatus.RUNNING
        
        # Update to completed with result
        result_data = {"output": "success"}
        await listener._update_job_status(job_id, JobStatus.COMPLETED, result=result_data)
        
        job_info = await listener.get_job_status(job_id)
        assert job_info is not None
        assert job_info.status == JobStatus.COMPLETED
        assert job_info.result == result_data
        assert job_info.completed_at is not None

    async def test_job_status_queries(self, sample_config):
        """Test various job status query methods."""
        listener = EventListener(sample_config)
        
        # Create jobs with different statuses
        await listener._create_job("pending", {})
        await listener._create_job("running", {})
        await listener._create_job("completed", {})
        await listener._create_job("failed", {})
        
        await listener._update_job_status("running", JobStatus.RUNNING)
        await listener._update_job_status("completed", JobStatus.COMPLETED)
        await listener._update_job_status("failed", JobStatus.FAILED, error="test error")
        
        # Test query methods
        assert await listener.is_job_running("running") is True
        assert await listener.is_job_running("completed") is False
        
        assert await listener.is_job_completed("completed") is True
        assert await listener.is_job_completed("failed") is True
        assert await listener.is_job_completed("running") is False
        
        # Test getting jobs by status
        running_jobs = await listener.get_running_jobs()
        assert len(running_jobs) == 1
        assert "running" in running_jobs
        
        completed_jobs = await listener.get_completed_jobs()
        assert len(completed_jobs) == 1
        assert "completed" in completed_jobs

    async def test_job_cleanup(self, sample_config):
        """Test job cleanup functionality."""
        config = EventListenerConfig(
            host=sample_config.host,
            port=sample_config.port,
            client_id=sample_config.client_id,
            max_jobs_in_memory=2
        )
        listener = EventListener(config)
        
        # Create multiple completed jobs
        for i in range(5):
            job_id = f"cleanup-job-{i}"
            await listener._create_job(job_id, {})
            await listener._update_job_status(job_id, JobStatus.COMPLETED)
        
        # Trigger cleanup
        await listener.cleanup_old_jobs()
        
        # Should not exceed max jobs limit
        all_jobs = await listener.get_all_jobs()
        assert len(all_jobs) <= config.max_jobs_in_memory


@pytest.mark.unit
class TestEventListenerUtilities:
    """Test EventListener utility methods."""

    def test_stop_method(self, sample_config):
        """Test stopping the event listener."""
        listener = EventListener(sample_config)
        
        assert listener.is_running is False
        
        # Set running to True to test stop
        listener.is_running = True
        listener.stop()
        
        assert listener.is_running is False
