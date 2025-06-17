import os
import logging
from typing import Tuple, Union, List, Dict, Any
from pymongo import MongoClient, errors

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class BaseMongoDB:
    def __init__(self, collection_name: str):
        try:
            uri = os.getenv("MONGO_URL", "mongodb://localhost:27017")
            self.client = MongoClient(uri)
            self.db = self.client["orgs"]
            self.collection = self.db[collection_name]
            logger.info(f"Connected to MongoDB collection: {collection_name}")
        except errors.ConnectionFailure as e:
            logger.error(f"MongoDB connection error: {e}")
            raise

    def insert(self, obj) -> Tuple[bool, Union[str, None]]:
        try:
            result = self.collection.insert_one(obj.to_dict())
            return True, str(result.inserted_id)
        except errors.PyMongoError as e:
            logger.error(f"Insertion failed: {e}")
            return False, str(e)

    def get_by_id(self, key: str, value: str) -> Tuple[bool, Union[Dict[str, Any], str]]:
        try:
            doc = self.collection.find_one({key: value})
            return (True, doc) if doc else (False, "Not found")
        except errors.PyMongoError as e:
            return False, str(e)

    def query(self, filters: Dict[str, Any]) -> Tuple[bool, Union[List[Dict[str, Any]], str]]:
        try:
            return True, list(self.collection.find(filters))
        except errors.PyMongoError as e:
            return False, str(e)

    def update(self, key: str, value: str, update_fields: Dict[str, Any]) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.update_one({key: value}, {"$set": update_fields})
            return True, result.modified_count
        except errors.PyMongoError as e:
            return False, str(e)

    def delete(self, key: str, value: str) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.delete_one({key: value})
            return True, result.deleted_count
        except errors.PyMongoError as e:
            return False, str(e)

# Specific CRUD classes
class SubjectAssociationDatabase(BaseMongoDB):
    def __init__(self):
        super().__init__("subject_association")

class SubjectContractAssociationDatabase(BaseMongoDB):
    def __init__(self):
        super().__init__("subject_contract_association")

class SubjectMessageCommunicationDatabase(BaseMongoDB):
    def __init__(self):
        super().__init__("subject_message_communication")

class SubjectAssociationConfigDatabase(BaseMongoDB):
    def __init__(self):
        super().__init__("subject_association_config")
