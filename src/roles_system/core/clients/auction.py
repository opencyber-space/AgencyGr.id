import os
import json
import logging
import requests
import asyncio
from threading import Thread, Event
from typing import Dict, Optional

from nats.aio.client import Client as NATS

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class AuctionClient:
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip("/")
        self.nats_url = os.getenv("ORG_NATS_CLIENT", "nats://localhost:4222")
        self.subject_id = os.getenv("ORG_ID", "default_org")
        self.topic = f"{self.subject_id}_bid_events"
        self.loop = asyncio.new_event_loop()
        self.nc = NATS()
        self.result = None
        self._event = Event()

    def submit_bid_and_wait(self, bid_payload: Dict, timeout: int = 30) -> Optional[Dict]:
        try:
            logger.info("Submitting bid task to API...")
            response = requests.post(
                f"{self.api_url}/bid-task/submit-task",
                json=bid_payload,
                timeout=10
            )
            if response.status_code != 200 or not response.json().get("success"):
                logger.error(f"API error: {response.text}")
                return {"success": False, "message": "Bid task submission failed"}

            logger.info("Bid task submitted. Waiting for evaluation result on NATS...")
            thread = Thread(target=self._run_event_loop)
            thread.start()

            if self._event.wait(timeout=timeout):
                return {"success": True, "data": self.result}
            else:
                logger.warning("Timeout reached waiting for bid evaluation result")
                return {"success": False, "message": "Timeout waiting for bid result"}

        finally:
            if self.loop.is_running():
                self.loop.call_soon_threadsafe(self.loop.stop)

    def _run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._listen_for_result())

    async def _listen_for_result(self):
        try:
            await self.nc.connect(self.nats_url, loop=self.loop)

            async def message_handler(msg):
                try:
                    data = msg.data.decode()
                    logger.info(f"Received bid event: {data}")
                    self.result = json.loads(data.replace("'", '"'))  # if JSON sent as str(dict)
                    self._event.set()
                    await self.nc.close()
                except Exception as e:
                    logger.error(f"Failed to parse bid event message: {e}")

            await self.nc.subscribe(self.topic, cb=message_handler)
            logger.info(f"Subscribed to NATS topic: {self.topic}")

            while not self._event.is_set():
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Error during NATS listening: {e}")
            self._event.set()
