import os
import logging
from typing import Dict, Tuple, Union, List
from pymongo import MongoClient, errors
from dataclasses import asdict
from .schema import OrgCreationTask, OrgCreationStage



logger = logging.getLogger(__name__)


class OrgCreationTaskDatabase:
    def __init__(self):
        try:
            uri = os.getenv("MONGO_URL", "mongodb://localhost:27017")
            self.client = MongoClient(uri)
            self.db = self.client["orgs"]
            self.collection = self.db["org_creation_tasks"]
            logger.info("MongoDB connection established for OrgCreationTaskDatabase")
        except errors.ConnectionFailure as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise

    def insert(self, task: OrgCreationTask) -> Tuple[bool, Union[str, None]]:
        try:
            document = task.to_dict()
            result = self.collection.insert_one(document)
            logger.info(f"Task inserted with task_id: {task.org_creation_task_id}")
            return True, str(result.inserted_id)
        except errors.PyMongoError as e:
            logger.error(f"Error inserting task: {e}")
            return False, str(e)

    def update(self, task_id: str, update_fields: Dict) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.update_one(
                {"org_creation_task_id": task_id},
                {"$set": update_fields},
                upsert=True
            )
            if result.modified_count > 0:
                logger.info(f"Task with ID {task_id} updated")
                return True, result.modified_count
            else:
                return False, "No document found to update"
        except errors.PyMongoError as e:
            logger.error(f"Error updating task: {e}")
            return False, str(e)

    def delete(self, task_id: str) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.delete_one({"org_creation_task_id": task_id})
            if result.deleted_count > 0:
                logger.info(f"Task with ID {task_id} deleted")
                return True, result.deleted_count
            else:
                return False, "No document found to delete"
        except errors.PyMongoError as e:
            logger.error(f"Error deleting task: {e}")
            return False, str(e)

    def query(self, query_filter: Dict) -> Tuple[bool, Union[List[Dict], str]]:
        try:
            documents = list(self.collection.find(query_filter))
            for doc in documents:
                doc.pop('_id', None)
            return True, documents
        except errors.PyMongoError as e:
            logger.error(f"Error querying tasks: {e}")
            return False, str(e)

    def get_by_id(self, task_id: str) -> Tuple[bool, Union[OrgCreationTask, str]]:
        try:
            doc = self.collection.find_one({"org_creation_task_id": task_id})
            if doc:
                doc.pop('_id', None)
                return True, OrgCreationTask.from_dict(doc)
            else:
                return False, "No document found"
        except errors.PyMongoError as e:
            logger.error(f"Error retrieving task: {e}")
            return False, str(e)


class OrgCreationStageDatabase:
    def __init__(self):
        try:
            uri = os.getenv("MONGO_URL", "mongodb://localhost:27017")
            self.client = MongoClient(uri)
            self.db = self.client["orgs"]
            self.collection = self.db["org_creation_stages"]
            logger.info("MongoDB connection established for OrgCreationStageDatabase")
        except errors.ConnectionFailure as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise

    def insert(self, stage: OrgCreationStage) -> Tuple[bool, Union[str, None]]:
        try:
            document = stage.to_dict()
            result = self.collection.insert_one(document)
            logger.info(f"Stage inserted with stage_id: {stage.stage_id}")
            return True, str(result.inserted_id)
        except errors.PyMongoError as e:
            logger.error(f"Error inserting stage: {e}")
            return False, str(e)

    def update(self, stage_id: str, update_fields: Dict) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.update_one(
                {"stage_id": stage_id},
                {"$set": update_fields},
                upsert=True
            )
            if result.modified_count > 0:
                logger.info(f"Stage with ID {stage_id} updated")
                return True, result.modified_count
            else:
                return False, "No document found to update"
        except errors.PyMongoError as e:
            logger.error(f"Error updating stage: {e}")
            return False, str(e)

    def delete(self, stage_id: str) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.delete_one({"stage_id": stage_id})
            if result.deleted_count > 0:
                logger.info(f"Stage with ID {stage_id} deleted")
                return True, result.deleted_count
            else:
                return False, "No document found to delete"
        except errors.PyMongoError as e:
            logger.error(f"Error deleting stage: {e}")
            return False, str(e)

    def query(self, query_filter: Dict) -> Tuple[bool, Union[List[Dict], str]]:
        try:
            documents = list(self.collection.find(query_filter))
            for doc in documents:
                doc.pop('_id', None)
            return True, documents
        except errors.PyMongoError as e:
            logger.error(f"Error querying stages: {e}")
            return False, str(e)

    def get_by_id(self, stage_id: str) -> Tuple[bool, Union[OrgCreationStage, str]]:
        try:
            doc = self.collection.find_one({"stage_id": stage_id})
            if doc:
                doc.pop('_id', None)
                return True, OrgCreationStage.from_dict(doc)
            else:
                return False, "No document found"
        except errors.PyMongoError as e:
            logger.error(f"Error retrieving stage: {e}")
            return False, str(e)