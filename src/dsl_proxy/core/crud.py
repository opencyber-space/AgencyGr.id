import os
import logging
from pymongo import MongoClient, errors
from typing import Tuple, Union, List, Dict

from .schema import OrgDSLWorkflows 

logger = logging.getLogger(__name__)


class OrgDSLWorkflowsDatabase:
    def __init__(self):
        try:
            uri = os.getenv("MONGO_URL", "mongodb://localhost:27017")
            self.client = MongoClient(uri)
            self.db = self.client["orgs"]
            self.collection = self.db["org_dsl_workflows"]
            logger.info("MongoDB connection established for OrgDSLWorkflowsDatabase")
        except errors.ConnectionFailure as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise

    def insert(self, workflow: OrgDSLWorkflows) -> Tuple[bool, Union[str, None]]:
        try:
            document = workflow.to_dict()
            result = self.collection.insert_one(document)
            logger.info(f"Workflow inserted with workflow_id: {workflow.workflow_id}")
            return True, str(result.inserted_id)
        except errors.PyMongoError as e:
            logger.error(f"Error inserting workflow: {e}")
            return False, str(e)

    def update(self, workflow_id: str, update_fields: Dict) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.update_one(
                {"workflow_id": workflow_id},
                {"$set": update_fields},
                upsert=True
            )
            if result.modified_count > 0:
                logger.info(f"Workflow with workflow_id {workflow_id} updated")
                return True, result.modified_count
            else:
                logger.info(f"No document found with workflow_id {workflow_id} to update")
                return False, "No document found to update"
        except errors.PyMongoError as e:
            logger.error(f"Error updating workflow: {e}")
            return False, str(e)

    def delete(self, workflow_id: str) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.delete_one({"workflow_id": workflow_id})
            if result.deleted_count > 0:
                logger.info(f"Workflow with workflow_id {workflow_id} deleted")
                return True, result.deleted_count
            else:
                logger.info(f"No document found with workflow_id {workflow_id} to delete")
                return False, "No document found to delete"
        except errors.PyMongoError as e:
            logger.error(f"Error deleting workflow: {e}")
            return False, str(e)

    def query(self, query_filter: Dict) -> Tuple[bool, Union[List[Dict], str]]:
        try:
            result = self.collection.find(query_filter)
            documents = []
            for doc in result:
                doc.pop('_id', None)
                documents.append(doc)
            logger.info(f"Query successful, found {len(documents)} documents")
            return True, documents
        except errors.PyMongoError as e:
            logger.error(f"Error querying workflows: {e}")
            return False, str(e)

    def get_by_workflow_id(self, workflow_id: str) -> Tuple[bool, Union[OrgDSLWorkflows, str]]:
        try:
            doc = self.collection.find_one({"workflow_id": workflow_id})
            if doc:
                doc.pop('_id', None)
                workflow = OrgDSLWorkflows.from_dict(doc)
                logger.info(f"Workflow with workflow_id {workflow_id} retrieved")
                return True, workflow
            else:
                logger.info(f"No workflow found with workflow_id {workflow_id}")
                return False, "No document found"
        except errors.PyMongoError as e:
            logger.error(f"Error retrieving workflow: {e}")
            return False, str(e)
