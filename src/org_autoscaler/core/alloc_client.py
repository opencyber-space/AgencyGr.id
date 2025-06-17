import requests
import logging
import os
import json
import asyncio

from nats.aio.client import Client as NATS

from typing import Any, Dict

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class APIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class SubjectResourceAllocator:
    def __init__(self):
        self.base_url = os.getenv("GLOBAL_RESOURCE_ALLOCATOR_API_URL", "http://localhost:8893").rstrip('/')
        logger.info(f"SubjectResourceAllocator initialized with base URL: {self.base_url}")

    def _handle_response(self, response):
        try:
            response.raise_for_status()
            json_data = response.json()
            if not json_data.get("success", False):
                raise APIError(json_data.get("error", "Unknown error"), response.status_code)
            return json_data.get("data")
        except requests.RequestException as e:
            logger.error(f"HTTP error: {e}")
            raise
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise

    def allocate_resources(self, uuid: str, subject_id: str, new_replicas: int):
        url = f"{self.base_url}/allocate"
        payload = {
            "uuid": uuid,
            "subject_id": subject_id,
            "replicas": new_replicas
        }
        try:
            response = requests.post(url, json=payload)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Failed to allocate resources for {subject_id}: {e}")
            raise


class AllocationResponseListener:
    def __init__(self):
        self.nats_url = os.getenv("NATS_ORG_URL", "nats://localhost:4222")
        self.subject = f"{os.getenv('ORG_ID', 'default_org')}__alloc_response"
        self.nc = NATS()
        self.loop = asyncio.new_event_loop()
        logger.info(f"AllocationResponseListener will subscribe to topic: {self.subject}")

    async def _message_handler(self, msg):
        try:
            data = json.loads(msg.data.decode())
            uuid = data.get("uuid")
            response = data.get("response", {})
            logger.info(f"Received allocation response for UUID={uuid}: {response}")
        except Exception as e:
            logger.error(f"Failed to process message: {e}")

    async def _connect_and_listen(self):
        await self.nc.connect(servers=[self.nats_url], loop=self.loop)
        await self.nc.subscribe(self.subject, cb=self._message_handler)
        logger.info(f"Subscribed to NATS subject: {self.subject}")
        try:
            while True:
                await asyncio.sleep(1)
        finally:
            await self.nc.drain()

    def start(self):
        logger.info("Starting AllocationResponseListener event loop")
        self.loop.run_until_complete(self._connect_and_listen())


class QuotaClient:
    def __init__(self, base_url: str = None):
        self.base_url = (base_url or os.getenv("QUOTA_SERVER_URL", "http://localhost:8000")).rstrip("/")
        logger.info(f"QuotaClient initialized with base URL: {self.base_url}")

    def _handle_response(self, response: requests.Response) -> Any:
        try:
            response.raise_for_status()
            json_data = response.json()
            if not json_data.get("success", False):
                raise APIError(json_data.get("error", "Unknown error"), response.status_code)
            return json_data.get("data")
        except requests.RequestException as e:
            logger.error(f"HTTP error: {e}")
            raise
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise

    def get_metrics_report(self) -> Dict:
        url = f"{self.base_url}/metrics/report"
        logger.info(f"Fetching metrics report from {url}")
        response = requests.get(url)
        return self._handle_response(response)

    def update_quota(self, quota_id: str, update_fields: Dict[str, Any]) -> Dict:
        url = f"{self.base_url}/quota/{quota_id}"
        logger.info(f"Updating quota {quota_id} with fields {update_fields}")
        response = requests.put(url, json=update_fields)
        return self._handle_response(response)