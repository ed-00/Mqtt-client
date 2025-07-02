"""
MQTT Event Listener with Job Tracking

This module provides an EventListener class that connects to an MQTT broker,
listens for TOML-formatted messages, and processes them with job tracking capabilities.

Author: 
    - Abed Hameed (@ed-00)
Date: 
    - 2025-06-30
"""

import uuid
import asyncio
import tomllib
import logging
from enum import Enum
from datetime import datetime
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass, field

import tomli_w 
import amqtt.client as mqtt  # type: ignore
from .safe_config_parser import SafeConfigParser, ConfigError


class JobStatus(Enum):
    """Job execution status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DUPLICATE = "duplicate"


@dataclass
class JobInfo:
    """
    Information about a job run.

    Attributes:
        job_id (str): Unique identifier for the job
        status (JobStatus): Current status of the job
        started_at (datetime): When the job was first created
        completed_at (Optional[datetime]): When the job completed (None if still running)
        input_data (Optional[Dict[str, Any]]): The input data for the job
        result (Optional[Any]): The result returned by the job function
        error (Optional[str]): Error message if the job failed
    """

    job_id: str
    status: JobStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    input_data: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass(frozen=True)
class EventListenerConfig:
    """Unified configuration for the MQTT Event Listener - max 2 levels deep."""

    # Connection Settings
    host: str = "localhost"
    port: int = 1883
    client_id: str = "event-listener"
    username: str = "test"
    password: str = "test"
    uri: str = "mqtt://localhost:1883"

    # SSL/TLS Settings
    cafile: Optional[str] = None
    capath: Optional[str] = None
    cadata: Optional[str] = None
    additional_headers: Optional[Dict[str, Any]] = None

    # MQTT Client Settings
    keep_alive: int = 10
    ping_delay: int = 1
    default_qos: int = 0
    default_retain: bool = False
    auto_reconnect: bool = True
    connect_timeout: Optional[int] = None
    reconnect_retries: int = 2
    reconnect_max_interval: int = 10
    cleansession: bool = True

    # Topic Settings
    topic: str = "test"
    qos: int = 0
    retain: bool = False
    error_topic: str = "test/error"
    log_topic: str = "test/log"
    results_topic: str = "test/results"

    # Will Message (Level 2)
    will: Optional[Dict[str, Any]] = (
        None  # {topic: str, message: str, qos: int, retain: bool}
    )

    # Custom Topics (Level 2)
    custom_topics: Dict[str, Dict[str, Any]] = field(
        default_factory=dict
    )  # {topic_name: {qos: int, retain: bool}}

    # Job Tracking Settings
    max_jobs_in_memory: int = 5000  # Maximum number of jobs to keep in memory
    job_cleanup_interval: int = (
        259200  # Cleanup completed jobs older than this (seconds)
    )
    job_id_field: str = "job_id"  # Field name in TOML message containing job ID
    allow_job_id_generation: bool = (
        False  # Whether to generate ID if not found in message
    )
    duplicate_action: str = "skip"  # "skip", "reprocess", or "error" for duplicate jobs


@dataclass
class ReturnType:
    """
    Return type for processed messages.

    Attributes:
        data (Dict[str, Any]): The processed data to be published
        topic (str): MQTT topic to publish the result to
        qos (int): Quality of Service level for publishing
        retain (bool): Whether to retain the message on the broker
        message_id (int): Unique message identifier
        timestamp (datetime): When the message was processed
        job_id (str): The job ID associated with this result
    """

    data: Dict[str, Any]
    topic: str
    qos: int
    retain: bool
    message_id: int
    timestamp: datetime
    job_id: str  # Added job_id to return type
    


class EventListener:
    """
    MQTT Event Listener with job tracking capabilities.

    This class connects to an MQTT broker, subscribes to topics, and processes
    incoming TOML messages with comprehensive job tracking and duplicate detection.
    """

    def __init__(
        self,
        config: EventListenerConfig,
        config_parser: Optional[SafeConfigParser] = None,
    ) -> None:
        """
        Initialize the EventListener.

        Args:
            config (EventListenerConfig): Configuration object containing all settings
            config_parser (Optional[SafeConfigParser]): Custom config parser instance.
                If None, a default SafeConfigParser will be created.

        Returns:
            None
        """
        self.config = config

        # Job tracking storage
        self.jobs: Dict[str, JobInfo] = {}  # In-memory job storage
        self.job_lock = asyncio.Lock()  # Thread-safe access to jobs

        # Build MQTT client configuration dictionary
        mqtt_config: Dict[str, Any] = {
            "keep_alive": config.keep_alive,
            "ping_delay": config.ping_delay,
            "default_qos": config.default_qos,
            "default_retain": config.default_retain,
            "auto_reconnect": config.auto_reconnect,
            "connect_timeout": config.connect_timeout,
            "reconnect_retries": config.reconnect_retries,
            "reconnect_max_interval": config.reconnect_max_interval,
            "cleansession": config.cleansession,
        }

        # Add will message if configured
        if config.will:
            mqtt_config["will"] = config.will

        # Add custom topics if configured
        if config.custom_topics:
            mqtt_config["topics"] = config.custom_topics

        self.client = mqtt.MQTTClient(client_id=config.client_id, config=mqtt_config)
        self.is_running = False
        self.logger = logging.getLogger(__name__)
        self.config_parser = config_parser or SafeConfigParser(self.logger)

    def extract_job_id(self, toml_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract job ID from TOML data based on configured field name.

        Args:
            toml_data (Dict[str, Any]): Parsed TOML data dictionary

        Returns:
            Optional[str]: Job ID as string if found, None otherwise
        """
        job_id = toml_data.get(self.config.job_id_field)
        if job_id is not None:
            return str(job_id)
        return None

    def generate_job_id(self) -> Optional[str]:
        """
        Generate a unique job ID if allowed by configuration.

        Returns:
            Optional[str]: Generated UUID string if generation is allowed, None otherwise
        """
        if self.config.allow_job_id_generation:
            return str(uuid.uuid4())
        return None

    async def get_job_status(self, job_id: str) -> Optional[JobInfo]:
        """
        Get job information by ID.

        Args:
            job_id (str): The job ID to look up

        Returns:
            Optional[JobInfo]: JobInfo object if found, None otherwise
        """
        async with self.job_lock:
            return self.jobs.get(job_id)

    async def is_job_completed(self, job_id: str) -> bool:
        """
        Check if a job has completed (successfully or failed).

        Args:
            job_id (str): The job ID to check

        Returns:
            bool: True if job is completed or failed, False otherwise
        """
        job_info = await self.get_job_status(job_id)
        return job_info is not None and job_info.status in [
            JobStatus.COMPLETED,
            JobStatus.FAILED,
        ]

    async def is_job_running(self, job_id: str) -> bool:
        """
        Check if a job is currently running.

        Args:
            job_id (str): The job ID to check

        Returns:
            bool: True if job is currently running, False otherwise
        """
        job_info = await self.get_job_status(job_id)
        return job_info is not None and job_info.status == JobStatus.RUNNING

    async def job_exists(self, job_id: str) -> bool:
        """
        Check if a job exists in memory.

        Args:
            job_id (str): The job ID to check

        Returns:
            bool: True if job exists in memory, False otherwise
        """
        async with self.job_lock:
            return job_id in self.jobs

    async def cleanup_old_jobs(self) -> None:
        """
        Clean up old completed jobs to prevent memory bloat.

        Removes jobs that are older than the configured cleanup interval
        and enforces the maximum number of jobs in memory.

        Returns:
            None
        """
        current_time = datetime.now()
        cutoff_time = current_time.timestamp() - self.config.job_cleanup_interval

        async with self.job_lock:
            jobs_to_remove = []
            for job_id, job_info in self.jobs.items():
                if (
                    job_info.status
                    in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.DUPLICATE]
                    and job_info.completed_at
                    and job_info.completed_at.timestamp() < cutoff_time
                ):
                    jobs_to_remove.append(job_id)

            for job_id in jobs_to_remove:
                del self.jobs[job_id]

            # Also limit total number of jobs in memory
            if len(self.jobs) > self.config.max_jobs_in_memory:
                # Remove oldest completed jobs first
                sorted_jobs = sorted(
                    [
                        (jid, jinfo)
                        for jid, jinfo in self.jobs.items()
                        if jinfo.status
                        in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.DUPLICATE]
                    ],
                    key=lambda x: x[1].completed_at or datetime.min,
                )

                excess_jobs = sorted_jobs[
                    : len(self.jobs) - self.config.max_jobs_in_memory
                ]
                for job_id, _ in excess_jobs:
                    del self.jobs[job_id]

    async def _create_job(self, job_id: str, input_data: Dict[str, Any]) -> bool:
        """
        Create a new job entry.

        Args:
            job_id (str): Unique identifier for the job
            input_data (Dict[str, Any]): Input data for the job

        Returns:
            bool: True if job was created, False if it already exists
        """
        async with self.job_lock:
            if job_id in self.jobs:
                return False  # Job already exists

            job_info = JobInfo(
                job_id=job_id,
                status=JobStatus.PENDING,
                started_at=datetime.now(),
                input_data=input_data,
            )
            self.jobs[job_id] = job_info
            return True

    async def _mark_job_duplicate(self, job_id: str) -> None:
        """
        Mark a job as duplicate.

        Args:
            job_id (str): The job ID to mark as duplicate

        Returns:
            None
        """
        async with self.job_lock:
            if job_id in self.jobs:
                self.jobs[job_id].status = JobStatus.DUPLICATE
                self.jobs[job_id].completed_at = datetime.now()

    async def _update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        result: Any = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Update job status and completion time.

        Args:
            job_id (str): The job ID to update
            status (JobStatus): New status for the job
            result (Any, optional): Result data if job completed successfully
            error (Optional[str], optional): Error message if job failed

        Returns:
            None
        """
        async with self.job_lock:
            if job_id in self.jobs:
                self.jobs[job_id].status = status
                if status in [
                    JobStatus.COMPLETED,
                    JobStatus.FAILED,
                    JobStatus.DUPLICATE,
                ]:
                    self.jobs[job_id].completed_at = datetime.now()
                if result is not None:
                    self.jobs[job_id].result = result
                if error is not None:
                    self.jobs[job_id].error = error

    async def _connect(self) -> None:
        """
        Connect to the MQTT broker using configured settings.

        Returns:
            None

        Raises:
            OSError: If connection fails due to network issues
            ConnectionError: If broker connection is refused
            asyncio.TimeoutError: If connection times out
        """
        await self.client.connect(
            uri=self.config.uri,
            cleansession=self.config.cleansession,
            cafile=self.config.cafile,
            capath=self.config.capath,
            cadata=self.config.cadata,
            additional_headers=self.config.additional_headers,
        )

    async def _subscribe(self) -> None:
        """
        Subscribe to the configured MQTT topic.

        Returns:
            None

        Raises:
            OSError: If subscription fails due to network issues
            ValueError: If topic or QoS is invalid
        """
        await self.client.subscribe([(self.config.topic, self.config.qos)])

    async def run(
        self, func: Callable[[Dict[str, Any], str], Optional[ReturnType]]
    ) -> None:
        """
        Run the event listener with job tracking.

        This method connects to the MQTT broker, subscribes to the configured topic,
        and processes incoming messages with job tracking and duplicate detection.

        Args:
            func (Callable[[Dict[str, Any], str], Optional[ReturnType]]):
                Function that takes (toml_data, job_id) and returns ReturnType or None.
                The function will be called for each received message.

        Returns:
            None
        """
        try:
            await self._connect()
            await self._subscribe()
        except (OSError, ConnectionError, asyncio.TimeoutError) as e:
            self.logger.error("Error connecting to MQTT broker: %s", e)
            return

        self.is_running = True
        last_cleanup = datetime.now()

        while self.is_running:
            # Periodic cleanup of old jobs
            if (datetime.now() - last_cleanup).seconds > 300:  # Every 5 minutes
                await self.cleanup_old_jobs()
                last_cleanup = datetime.now()

            message = await self.client.deliver_message()
            if (
                (message is not None)
                and (message.publish_packet is not None)
                and (message.publish_packet.payload is not None)
                and (message.publish_packet.payload.data is not None)
            ):
                toml_input: str = message.publish_packet.payload.data.decode("utf-8")

                try:
                    # Use the safe config parser to parse the TOML data
                    toml_data = self.config_parser.safe_get_config(
                        toml_input,
                        default={},  # Return empty dict if parsing fails
                        raise_on_invalid=False,  # Don't raise on validation failures
                    )

                    # Skip processing if we got an empty config (parsing failed)
                    if not toml_data:
                        self.logger.warning("Received empty configuration, skipping")
                        continue

                except ConfigError as e:
                    self.logger.error("Configuration parsing error: %s", e)
                    continue
                except (ValueError, TypeError, UnicodeDecodeError) as e:
                    self.logger.error("Unexpected error parsing configuration: %s", e)
                    continue

                # Extract or generate job ID
                job_id = self.extract_job_id(toml_data)
                if job_id is None:
                    job_id = self.generate_job_id()
                    if job_id is None:
                        self.logger.error(
                            "No job ID found in message and generation disabled"
                        )
                        continue

                # Check if job already exists (duplicate detection)
                if await self.job_exists(job_id):
                    existing_job = await self.get_job_status(job_id)

                    if existing_job is None:
                        self.logger.warning(
                            "Job %s exists but cannot retrieve status", job_id
                        )
                        continue

                    if self.config.duplicate_action == "skip":
                        self.logger.info(
                            "Job %s already exists, skipping (status: %s)",
                            job_id,
                            existing_job.status,
                        )
                        await self._mark_job_duplicate(job_id)
                        continue
                    elif self.config.duplicate_action == "error":
                        self.logger.error(
                            "Job %s already exists, cannot reprocess", job_id
                        )
                        continue
                    elif self.config.duplicate_action == "reprocess":
                        if existing_job.status == JobStatus.RUNNING:
                            self.logger.warning(
                                "Job %s is currently running, skipping", job_id
                            )
                            continue
                        self.logger.info(
                            "Job %s exists, reprocessing as requested", job_id
                        )
                    else:
                        self.logger.warning(
                            "Unknown duplicate_action: %s, skipping",
                            self.config.duplicate_action,
                        )
                        continue

                # Create or update job entry
                job_created = await self._create_job(job_id, toml_data)
                if not job_created and self.config.duplicate_action != "reprocess":
                    continue

                self.logger.info("Processing job %s", job_id)

                try:
                    # Update job status to running
                    await self._update_job_status(job_id, JobStatus.RUNNING)

                    # Execute the function with job tracking
                    return_value = func(toml_data, job_id)

                    # Update job status to completed
                    await self._update_job_status(
                        job_id, JobStatus.COMPLETED, result=return_value
                    )
                    self.logger.info("Job %s completed successfully", job_id)

                except (ValueError, TypeError, AttributeError, RuntimeError) as e:
                    # Update job status to failed
                    await self._update_job_status(
                        job_id, JobStatus.FAILED, error=str(e)
                    )
                    self.logger.error("Job %s failed: %s", job_id, e)
                    continue

                if return_value is not None:
                    try:
                        # Use the topic from return_value or fallback to results_topic
                        topic: str = (
                            return_value.topic
                            if return_value.topic
                            else self.config.results_topic
                        )
                        # Ensure data is not None and serialize it
                        data = (
                            return_value.data if return_value.data is not None else {}
                        )
                        # Serialize data to TOML for publishing
                        serialized_data = tomli_w.dumps(data).encode('utf-8')
                        await self.client.publish(
                            topic,
                            serialized_data,
                            qos=return_value.qos,
                            retain=return_value.retain,
                        )
                        self.logger.info(
                            "Published result for job %s to topic %s", job_id, topic
                        )
                    except (OSError, ConnectionError, ValueError) as e:
                        self.logger.error(
                            "Error publishing result for job %s: %s", job_id, e
                        )
                        continue

            else:
                await asyncio.sleep(0.1)

    def stop(self) -> None:
        """
        Stop the event listener.

        Sets the is_running flag to False, which will cause the main loop
        in the run() method to exit.

        Returns:
            None
        """
        self.is_running = False

    async def get_all_jobs(self) -> Dict[str, JobInfo]:
        """
        Get all jobs currently in memory.

        Returns:
            Dict[str, JobInfo]: Dictionary mapping job IDs to JobInfo objects
        """
        async with self.job_lock:
            return self.jobs.copy()

    async def get_running_jobs(self) -> Dict[str, JobInfo]:
        """
        Get all currently running jobs.

        Returns:
            Dict[str, JobInfo]: Dictionary of job IDs to JobInfo objects
                                for jobs with RUNNING status
        """
        async with self.job_lock:
            return {
                jid: jinfo
                for jid, jinfo in self.jobs.items()
                if jinfo.status == JobStatus.RUNNING
            }

    async def get_completed_jobs(self) -> Dict[str, JobInfo]:
        """
        Get all completed jobs.

        Returns:
            Dict[str, JobInfo]: Dictionary of job IDs to JobInfo objects
                                for jobs with COMPLETED status
        """
        async with self.job_lock:
            return {
                jid: jinfo
                for jid, jinfo in self.jobs.items()
                if jinfo.status == JobStatus.COMPLETED
            }

    async def get_duplicate_jobs(self) -> Dict[str, JobInfo]:
        """
        Get all duplicate jobs.

        Returns:
            Dict[str, JobInfo]: Dictionary of job IDs to JobInfo objects
                                for jobs with DUPLICATE status
        """
        async with self.job_lock:
            return {
                jid: jinfo
                for jid, jinfo in self.jobs.items()
                if jinfo.status == JobStatus.DUPLICATE
            }

    async def _send_message(
        self, topic: str, data: str, qos: int, retain: bool
    ) -> None:
        """
        Send a message to the specified MQTT topic.

        Args:
            topic (str): MQTT topic to publish to
            data (str): Message data to send
            qos (int): Quality of Service level (0, 1, or 2)
            retain (bool): Whether to retain the message on the broker

        Returns:
            None

        Raises:
            OSError: If publishing fails due to network issues
            ValueError: If topic or QoS is invalid
        """
        # Encode string data to bytes for MQTT client
        data_bytes = data.encode('utf-8') if isinstance(data, str) else data
        await self.client.publish(topic, data_bytes, qos, retain)

    async def _send_message_with_toml(
        self, topic: str, toml_path: str, qos: int, retain: bool
    ) -> None:
        """
        Send a message to MQTT topic with data loaded from a TOML file.

        Args:
            topic (str): MQTT topic to publish to
            toml_path (str): Path to the TOML file to load
            qos (int): Quality of Service level (0, 1, or 2)
            retain (bool): Whether to retain the message on the broker

        Returns:
            None

        Raises:
            FileNotFoundError: If the TOML file doesn't exist
            tomllib.TOMLDecodeError: If the TOML file is malformed
            OSError: If publishing fails due to network issues
            ValueError: If topic or QoS is invalid
        """
        with open(toml_path, "rb") as f:
            toml_data = tomllib.load(f)
        await self.client.publish(topic, toml_data, qos, retain)
