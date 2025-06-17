import logging
from typing import Any, Dict, Optional

from .cache import AccessCache
from .mgmt_db import OrgAccessControlDB
from .schema import APIConstraintMap
from constraints_checker import ConstraintsManager 

logger = logging.getLogger("RevProxyConstraintsChecker")
logging.basicConfig(level=logging.INFO)


class RevProxyConstraintsChecker:
    def __init__(self, cache: AccessCache, db: Optional[OrgAccessControlDB] = None):
        self.cache = cache
        self.db = db or cache.db
        self.manager = ConstraintsManager()

    def _fetch_constraint_map(self, api_route: str) -> Optional[APIConstraintMap]:
        cached = self.cache.get_constraint_map(api_route)
        if cached:
            logger.debug(f"Constraint map for route '{api_route}' found in cache")
            return APIConstraintMap.from_dict(cached)

        # Fallback to DB
        try:
            constraint_map = self.db.get_constraint(api_route)
            if constraint_map:
                self.cache.set_constraint_map(constraint_map)
                logger.info(f"Constraint map for route '{api_route}' loaded from DB and cached")
                return constraint_map
            else:
                logger.warning(f"No constraint map found for route '{api_route}'")
                return None
        except Exception as e:
            logger.exception(f"Error fetching constraint map for route '{api_route}'")
            return None

    def validate_request(
        self,
        api_route: str,
        input_data: Any,
        subject_id: str
    ) -> Any:
        
        try:
            constraint_map = self._fetch_constraint_map(api_route)
            if not constraint_map:
                logger.info(f"No constraints to apply for route '{api_route}' — allowing request")
                return input_data  # no constraint = pass through

            message_type = constraint_map.constraints_map.get("message_type")
            dsl_workflow_id = constraint_map.constraints_map.get("dsl_workflow_id")

            if not message_type or not dsl_workflow_id:
                logger.warning(f"Incomplete constraint map for route '{api_route}' — skipping constraint check")
                return input_data

            if message_type not in self.manager._constraints:
                self.manager.load(message_type, subject_id, dsl_workflow_id)

            output = self.manager.check_constraint_and_convert_packet(
                message_type=message_type,
                input_data=input_data,
                subject_id=subject_id,
                dsl_workflow_id=dsl_workflow_id
            )
            logger.info(f"Constraint check passed for route '{api_route}'")
            return output

        except Exception as e:
            logger.error(f"Constraint check failed for route '{api_route}': {e}")
            raise
