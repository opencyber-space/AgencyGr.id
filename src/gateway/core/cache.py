import redis
import json
import logging
from typing import Optional, Dict, Any

from .schema import APIRoleAssociation, APIConstraintMap
from .mgmt_db import OrgAccessControlDB

logger = logging.getLogger("AccessCache")
logging.basicConfig(level=logging.INFO)


class AccessCache:
    def __init__(self,
                 redis_host: str = "localhost",
                 redis_port: int = 6379,
                 db_prefix: str = "org_access",
                 db: Optional[OrgAccessControlDB] = None):
        try:
            self.redis = redis.StrictRedis(
                host=redis_host, port=redis_port, decode_responses=True)
            self.db_prefix = db_prefix
            self.db = db
            logger.info("Initialized AccessCache module with Redis backend")
        except Exception as e:
            logger.exception("Failed to initialize Redis client")
            raise

    def _role_key(self, api_route: str) -> str:
        return f"{self.db_prefix}:role:{api_route}"

    def _constraint_key(self, api_route: str) -> str:
        return f"{self.db_prefix}:constraint:{api_route}"

    def get_role_association(self, api_route: str) -> Optional[Dict[str, Any]]:
        try:
            key = self._role_key(api_route)
            value = self.redis.get(key)
            if value:
                logger.debug(
                    f"Role association cache hit for route: {api_route}")
                return json.loads(value)
            logger.debug(f"Role association cache miss for route: {api_route}")
            return None
        except Exception as e:
            logger.exception("Error reading role association from cache")
            return None

    def set_role_association(self, association: APIRoleAssociation):
        try:
            key = self._role_key(association.api_route)
            self.redis.set(key, json.dumps(association.to_dict()))
            logger.info(
                f"Cached role association for route: {association.api_route}")
        except Exception as e:
            logger.exception("Failed to cache role association")

    def delete_role_association(self, api_route: str):
        try:
            self.redis.delete(self._role_key(api_route))
            logger.info(
                f"Deleted role association cache for route: {api_route}")
        except Exception as e:
            logger.exception("Failed to delete role association cache")

    def get_constraint_map(self, api_route: str) -> Optional[Dict[str, Any]]:
        try:
            key = self._constraint_key(api_route)
            value = self.redis.get(key)
            if value:
                logger.debug(f"Constraint cache hit for route: {api_route}")
                return json.loads(value)
            logger.debug(f"Constraint cache miss for route: {api_route}")
            return None
        except Exception as e:
            logger.exception("Error reading constraint map from cache")
            return None

    def set_constraint_map(self, constraint: APIConstraintMap):
        try:
            key = self._constraint_key(constraint.api_route)
            self.redis.set(key, json.dumps(constraint.to_dict()))
            logger.info(
                f"Cached constraint map for route: {constraint.api_route}")
        except Exception as e:
            logger.exception("Failed to cache constraint map")

    def delete_constraint_map(self, api_route: str):
        try:
            self.redis.delete(self._constraint_key(api_route))
            logger.info(f"Deleted constraint map cache for route: {api_route}")
        except Exception as e:
            logger.exception("Failed to delete constraint map cache")

    def flush_all_cache(self):
        try:
            keys = self.redis.keys(f"{self.db_prefix}:*")
            if keys:
                self.redis.delete(*keys)
                logger.info(f"Flushed {len(keys)} cache entries from Redis")
            else:
                logger.info("No cache keys found to flush")
        except Exception as e:
            logger.exception("Failed to flush Redis cache")

    def initialize_cache_from_db(self):
        if not self.db:
            logger.warning("DB instance not provided for cache initialization")
            return

        try:
            logger.info("Initializing cache from DB...")
            for assoc in self.db.list_all_role_associations():
                self.set_role_association(assoc)

            for constraint in self.db.list_all_constraints():
                self.set_constraint_map(constraint)

            logger.info("Cache initialized from DB successfully")
        except Exception as e:
            logger.exception("Failed to initialize cache from DB")


class CacheManager:
    def __init__(self, cache: AccessCache, db: Optional[OrgAccessControlDB] = None):
        self.cache = cache
        self.db = db or cache.db

    def flush_entire_cache(self):
        try:
            self.cache.flush_all_cache()
            logger.info("CacheManager: Entire cache flushed.")
            return True
        except Exception as e:
            logger.exception("CacheManager: Failed to flush entire cache.")
            return False

    def initialize_cache(self):
        try:
            self.cache.initialize_cache_from_db()
            logger.info("CacheManager: Cache initialized from DB.")
            return True
        except Exception as e:
            logger.exception("CacheManager: Failed to initialize cache from DB.")
            return False

    def refresh_cache_for_route(self, api_route: str) -> bool:
        if not self.db:
            logger.error("CacheManager: DB instance is required for refresh.")
            return False

        try:
            role_assoc = self.db.get_role_association(api_route)
            if role_assoc:
                self.cache.set_role_association(role_assoc)
                logger.info(f"CacheManager: Refreshed role association for {api_route}")
            else:
                logger.warning(f"CacheManager: No role association found for {api_route}")

            constraint = self.db.get_constraint(api_route)
            if constraint:
                self.cache.set_constraint_map(constraint)
                logger.info(f"CacheManager: Refreshed constraint map for {api_route}")
            else:
                logger.warning(f"CacheManager: No constraint map found for {api_route}")

            return True
        except Exception as e:
            logger.exception(f"CacheManager: Failed to refresh cache for route: {api_route}")
            return False

    def delete_cache_for_route(self, api_route: str) -> bool:
        try:
            self.cache.delete_role_association(api_route)
            self.cache.delete_constraint_map(api_route)
            logger.info(f"CacheManager: Deleted cache for route: {api_route}")
            return True
        except Exception as e:
            logger.exception(f"CacheManager: Failed to delete cache for route: {api_route}")
            return False