import os
import logging
import uuid
import threading
import queue

from typing import Dict, Any, Optional

from .clients.dsl import DSLExecutor
from .clients.auction import AuctionClient

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class RoleAuction:
    def __init__(self):
        try:
            self.dsl_id = os.getenv("ORG_ROLE_AUCTION_DSL_ID", "")
            if not self.dsl_id:
                raise ValueError(
                    "Missing ORG_ROLE_AUCTION_DSL_ID environment variable")

            self.dsl_executor = DSLExecutor(workflow_id=self.dsl_id)
            self.auction_client = AuctionClient(
                api_url=os.getenv("AUCTION_API_URL", "http://localhost:7000")
            )

            logger.info(f"RoleAuction initialized with DSL ID: {self.dsl_id}")

        except Exception as e:
            logger.error(
                f"Failed to initialize RoleAuction: {e}", exc_info=True)
            raise

    def execute(self, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            logger.info(
                f"Running DSL to produce auction input with input: {input_data}")
            output = self.dsl_executor.run(input_data)

            logger.info("Parsing DSL output to extract auction payload")
            auction_input = self.dsl_executor.get_final_output(output)

            logger.info(f"Submitting auction with input: {auction_input}")
            result = self.auction_client.submit_bid_and_wait(
                bid_payload=auction_input)

            logger.info(f"Auction result received: {result}")
            return result

        except Exception as e:
            logger.error(
                f"Error during RoleAuction execution: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


class RoleAuctionExecutor:
    def __init__(self):
        self.task_queue = queue.Queue()
        self.waiters: Dict[str, queue.Queue] = {}
        self.lock = threading.Lock()

        self.worker_thread = threading.Thread(
            target=self._worker_loop, daemon=True)
        self.worker_thread.start()

        logger.info(
            "RoleAuctionExecutor initialized and background worker started")

    def submit_task(self, input_data: Dict[str, Any]) -> queue.Queue:
        """Submits a task and returns a waiter queue to receive the result."""
        task_id = str(uuid.uuid4())
        waiter = queue.Queue(maxsize=1)

        with self.lock:
            self.waiters[task_id] = waiter

        self.task_queue.put((task_id, input_data))
        logger.info(f"Task {task_id} submitted to RoleAuctionExecutor")
        return waiter

    def _worker_loop(self):
        auction = RoleAuction()

        while True:
            try:
                task_id, input_data = self.task_queue.get()
                logger.info(f"Processing RoleAuction task {task_id}...")

                result = auction.execute(input_data)

                with self.lock:
                    waiter = self.waiters.pop(task_id, None)

                if waiter:
                    waiter.put(result)
                    logger.info(f"Result for task {task_id} placed in waiter")
                else:
                    logger.warning(
                        f"No waiter found for completed task {task_id}")

            except Exception as e:
                logger.error(
                    f"Error in RoleAuctionExecutor worker loop: {e}", exc_info=True)
