import threading
import queue
import logging
import time
import os
from typing import Any, Dict

from .tasks.loader import TasksLoader
from .job_input_queue import JobInitiationListener
from .priority import TasksProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TasksInitiator")


class TasksInitiator:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.incoming_queue = queue.Queue()

        self.final_priority_queue = queue.PriorityQueue()

        # Start loader
        self._load_initial_tasks()

        self.redis_listener = JobInitiationListener(redis_url=redis_url)
        self.listener_thread = threading.Thread(
            target=self.redis_listener.listen,
            args=(self.handle_redis_task,),
            daemon=True
        )
        self.listener_thread.start()

        self.processor = TasksProcessor(
            incoming_queue=self.incoming_queue,
            final_priority_queue=self.final_priority_queue
        )
        self.processor_thread = threading.Thread(
            target=self._process_loop,
            daemon=True
        )
        self.processor_thread.start()

        logger.info("TasksInitiator fully initialized.")

    def _load_initial_tasks(self):
        try:
            loader = TasksLoader(redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"))
            tasks, sub_tasks = loader.load_pending_tasks()

            for task in tasks:
                self.incoming_queue.put((task.task_priority_value, {"type": "task", "data": task.to_dict()}))
            for sub_task in sub_tasks:
                self.incoming_queue.put((sub_task.sub_task_priority_value, {"type": "sub_task", "data": sub_task.to_dict()}))

            logger.info(f"Loaded {len(tasks)} tasks and {len(sub_tasks)} sub-tasks into incoming queue.")

        except Exception as e:
            logger.exception("Failed to load initial tasks.")

    def handle_redis_task(self, payload: Dict[str, Any]):
        try:
            task_type = payload.get("type")
            data = payload.get("data")

            if task_type in {"task", "sub_task"}:
                self.incoming_queue.put((0, {"type": task_type, "data": data}))
                logger.info(f"Received new {task_type} from Redis and pushed to incoming queue.")
            else:
                logger.warning("Unknown task type received from Redis.")

        except Exception as e:
            logger.exception("Error handling task from Redis.")

    def _process_loop(self):
        while True:
            try:
                self.processor.process_next()
                # Optional: sleep to reduce CPU usage
                time.sleep(0.1)
            except Exception as e:
                logger.exception("Processor loop error")
                time.sleep(1)

    def get_next_task(self) -> Dict[str, Any]:
        if not self.final_priority_queue.empty():
            return self.final_priority_queue.get()
        return None
