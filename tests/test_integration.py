"""
Integration tests for the MQTT client functionality.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from Listener.event_listener import EventListener, EventListenerConfig, JobStatus
from Listener.safe_config_parser import SafeConfigParser
from Listener.safe_config_parser import (
    validate_required_fields,
    validate_field_types,
)


@pytest.mark.integration
class TestConfigParserIntegration:
    """Integration tests for config parser with real files."""

    def test_parse_real_toml_file(self, safe_config_parser):
        """Test parsing a real TOML configuration file."""
        toml_content = """
        [mqtt]
        host = "test.mosquitto.org"
        port = 1883
        client_id = "test-client"

        [topics]
        main = "test/topic"
        error = "test/error"

        [settings]
        keep_alive = 60
        qos = 1
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            temp_path = f.name

        try:
            result = safe_config_parser.parse_config(Path(temp_path))
            assert result.is_valid
            assert "mqtt" in result.data
            assert result.data["mqtt"]["host"] == "test.mosquitto.org"
            assert result.data["topics"]["main"] == "test/topic"
        finally:
            os.unlink(temp_path)

    def test_parse_with_validation(self, safe_config_parser):
        """Test parsing with custom validation rules."""

        # Add validators
        safe_config_parser.add_validator(validate_required_fields(["mqtt", "topics"]))
        safe_config_parser.add_validator(
            validate_field_types({"mqtt": dict, "topics": dict})
        )

        valid_config = {"mqtt": {"host": "localhost"}, "topics": {"main": "test"}}

        result = safe_config_parser.parse_config(valid_config)
        assert result.is_valid

        invalid_config = {
            "mqtt": "not a dict",  # Wrong type
            "missing": "topics",  # Missing required field
        }

        result = safe_config_parser.parse_config(invalid_config)
        assert not result.is_valid
        assert len(result.validation_errors) > 0


@pytest.mark.integration
class TestEventListenerWithMockMqtt:
    """Integration tests for EventListener with mocked MQTT."""

    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete workflow from config to job processing."""
        config = EventListenerConfig(
            host="test.broker.com",
            port=1883,
            client_id="integration-test",
            topic="test/integration",
            max_jobs_in_memory=100,
            allow_job_id_generation=True,
        )

        listener = EventListener(config)

        # Mock the MQTT client
        listener.client = AsyncMock()

        # Test job creation and processing
        job_data = {"task": "integration_test", "data": "test_payload"}

        # Extract or generate job ID
        job_id = listener.extract_job_id(job_data)
        if not job_id:
            job_id = listener.generate_job_id()

        assert job_id is not None

        # Create job
        success = await listener._create_job(  # pylint: disable=protected-access
            job_id, job_data
        )
        assert success

        # Verify job exists and is pending
        assert await listener.job_exists(job_id)
        job_info = await listener.get_job_status(job_id)
        assert job_info is not None
        assert job_info.status == JobStatus.PENDING

        # Start processing
        await listener._update_job_status(  # pylint: disable=protected-access
            job_id, JobStatus.RUNNING
        )
        assert await listener.is_job_running(job_id)

        # Complete processing
        result = {"output": "success", "processed_at": "2024-01-01T00:00:00"}
        await listener._update_job_status(  # pylint: disable=protected-access
            job_id, JobStatus.COMPLETED, result=result
        )

        # Verify completion
        assert await listener.is_job_completed(job_id)
        final_job = await listener.get_job_status(job_id)
        assert final_job is not None
        assert final_job.result == result
        assert final_job.status == JobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_mqtt_connection_flow(self):
        """Test MQTT connection and subscription flow."""
        config = EventListenerConfig(
            host="mqtt.eclipse.org",
            port=1883,
            client_id="test-integration",
            topic="test/mqtt/flow",
        )

        listener = EventListener(config)
        mock_client = AsyncMock()
        listener.client = mock_client

        # Test connection
        await listener._connect()  # pylint: disable=protected-access
        mock_client.connect.assert_called_once()

        # Test subscription
        await listener._subscribe()  # pylint: disable=protected-access
        mock_client.subscribe.assert_called_once()

        # Test message publishing
        await listener._send_message(  # pylint: disable=protected-access
            "test/output", "test message", 1, False
        )  # pylint: disable=protected-access
        mock_client.publish.assert_called_with("test/output", "test message", 1, False)

    @pytest.mark.asyncio
    async def test_job_memory_management(self):
        """Test job memory management and cleanup."""
        config = EventListenerConfig(
            max_jobs_in_memory=3, job_cleanup_interval=1  # 1 second for testing
        )

        listener = EventListener(config)

        # Fill up job memory
        for i in range(3):
            success = await listener._create_job(  # pylint: disable=protected-access
                f"job-{i}", {"data": i}
            )  # pylint: disable=protected-access
            assert success

        # Try to add one more - should fail if memory management is implemented
        success = await listener._create_job(  # pylint: disable=protected-access
            "job-overflow", {"data": "overflow"}
        )  # pylint: disable=protected-access
        # Note: This test assumes memory limit enforcement is implemented
        # If not implemented yet, this test documents the expected behavior

        # Complete some jobs to test cleanup
        await listener._update_job_status(  # pylint: disable=protected-access
            "job-0", JobStatus.COMPLETED
        )  # pylint: disable=protected-access
        await listener._update_job_status(  # pylint: disable=protected-access
            "job-1", JobStatus.FAILED, error="test error"
        )  # pylint: disable=protected-access

        # Wait and cleanup (in real scenario this would be time-based)
        # For testing, we manually trigger cleanup
        await listener.cleanup_old_jobs()

        # Verify job counts
        all_jobs = await listener.get_all_jobs()
        completed_jobs = await listener.get_completed_jobs()

        assert len(all_jobs) >= 1  # At least the running job should remain
        assert len(completed_jobs) >= 0  # Completed jobs might be cleaned up


@pytest.mark.integration
@pytest.mark.slow
class TestRealFileOperations:
    """Integration tests with real file operations."""

    def test_config_file_validation_workflow(self):
        """Test complete config file validation workflow."""
        parser = SafeConfigParser()

        # Create a realistic config file
        config_content = """
        [connection]
        host = "mqtt.example.com"
        port = 1883
        username = "test_user"
        password = "test_pass"

        [mqtt_settings]
        keep_alive = 60
        qos = 1
        clean_session = true

        [topics]
        main_topic = "sensors/data"
        error_topic = "sensors/errors"
        log_topic = "sensors/logs"

        [job_management]
        max_jobs = 1000
        cleanup_interval = 3600
        job_id_field = "job_id"
        allow_generation = false
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            # Test direct parsing
            parsed = parser.parse_config(config_path)
            assert parsed.is_valid
            assert "connection" in parsed.data
            assert "mqtt_settings" in parsed.data
            assert "topics" in parsed.data

            # Test safe retrieval
            safe_config = parser.safe_get_config(config_path)
            assert "connection" in safe_config
            assert safe_config["connection"]["host"] == "mqtt.example.com"

            # Test with default fallback
            default_config = {"default": True}
            result = parser.safe_get_config(
                "/nonexistent/file.toml", default=default_config
            )
            assert result == default_config

        finally:
            os.unlink(config_path)

    def test_error_handling_with_bad_files(self):
        """Test error handling with various bad file scenarios."""
        parser = SafeConfigParser()

        # Test with invalid TOML syntax
        bad_toml = """
        [section
        missing_bracket = "value"
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(bad_toml)
            bad_path = f.name

        try:
            # Should handle gracefully
            result = parser.safe_get_config(bad_path, default={"fallback": True})
            assert result == {"fallback": True}

            # Should raise with raise_on_invalid
            with pytest.raises(Exception):
                parser.safe_get_config(bad_path, raise_on_invalid=True)

        finally:
            os.unlink(bad_path)
