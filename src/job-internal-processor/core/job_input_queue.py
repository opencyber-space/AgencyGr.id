import redis
import time
import json
import logging
from typing import Callable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JobInitiationListener")


class JobInitiationListener:
    def __init__(self, redis_url: str = "redis://localhost:6379", queue_name: str = "TASK_INPUT"):
        self.redis_url = redis_url
        self.queue_name = queue_name
        self.redis_conn = None

    def _connect(self):
        try:
            self.redis_conn = redis.Redis.from_url(
                self.redis_url, decode_responses=True)
            self.redis_conn.ping()
            logger.info("Connected to Redis.")
        except redis.RedisError as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_conn = None

    def _reconnect(self, delay=5):
        logger.info(f"Reconnecting to Redis in {delay} seconds...")
        time.sleep(delay)
        self._connect()

    def listen(self, handle_task: Callable[[dict], None]):

        while True:
            if not self.redis_conn:
                self._connect()
                if not self.redis_conn:
                    self._reconnect()
                    continue

            try:
                logger.info(f"Waiting for tasks on '{self.queue_name}'...")
                _, task_data = self.redis_conn.blpop(
                    self.queue_name, timeout=0)  # blocking pop
                logger.info(f"Received task: {task_data}")

                try:
                    task_json = json.loads(task_data)
                    handle_task(task_json)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in task data: {e}")

            except redis.RedisError as e:
                logger.error(f"Redis error: {e}")
                self._reconnect()
            except Exception as e:
                logger.exception(f"Unexpected error: {e}")
                time.sleep(5)
