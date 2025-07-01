"""
MQTT Connectivity Test Script

This script tests MQTT connectivity using different approaches:
1. Direct amqtt library connection
2. EventListener class functionality
3. Message publishing and subscribing
4. Authentication testing
"""

import os
import asyncio
import logging

from datetime import datetime
from typing import Dict, Any, Optional

import amqtt.client as mqtt  # type: ignore
from amqtt.mqtt.constants import QOS_0  # type: ignore

from Listener.event_listener import EventListener, EventListenerConfig, ReturnType

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MQTTTester:
    """Test MQTT connectivity and functionality."""

    def __init__(self):
        """Initialize the MQTT tester with the correct Docker network configuration."""
        self.test_results = {"timestamp": datetime.now().isoformat(), "tests": {}}

        # Use only the mosquitto hostname since we're in Docker containers
        self.host_config = {
            "name": "Mosquitto Docker Container",
            "host": os.getenv("MQTT_HOST", "mosquitto"),
            "port": int(os.getenv("MQTT_PORT", "1883")),
            "username": os.getenv("MQTT_USERNAME", "user"),
            "password": os.getenv("MQTT_PASSWORD", "password"),
        }

    async def test_authenticated_connection(self) -> Dict[str, Any]:
        """Test MQTT connection with authentication (required by our broker)."""
        test_name = "authenticated_connection"
        logger.info(
            "Testing authenticated connection to %s:%s",
            self.host_config["host"],
            self.host_config["port"],
        )

        result = {
            "test_name": test_name,
            "host": self.host_config["host"],
            "port": self.host_config["port"],
            "username": self.host_config["username"],
            "success": False,
            "error": None,
            "details": {},
        }

        client = mqtt.MQTTClient(client_id="test-auth-connection")

        try:
            # Test connection with auth (required by broker)
            uri = f"mqtt://{self.host_config['username']}:{self.host_config['password']}@{self.host_config['host']}:{self.host_config['port']}"
            logger.info(
                "Connecting with auth to: %s:%s",
                self.host_config["host"],
                self.host_config["port"],
            )

            connect_result = await asyncio.wait_for(client.connect(uri), timeout=10.0)

            result["details"]["connection_result"] = connect_result

            # Check connection state more robustly
            state = "unknown"
            if client.session and hasattr(client.session.transitions, "state"):
                state_obj = client.session.transitions.state
                state = state_obj.name if hasattr(state_obj, "name") else str(state_obj)
            result["details"]["state"] = state

            if client.session and state == "connected":
                result["success"] = True
                logger.info(
                    "✅ Authenticated connection successful to %s",
                    self.host_config["host"],
                )

                # Test disconnection
                await client.disconnect()
                result["details"]["disconnection"] = "successful"
            else:
                result["error"] = (
                    f"Connection state: {client.session.transitions.state.name if client.session else 'no session'}"
                )

        except asyncio.TimeoutError:
            result["error"] = "Connection timeout (10s)"
            logger.error(
                "❌ Auth connection timeout to %s",
                self.host_config["host"],
            )
        except Exception as e:
            result["error"] = str(e)
            logger.error(
                "❌ Auth connection failed to %s: %s",
                self.host_config["host"],
                e,
            )
        finally:
            try:
                if (
                    client.session
                    and client.session.transitions.state.name != "disconnected"
                ):
                    await client.disconnect()
            except (OSError, RuntimeError, asyncio.TimeoutError):
                pass

        return result

    async def test_publish_subscribe(self) -> Dict[str, Any]:
        """Test MQTT publish and subscribe functionality."""
        test_name = "pub_sub_test"
        logger.info(
            "Testing publish/subscribe to %s:%s",
            self.host_config["host"],
            self.host_config["port"],
        )

        result = {
            "test_name": test_name,
            "host": self.host_config["host"],
            "port": self.host_config["port"],
            "success": False,
            "error": None,
            "details": {},
        }

        publisher = mqtt.MQTTClient(client_id="test-publisher")
        subscriber = mqtt.MQTTClient(client_id="test-subscriber")

        try:
            uri = f"mqtt://{self.host_config['username']}:{self.host_config['password']}@{self.host_config['host']}:{self.host_config['port']}"

            # Connect both clients
            await asyncio.wait_for(publisher.connect(uri), timeout=10.0)
            await asyncio.wait_for(subscriber.connect(uri), timeout=10.0)

            test_topic = "test/connectivity"
            test_message = f"Hello from MQTT test at {datetime.now().isoformat()}"

            # Subscribe
            await subscriber.subscribe([(test_topic, QOS_0)])
            await asyncio.sleep(0.2)  # Allow subscription to establish

            # Publish
            await publisher.publish(test_topic, test_message.encode(), qos=QOS_0)

            # Wait for message
            try:
                message = await asyncio.wait_for(
                    subscriber.deliver_message(), timeout=5.0
                )
                if message and hasattr(message, "data"):
                    received_message = message.data.decode()

                    # Get topic name (attribute varies by amqtt version)
                    topic = getattr(
                        message, "topic_name", getattr(message, "topic", "unknown")
                    )

                    result["details"]["published_message"] = test_message
                    result["details"]["received_message"] = received_message
                    result["details"]["topic"] = topic

                    if received_message == test_message and topic == test_topic:
                        result["success"] = True
                        logger.info(
                            "✅ Publish/Subscribe successful to %s",
                            self.host_config["host"],
                        )
                    else:
                        result["error"] = "Message mismatch or topic mismatch"
                else:
                    result["error"] = "No message data received"
                    return result

            except asyncio.TimeoutError:
                result["error"] = "No message received within 5 seconds"
                logger.error(
                    "❌ Message timeout from %s",
                    self.host_config["host"],
                )

        except Exception as e:
            result["error"] = str(e)
            logger.error(
                "❌ Publish/Subscribe failed to %s: %s",
                self.host_config["host"],
                e,
            )
        finally:
            try:
                await publisher.disconnect()
                await subscriber.disconnect()
            except (OSError, RuntimeError, asyncio.TimeoutError):
                pass

        return result

    async def test_event_listener(self) -> Dict[str, Any]:
        """Test the EventListener class functionality."""
        test_name = "event_listener_test"
        logger.info(
            "Testing EventListener to %s:%s",
            self.host_config["host"],
            self.host_config["port"],
        )

        result = {
            "test_name": test_name,
            "host": self.host_config["host"],
            "port": self.host_config["port"],
            "success": False,
            "error": None,
            "details": {},
        }

        try:
            # Configure EventListener
            config = EventListenerConfig(
                host=self.host_config["host"],
                port=self.host_config["port"],
                username=self.host_config["username"],
                password=self.host_config["password"],
                client_id="test-event-listener",
                topic="test/event_listener",
                allow_job_id_generation=True,
                max_jobs_in_memory=10,
            )

            listener = EventListener(config)

            # Test processor function
            processed_data = []

            def test_processor(
                data: Dict[str, Any], job_id: str
            ) -> Optional[ReturnType]:
                """Test message processor."""
                processed_data.append({"data": data, "job_id": job_id})
                logger.info(
                    "Processed message with job_id: %s",
                    job_id,
                )

                return ReturnType(
                    data={"result": "processed", "original_data": data},
                    topic="test/results",
                    qos=0,
                    retain=False,
                    message_id=1,
                    timestamp=datetime.now(),
                    job_id=job_id,
                )

            # Test connection by attempting to start (but cancel quickly)
            listener_task = None
            try:
                listener_task = asyncio.create_task(listener.run(test_processor))

                # Give it time to connect
                await asyncio.sleep(2.0)

                # Check if it's running (connected)
                if listener.is_running:
                    result["success"] = True
                    result["details"]["connection_established"] = True
                    logger.info(
                        "✅ EventListener connected successfully to %s",
                        self.host_config["host"],
                    )
                else:
                    result["error"] = "EventListener failed to start/connect"

            except Exception as e:
                result["error"] = f"EventListener error: {str(e)}"
            finally:
                # Stop the listener
                if listener_task and not listener_task.done():
                    listener.stop()
                    try:
                        await asyncio.wait_for(listener_task, timeout=5.0)
                    except asyncio.TimeoutError:
                        listener_task.cancel()

        except Exception as e:
            result["error"] = str(e)
            logger.error(
                "❌ EventListener test failed to %s: %s",
                self.host_config["host"],
                e,
            )

        return result

    async def test_message_roundtrip(self) -> Dict[str, Any]:
        """Test complete message roundtrip with TOML processing."""
        test_name = "toml_message_roundtrip"
        logger.info("Testing TOML message processing roundtrip")

        result = {
            "test_name": test_name,
            "host": self.host_config["host"],
            "port": self.host_config["port"],
            "success": False,
            "error": None,
            "details": {},
        }

        publisher = mqtt.MQTTClient(client_id="test-toml-publisher")

        try:
            uri = f"mqtt://{self.host_config['username']}:{self.host_config['password']}@{self.host_config['host']}:{self.host_config['port']}"
            await asyncio.wait_for(publisher.connect(uri), timeout=10.0)

            # Test TOML message
            toml_message = """
job_id = "test-job-123"
message_type = "process_data"
timestamp = "2025-01-02T12:00:00Z"

[data]
input_value = 42
operation = "multiply"
factor = 2

[metadata]
source = "test_script"
priority = "high"
"""

            test_topic = "test/toml_processing"

            # Publish TOML message
            await publisher.publish(test_topic, toml_message.encode(), qos=QOS_0)

            result["details"]["published_toml"] = toml_message
            result["details"]["topic"] = test_topic
            result["success"] = True
            logger.info(
                "✅ TOML message published successfully",
            )

        except Exception as e:
            result["error"] = str(e)
            logger.error(
                "❌ TOML message test failed: %s",
                e,
            )
        finally:
            try:
                await publisher.disconnect()
            except (OSError, RuntimeError, asyncio.TimeoutError):
                pass

        return result

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all MQTT connectivity tests."""
        logger.info("🚀 Starting MQTT Connectivity Tests")
        logger.info("============================================================")
        logger.info("📡 Testing: %s", self.host_config['name'])
        logger.info("🔗 Host: %s:%s", self.host_config['host'], self.host_config['port'])
        logger.info("👤 Username: %s", self.host_config['username'])
        logger.info("----------------------------------------")

        # Test authenticated connection
        auth_result = await self.test_authenticated_connection()
        self.test_results["tests"][auth_result["test_name"]] = auth_result

        # Only proceed with other tests if connection works
        if auth_result["success"]:
            # Test publish/subscribe
            pubsub_result = await self.test_publish_subscribe()
            self.test_results["tests"][pubsub_result["test_name"]] = pubsub_result

            # Test EventListener
            listener_result = await self.test_event_listener()
            self.test_results["tests"][listener_result["test_name"]] = listener_result

            # Test TOML message processing
            toml_result = await self.test_message_roundtrip()
            self.test_results["tests"][toml_result["test_name"]] = toml_result
        else:
            logger.info("⏭️  Skipping other tests due to connection failure")

        return self.test_results

    def print_summary(self):
        """Print a summary of test results."""
        logger.info("\n============================================================")
        logger.info("📊 MQTT CONNECTIVITY TEST SUMMARY")
        logger.info("============================================================")

        total_tests = len(self.test_results["tests"])
        passed_tests = sum(
            1 for test in self.test_results["tests"].values() if test["success"]
        )

        logger.info("Total Tests: %s", total_tests)
        logger.info("Passed: %s", passed_tests)
        logger.info("Failed: %s", total_tests - passed_tests)
        logger.info("Success Rate: %.1f%%", (passed_tests/total_tests)*100 if total_tests > 0 else 0)

        logger.info("\n📋 Detailed Results:")
        for test_name, result in self.test_results["tests"].items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            logger.info("%s | %s", status, test_name)
            if result["error"]:
                logger.info("    Error: %s", result['error'])


async def main():
    """Main test function."""
    tester = MQTTTester()

    try:
        results = await tester.run_all_tests()
        tester.print_summary()

        # Save results to file
        import json

        with open("mqtt_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info("\n💾 Results saved to: mqtt_test_results.json")

        return results

    except Exception as e:
        logger.error("Test execution failed: %s", e)
        raise


if __name__ == "__main__":
    asyncio.run(main())
