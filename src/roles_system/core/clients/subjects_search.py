import os
import json
import logging
import asyncio
import websockets
from threading import Thread, Event
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class SubjectsSearch:
    def __init__(self, search_filter: Dict, dsl_workflow_id: Dict):
        self.search_filter = search_filter
        self.dsl_workflow_id = dsl_workflow_id
        self.ws_url = os.getenv("SUBJECTS_SEARCH_SERVER_WS_URL", "ws://localhost:9000")
        self.loop = asyncio.new_event_loop()
        self.result: Optional[List[str]] = None
        self._event = Event()

    def search(self, timeout: int = 30) -> List[str]:
        thread = Thread(target=self._run_loop)
        thread.start()

        completed = self._event.wait(timeout=timeout)
        if not completed:
            logger.warning("Search timed out.")
            return []

        return self.result or []

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._execute_ws_query())

    async def _execute_ws_query(self):
        try:
            async with websockets.connect(self.ws_url) as websocket:
                request_payload = {
                    "search_filter": self.search_filter,
                    "dsl_workflow_id": self.dsl_workflow_id,
                }
                await websocket.send(json.dumps(request_payload))
                logger.info(f"Sent search request: {request_payload}")

                response = await websocket.recv()
                logger.info(f"Received response: {response}")

                data = json.loads(response)
                self.result = data.get("subjects", [])
                self._event.set()
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self._event.set()
