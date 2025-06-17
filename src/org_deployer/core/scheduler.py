import time
import threading
import redis
import json
import os
from datetime import datetime
from typing import Dict
from .crud import OrgCreationTaskDatabase
from .schema import OrgCreationTask
import logging

logger = logging.getLogger(__name__)


class Scheduler(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True

        # Redis setup
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True)

        # DB and in-memory cache
        self.task_db = OrgCreationTaskDatabase()
        self.scheduled_tasks: Dict[str, OrgCreationTask] = {}

        self.load_pending_tasks()
        self.start()

    def load_pending_tasks(self):
        logger.info("Loading pending tasks into Scheduler")
        success, tasks = self.task_db.query({"status": "pending"})
        if not success:
            logger.error(f"Failed to load pending tasks: {tasks}")
            return

        for task_data in tasks:
            task = OrgCreationTask.from_dict(task_data)
            if task.creation_schedule != "-1":
                self.scheduled_tasks[task.org_creation_task_id] = task
                self.redis.set(
                    f"scheduler:task:{task.org_creation_task_id}", json.dumps(task.to_dict()))
        logger.info(f"{len(self.scheduled_tasks)} tasks loaded into Scheduler")

    def run(self):
        while True:
            try:
                now_ts = int(time.time())
                to_trigger = []

                for task_id, task in list(self.scheduled_tasks.items()):
                    try:
                        schedule_ts = int(task.creation_schedule)
                        if now_ts >= schedule_ts:
                            to_trigger.append(task_id)
                    except ValueError:
                        logger.warning(
                            f"Ignoring task {task_id} with invalid schedule: {task.creation_schedule}")

                for task_id in to_trigger:
                    self.trigger_task(task_id)

                time.sleep(300)  
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                time.sleep(60) 

    def trigger_task(self, task_id: str):
        try:
            logger.info(f"Triggering task {task_id}")
            submit_task_for_creation(task_id)
            self.scheduled_tasks.pop(task_id, None)
            self.redis.delete(f"scheduler:task:{task_id}")
        except Exception as e:
            logger.error(f"Error triggering task {task_id}: {e}")


def submit_task_for_creation(task_id: str):
    logger.info(f"submit_task_for_creation() called for task_id {task_id}")




