import os
import logging
import redis
from typing import Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OrgExecutionConfigProvider")


class OrgExecutionConfigProvider:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_conn = redis.Redis.from_url(self.redis_url, decode_responses=True)

    def _key(self, org_id: str, key: str) -> str:
        return f"org_config:{org_id}:{key}"

    def get(self, org_id: str, key: str) -> Optional[str]:
        try:
            redis_key = self._key(org_id, key)
            value = self.redis_conn.get(redis_key)
            if value is not None:
                logger.info(f"Fetched config [{key}] for org [{org_id}]: {value}")
            else:
                logger.warning(f"Config [{key}] not found for org [{org_id}]")
            return value
        except Exception as e:
            logger.exception(f"Failed to get config [{key}] for org [{org_id}]")
            return None

    def set(self, org_id: str, key: str, value: str) -> bool:
        try:
            redis_key = self._key(org_id, key)
            self.redis_conn.set(redis_key, value)
            logger.info(f"Set config [{key}] for org [{org_id}] = {value}")
            return True
        except Exception as e:
            logger.exception(f"Failed to set config [{key}] for org [{org_id}]")
            return False

    def get_all(self, org_id: str, keys: List[str]) -> dict:
        config = {}
        for key in keys:
            val = self.get(org_id, key)
            if val is not None:
                config[key] = val
        return config
