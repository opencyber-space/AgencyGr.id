import os
import json
import logging
import asyncio
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrTimeout, ErrNoServers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentQueueClient")


class AgentQueueClient:
    def __init__(self):
        self.nats_url = os.getenv("ORG_NATS_URL", "nats://localhost:4222")
        self.sender_subject_id = os.getenv("ORG_ID", "org-undefined")
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self.nc = NATS()

        try:
            self._loop.run_until_complete(self._connect())
        except Exception as e:
            logger.exception("Failed to connect to NATS during initialization.")

    async def _connect(self):
        try:
            await self.nc.connect(servers=[self.nats_url], io_loop=self._loop)
            logger.info(f"Connected to NATS at {self.nats_url}")
        except ErrNoServers as e:
            logger.error(f"Could not connect to NATS server: {e}")
            raise

    def push(self, subject_id: str, task_data: dict):
        try:
            self._loop.run_until_complete(self._push_internal(subject_id, task_data))
        except Exception as e:
            logger.exception(f"Error pushing message to {subject_id}")

    async def _push_internal(self, subject_id: str, task_data: dict):
        if not self.nc.is_connected:
            await self._connect()

        try:
            message = {
                "event_type": "task",
                "sender_subject_id": self.sender_subject_id,
                "event_data": task_data
            }
            await self.nc.publish(subject_id, json.dumps(message).encode())
            logger.info(f"Task pushed to agent subject queue: {subject_id}")
        except (ErrConnectionClosed, ErrTimeout) as e:
            logger.error(f"NATS publish failed: {e}")
        except Exception as e:
            logger.exception("Unexpected error in _push_internal")

    def close(self):
        try:
            self._loop.run_until_complete(self.nc.close())
            logger.info("Closed NATS connection.")
        except Exception:
            pass
