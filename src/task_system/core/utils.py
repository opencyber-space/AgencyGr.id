import os
import json
import asyncio
import logging
import requests

from dsl_executor import new_dsl_workflow_executor, parse_dsl_output

from nats.aio.client import Client as NATS

from typing import Any, Dict

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class JobInvitesListener:
    def __init__(self, queue: asyncio.Queue):
        self.subject_id = os.getenv("ORG_ID")
        self.nats_url = os.getenv("ORG_NATS_URL", "nats://localhost:4222")
        self.topic = f"{self.subject_id}_bid_events"
        self.queue = queue
        self.nc = NATS()
        logger.info(
            f"JobInvitesListener initialized for subject: {self.subject_id}")

    async def _message_handler(self, msg):
        try:
            data = json.loads(msg.data.decode())
            logger.info(f"Received bid event on {msg.subject}")
            await self.queue.put(data)
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def run(self):
        try:
            await self.nc.connect(servers=[self.nats_url])
            await self.nc.subscribe(self.topic, cb=self._message_handler)
            logger.info(f"Subscribed to NATS topic: {self.topic}")
            while True:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"JobInvitesListener encountered an error: {e}")
        finally:
            await self.nc.drain()

    def start(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.run())


class BidSubmissionClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv(
            "BID_SYSTEM_URL", "http://localhost:8000")

    def submit_bid(self, bid_data: Dict[str, Any]) -> Dict[str, Any]:

        try:
            url = f"{self.base_url}/bids/submit-bid"
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=bid_data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"success": False, "message": str(e)}


class BidsWinnerListener:
    def __init__(self, queue: asyncio.Queue):
        self.subject_id = os.getenv("ORG_ID")
        self.nats_url = os.getenv("ORG_NATS_URL", "nats://localhost:4222")
        self.topic = f"{self.subject_id}_bid_events"
        self.queue = queue
        self.nc = NATS()
        logger.info(
            f"BidsWinnerListener initialized for subject: {self.subject_id}")

    async def _message_handler(self, msg):
        try:
            data = json.loads(msg.data.decode())
            logger.info(f"Received evaluation result on {msg.subject}")
            await self.queue.put(data)
        except Exception as e:
            logger.error(f"Error handling bid winner message: {e}")

    async def run(self):
        try:
            await self.nc.connect(servers=[self.nats_url])
            await self.nc.subscribe(self.topic, cb=self._message_handler)
            logger.info(f"Subscribed to NATS topic: {self.topic}")
            while True:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"BidsWinnerListener encountered an error: {e}")
        finally:
            await self.nc.drain()

    def start(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.run())


class TaskCreationClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv(
            "ORG_aTASK_CREATION_URL", "http://localhost:8000")
        self.endpoint = "/tasks/create"

    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:

        try:
            url = f"{self.base_url}{self.endpoint}"
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=task_data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}


class DSLExecutor:
    def __init__(
        self,
        workflow_id: str,
        workflows_base_uri: str = "",
        is_remote: bool = False,
        addons: Dict[str, Any] = None,
    ):

        self.workflow_id = workflow_id
        self.workflows_base_uri = workflows_base_uri or os.getenv(
            "WORKFLOWS_API_URL", "http://localhost:8000")
        self.is_remote = is_remote
        self.addons = addons or {}

        self.executor = new_dsl_workflow_executor(
            workflow_id=self.workflow_id,
            workflows_base_uri=self.workflows_base_uri,
            is_remote=self.is_remote,
            addons=self.addons
        )

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.executor.execute(input_data)

    def get_final_output(self, output: Dict[str, Any]) -> Any:
        return parse_dsl_output(output)
