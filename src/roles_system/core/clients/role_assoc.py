import os
import requests
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class SubjectAssociationClient:
    def __init__(self, subject_id: str, subject_data: Dict, role_data: Dict):
        
        self.subject_id = subject_id
        self.subject_data = subject_data
        self.role_data = role_data
        self.base_url = os.getenv("ORG_ASSOCIATION_SYSTEM_URL", "http://localhost:8080")
        self.endpoint = f"{self.base_url}/associations/create-for-role"

    def create_association(self) -> Optional[Dict]:
       
        payload = {
            "subject_id": self.subject_id,
            "subject_data": self.subject_data,
            "role_data": self.role_data
        }

        try:
            logger.info(f"Calling Subject Association API at {self.endpoint} with payload: {payload}")
            response = requests.post(self.endpoint, json=payload, timeout=10)
            response.raise_for_status()

            json_response = response.json()
            if json_response.get("success"):
                return json_response.get("data")
            else:
                logger.warning(f"Association failed: {json_response.get('message')}")
                return None

        except requests.RequestException as e:
            logger.error(f"Error while calling Subject Association API: {e}")
            return None
