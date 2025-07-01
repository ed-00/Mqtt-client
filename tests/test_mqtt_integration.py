"""
Real MQTT Integration Tests

This module contains integration tests that connect to a real Mosquitto MQTT broker
and test the EventListener class with actual MQTT communication.
"""

import os
import json
import asyncio
import pytest

from Listener.event_listener import EventListener, EventListenerConfig, JobStatus, ReturnType
from datetime import datetime


@pytest.fixture
def mqtt_host():
    """Get MQTT host from environment or default to mosquitto."""
    return os.getenv("MQTT_HOST", "mosquitto")


@pytest.fixture
def mqtt_port():
    """Get MQTT port from environment or default to 1883."""
    return int(os.getenv("MQTT_BROKER_PORT", "1883"))


@pytest.fixture
def mqtt_username():
    """Get MQTT username from environment."""
    return os.getenv("MQTT_USERNAME", "user")


@pytest.fixture
def mqtt_password():
    """Get MQTT password from environment."""
    return os.getenv("MQTT_PASSWORD", "password")


@pytest.fixture
def mqtt_config(mqtt_host, mqtt_port, mqtt_username, mqtt_password):
    """Create MQTT configuration for testing EventListener."""
    return EventListenerConfig(
        host=mqtt_host,
        port=mqtt_port,
        uri=f"mqtt://{mqtt_username}:{mqtt_password}@{mqtt_host}:{mqtt_port}",
        client_id="test-event-listener",
        username=mqtt_username,
        password=mqtt_password,
        topic="test/eventlistener",
        keep_alive=30,
        allow_job_id_generation=True,
        max_jobs_in_memory=100,
        duplicate_action="skip"
    )


@pytest.mark.mqtt_integration
@pytest.mark.asyncio
class TestEventListenerConnection:
    """Test EventListener MQTT connection functionality."""

    async def test_eventlistener_basic_connection(self, mqtt_config):
        """Test basic EventListener connection to MQTT broker."""
        listener = EventListener(mqtt_config)
        
        try:
            # Test connection
            await listener._connect()
            
            # Verify client is connected
            assert listener.client is not None
            
            # Test disconnection
            await listener.client.disconnect()
            
        except Exception as e:
            pytest.fail(f"EventListener failed to connect: {e}")

    async def test_eventlistener_subscription(self, mqtt_config):
        """Test EventListener subscription to MQTT topic."""
        listener = EventListener(mqtt_config)
        
        try:
            # Connect and subscribe
            await listener._connect()
            await listener._subscribe()
            
            # Verify subscription was successful (no exception means success)
            assert listener.client is not None
            
            await listener.client.disconnect()
            
        except Exception as e:
            pytest.fail(f"EventListener subscription failed: {e}")

    async def test_eventlistener_publish_message(self, mqtt_config):
        """Test EventListener message publishing."""
        listener = EventListener(mqtt_config)
        
        try:
            await listener._connect()
            
            # Test publishing a message
            test_message = "Hello from EventListener!"
            await listener._send_message(
                topic="test/publish", 
                data=test_message, 
                qos=1, 
                retain=False
            )
            
            await listener.client.disconnect()
            
        except Exception as e:
            pytest.fail(f"EventListener message publishing failed: {e}")


@pytest.mark.mqtt_integration
@pytest.mark.asyncio
class TestEventListenerJobTracking:
    """Test EventListener job tracking functionality."""

    async def test_job_creation_and_tracking(self, mqtt_config):
        """Test job creation and status tracking."""
        listener = EventListener(mqtt_config)
        
        # Test job creation
        job_id = "test-job-123"
        input_data = {"action": "test", "data": "sample"}
        
        success = await listener._create_job(job_id, input_data)
        assert success is True
        
        # Test job exists
        exists = await listener.job_exists(job_id)
        assert exists is True
        
        # Test job status
        job_info = await listener.get_job_status(job_id)
        assert job_info is not None
        assert job_info.job_id == job_id
        assert job_info.status == JobStatus.PENDING
        assert job_info.input_data == input_data

    async def test_job_status_updates(self, mqtt_config):
        """Test job status update functionality."""
        listener = EventListener(mqtt_config)
        
        job_id = "test-job-status"
        input_data = {"test": "data"}
        
        # Create job
        await listener._create_job(job_id, input_data)
        
        # Update to running
        await listener._update_job_status(job_id, JobStatus.RUNNING)
        
        running = await listener.is_job_running(job_id)
        assert running is True
        
        # Update to completed
        result_data = {"result": "success"}
        await listener._update_job_status(job_id, JobStatus.COMPLETED, result=result_data)
        
        completed = await listener.is_job_completed(job_id)
        assert completed is True
        
        job_info = await listener.get_job_status(job_id)
        assert job_info is not None
        assert job_info.status == JobStatus.COMPLETED
        assert job_info.result == result_data

    async def test_duplicate_job_handling(self, mqtt_config):
        """Test duplicate job detection and handling."""
        listener = EventListener(mqtt_config)
        
        job_id = "duplicate-test-job"
        input_data = {"duplicate": "test"}
        
        # Create first job
        success1 = await listener._create_job(job_id, input_data)
        assert success1 is True
        
        # Try to create duplicate job
        success2 = await listener._create_job(job_id, input_data)
        assert success2 is False  # Should fail for duplicate
        
        # Mark as duplicate
        await listener._mark_job_duplicate(job_id)
        
        job_info = await listener.get_job_status(job_id)
        assert job_info is not None
        assert job_info.status == JobStatus.DUPLICATE


@pytest.mark.mqtt_integration
@pytest.mark.asyncio
class TestEventListenerMessageProcessing:
    """Test EventListener message processing with real MQTT."""

    async def test_eventlistener_toml_message_processing(self, mqtt_config):
        """Test EventListener processing TOML messages from MQTT."""
        # Create a test processor function
        processed_messages = []
        
        def test_processor(toml_data, job_id):
            processed_messages.append({
                "toml_data": toml_data,
                "job_id": job_id,
                "timestamp": datetime.now()
            })
            return ReturnType(
                data={"processed": True, "job_id": job_id},
                topic="test/results",
                qos=1,
                retain=False,
                message_id=1,
                timestamp=datetime.now(),
                job_id=job_id
            )
        
        # Configure listener for test
        test_config = EventListenerConfig(
            host=mqtt_config.host,
            port=mqtt_config.port,
            uri=mqtt_config.uri,
            client_id="test-toml-processing",
            username=mqtt_config.username,
            password=mqtt_config.password,
            topic="test/toml/processing",
            allow_job_id_generation=True
        )
        listener = EventListener(test_config)
        
        try:
            # Start listener in background
            listener_task = asyncio.create_task(listener.run(test_processor))
            
            # Give listener time to connect and subscribe
            await asyncio.sleep(1.0)
            
            # Send a TOML message
            test_toml = """
job_id = "toml-processing-test"
action = "process_data"
data = "test_payload"
timestamp = "2024-01-01T12:00:00Z"
"""
            
            await listener._send_message(
                topic=test_config.topic,
                data=test_toml,
                qos=1,
                retain=False
            )
            
            # Wait for processing
            await asyncio.sleep(2.0)
            
            # Stop listener
            listener.stop()
            await asyncio.sleep(0.5)
            listener_task.cancel()
            
            try:
                await listener_task
            except asyncio.CancelledError:
                pass
            
            # Verify message was processed
            assert len(processed_messages) >= 1
            
            # Check job tracking
            job_info = await listener.get_job_status("toml-processing-test")
            assert job_info is not None
            assert job_info.job_id == "toml-processing-test"
            
        except Exception as e:
            listener.stop()
            pytest.fail(f"TOML message processing test failed: {e}")

    async def test_eventlistener_job_id_generation(self, mqtt_config):
        """Test EventListener job ID generation when not provided."""
        processed_jobs = []
        
        def job_id_test_processor(toml_data, job_id):
            processed_jobs.append(job_id)
            return None
        
        # Enable job ID generation
        test_config = EventListenerConfig(
            host=mqtt_config.host,
            port=mqtt_config.port,
            uri=mqtt_config.uri,
            client_id="test-job-generation",
            username=mqtt_config.username,
            password=mqtt_config.password,
            topic="test/job/generation",
            allow_job_id_generation=True
        )
        listener = EventListener(test_config)
        
        try:
            listener_task = asyncio.create_task(listener.run(job_id_test_processor))
            await asyncio.sleep(1.0)
            
            # Send message without job_id
            test_toml_no_id = """
action = "test_without_id"
data = "no_job_id_provided"
"""
            
            await listener._send_message(
                topic=test_config.topic,
                data=test_toml_no_id,
                qos=1,
                retain=False
            )
            
            await asyncio.sleep(2.0)
            
            listener.stop()
            listener_task.cancel()
            
            try:
                await listener_task
            except asyncio.CancelledError:
                pass
            
            # Verify job ID was generated
            assert len(processed_jobs) >= 1
            generated_job_id = processed_jobs[0]
            assert generated_job_id is not None
            assert len(generated_job_id) > 0  # Should be a UUID string
            
        except Exception as e:
            listener.stop()
            pytest.fail(f"Job ID generation test failed: {e}")


@pytest.mark.mqtt_integration
@pytest.mark.asyncio
class TestEventListenerErrorHandling:
    """Test EventListener error handling and recovery."""

    async def test_eventlistener_invalid_toml_handling(self, mqtt_config):
        """Test EventListener handling of invalid TOML messages."""
        error_messages = []
        
        def error_test_processor(toml_data, job_id):
            # This should not be called for invalid TOML
            pytest.fail("Processor called with invalid TOML")
        
        test_config = EventListenerConfig(
            host=mqtt_config.host,
            port=mqtt_config.port,
            uri=mqtt_config.uri,
            client_id="test-error-handling",
            username=mqtt_config.username,
            password=mqtt_config.password,
            topic="test/error/handling",
            allow_job_id_generation=True
        )
        listener = EventListener(test_config)
        
        try:
            listener_task = asyncio.create_task(listener.run(error_test_processor))
            await asyncio.sleep(1.0)
            
            # Send invalid TOML
            invalid_toml = "invalid = toml content ["
            
            await listener._send_message(
                topic=test_config.topic,
                data=invalid_toml,
                qos=1,
                retain=False
            )
            
            await asyncio.sleep(2.0)
            
            listener.stop()
            listener_task.cancel()
            
            try:
                await listener_task
            except asyncio.CancelledError:
                pass
            
            # No exceptions should be raised - invalid TOML should be handled gracefully
            
        except Exception as e:
            listener.stop()
            pytest.fail(f"Invalid TOML handling test failed: {e}")

    async def test_eventlistener_job_cleanup(self, mqtt_config):
        """Test EventListener job cleanup functionality."""
        test_config = EventListenerConfig(
            host=mqtt_config.host,
            port=mqtt_config.port,
            uri=mqtt_config.uri,
            client_id="test-job-cleanup",
            username=mqtt_config.username,
            password=mqtt_config.password,
            topic="test/cleanup",
            max_jobs_in_memory=3
        )
        listener = EventListener(test_config)
        
        # Create multiple jobs
        for i in range(5):
            job_id = f"cleanup-test-{i}"
            await listener._create_job(job_id, {"test": i})
            await listener._update_job_status(job_id, JobStatus.COMPLETED)
        
        # Trigger cleanup
        await listener.cleanup_old_jobs()
        
        # Check that job count is within limits
        all_jobs = await listener.get_all_jobs()
        assert len(all_jobs) <= test_config.max_jobs_in_memory 