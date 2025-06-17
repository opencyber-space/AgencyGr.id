import os
import asyncio
import json
import logging
import requests
from typing import Any, Dict, Optional
from nats.aio.client import Client as NATS

logger = logging.getLogger(__name__)

# Default permissive template: accepts any payload
DEFAULT_TEMPLATE = {
    "type": "object",
    "additionalProperties": True
}

class SessionClient:
    def __init__(
        self,
        api_base_url: str,
        nats_servers: Optional[list] = None
    ):
        
        self.api_base_url = api_base_url.rstrip('/')
        self.nats_servers = nats_servers or [os.getenv("ORG_NATS_URL", "nats://127.0.0.1:4222")]
        self.nc = NATS()
        self.loop = asyncio.get_event_loop()
        self._response_future: Optional[asyncio.Future] = None

    def create_session(
        self,
        session_id: str,
        message_data: Optional[Dict[str, Any]] = None,
        message_data_template: Optional[Dict[str, Any]] = None,
        expiry_date: Optional[int] = None,
        subject_id: Optional[str] = None
    ) -> Dict[str, Any]:
        
        payload = {
            "session_id": session_id,
            "message_data": message_data or {},
            "message_data_template": message_data_template or DEFAULT_TEMPLATE,
            "expiry_date": expiry_date,
            "subject_id": subject_id
        }
        url = f"{self.api_base_url}/sessions"
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.info(f"Created session {session_id}")
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {e}")
            raise

    def send_message(self, session_id: str, channel_id: str, message: str) -> Dict[str, Any]:
       
        url = f"{self.api_base_url}/sessions/{session_id}/send_message"
        payload = {
            "channel_id": channel_id,
            "message": message
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.info(f"Sent message to session {session_id} on channel {channel_id}")
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise

    def expire_sessions(self) -> Dict[str, Any]:
       
        url = f"{self.api_base_url}/sessions/expire"
        try:
            resp = requests.post(url, timeout=10)
            resp.raise_for_status()
            logger.info("Triggered expiry process")
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to trigger expiry: {e}")
            raise

    async def _nats_connect(self):
        if not self.nc.is_connected:
            await self.nc.connect(servers=self.nats_servers, loop=self.loop)
            logger.info(f"Connected to NATS servers: {self.nats_servers}")

    async def wait_for_response(self, subject_id: str, timeout: int = 60) -> Dict[str, Any]:
       
        await self._nats_connect()

        topic = f"{subject_id}__human_intervention_results"
        self._response_future = self.loop.create_future()

        async def message_handler(msg):
            data = json.loads(msg.data.decode())
            logger.info(f"Received NATS message on {msg.subject}: {data}")
            if not self._response_future.done():
                self._response_future.set_result(data)

        sid = await self.nc.subscribe(topic, cb=message_handler)
        logger.info(f"Subscribed to NATS topic {topic}")

        try:
            result = await asyncio.wait_for(self._response_future, timeout=timeout)
            return result
        finally:
            await self.nc.unsubscribe(sid)

    def reject_session(self, session_id: str) -> Dict[str, Any]:
        
        url = f"{self.api_base_url}/sessions/{session_id}"
        payload = {
            "status": "FAILED"
        }
        try:
            resp = requests.patch(url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.info(f"Rejected session {session_id}")
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to reject session {session_id}: {e}")
            raise

    def send_and_wait_for_response(
        self,
        session_id: str,
        channel_id: str,
        message: str,
        subject_id: str,
        timeout: int = 60
    ) -> Dict[str, Any]:
        
        self.send_message(session_id, channel_id, message)
        return self.loop.run_until_complete(self.wait_for_response(subject_id, timeout))
