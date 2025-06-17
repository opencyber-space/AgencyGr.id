import requests
import logging
import os

from typing import Tuple

from .schema import OrgDSLWorkflows
from .crud import OrgDSLWorkflowsDatabase
from .dsl import DSLDBClient


logger = logging.getLogger(__name__)

class DSLDBClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def get_dsl_by_id(self, workflow_id: str) -> dict:
        url = f"{self.base_url}/workflows/{workflow_id}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()["data"]
            elif response.status_code == 404:
                raise Exception(f"Workflow '{workflow_id}' not found.")
            else:
                raise Exception(f"Error {response.status_code}: {response.text}")
        except requests.RequestException as e:
            logger.error(f"Request to {url} failed: {e}")
            raise Exception(f"Request failed: {str(e)}")



def register_dsl_entry(dsl_id: str) -> Tuple[bool, str]:
    try:
        dsl_client = DSLDBClient(base_url=os.getenv("DSL_DB_SERVER", "http://localhost:8000"))
        dsl_data = dsl_client.get_dsl_by_id(dsl_id)

        workflow = OrgDSLWorkflows(
            workflow_id=dsl_data.get("workflow_id", ""),
            workflow_search_tags=dsl_data.get("tags", []),
            workflow_metadata={
                "name": dsl_data.get("name", ""),
                "version": dsl_data.get("version", {}),
                "graph": dsl_data.get("graph", {}),
                "modules": dsl_data.get("modules", {}),
            },
            workflow_description=dsl_data.get("description", ""),
            workflow_default_params={
                "globalSettings": dsl_data.get("globalSettings", {}),
                "globalParameters": dsl_data.get("globalParameters", {})
            }
        )

        db = OrgDSLWorkflowsDatabase()
        success, result = db.insert(workflow)

        if success:
            logger.info(f"Successfully registered DSL entry {dsl_id}")
            return True, f"Inserted DSL workflow with id: {result}"
        else:
            logger.warning(f"Failed to insert DSL entry {dsl_id}: {result}")
            return False, result

    except Exception as e:
        logger.error(f"register_dsl_entry error for {dsl_id}: {e}")
        return False, str(e)

