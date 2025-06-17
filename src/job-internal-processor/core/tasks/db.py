import logging
from pymongo import MongoClient, errors
import os

from typing import Dict, Any, Tuple, List, Union

from .schema import *

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class BaseMongoDB:
    def __init__(self, collection_name: str):
        try:
            uri = os.getenv("MONGO_URL", "mongodb://localhost:27017")
            self.client = MongoClient(uri)
            self.db = self.client["tasks"]
            self.collection = self.db[collection_name]
            logger.info(f"MongoDB connected for collection: {collection_name}")
        except errors.ConnectionFailure as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise

    def insert(self, obj) -> Tuple[bool, Union[str, None]]:
        try:
            result = self.collection.insert_one(obj.to_dict())
            return True, str(result.inserted_id)
        except errors.PyMongoError as e:
            return False, str(e)

    def update(self, id_field: str, id_value: str, update_fields: Dict) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.update_one(
                {id_field: id_value}, {"$set": update_fields}, upsert=True
            )
            return (True, result.modified_count) if result.modified_count > 0 else (False, "No document found to update")
        except errors.PyMongoError as e:
            return False, str(e)

    def delete(self, id_field: str, id_value: str) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.delete_one({id_field: id_value})
            return (True, result.deleted_count) if result.deleted_count > 0 else (False, "No document found to delete")
        except errors.PyMongoError as e:
            return False, str(e)

    def query(self, query_filter: Dict) -> Tuple[bool, Union[List[Dict], str]]:
        try:
            result = self.collection.find(query_filter)
            docs = [{k: v for k, v in doc.items() if k != '_id'}
                    for doc in result]
            return True, docs
        except errors.PyMongoError as e:
            return False, str(e)

    def get_by_id(self, id_field: str, id_value: str, cls) -> Tuple[bool, Union[Any, str]]:
        try:
            doc = self.collection.find_one({id_field: id_value})
            if doc:
                doc.pop('_id', None)
                return True, cls.from_dict(doc)
            return False, "No document found"
        except errors.PyMongoError as e:
            return False, str(e)


class TaskEntryDatabase(BaseMongoDB):
    def __init__(self): super().__init__("task_entries")
    def get_by_task_id(self, task_id): return self.get_by_id(
        "task_id", task_id, TaskEntry)


class SubTaskEntryDatabase(BaseMongoDB):
    def __init__(self): super().__init__("sub_task_entries")

    def get_by_sub_task_id(self, sub_task_id): return self.get_by_id(
        "sub_task_id", sub_task_id, SubTaskEntry)
