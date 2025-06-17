from pymongo import MongoClient, errors
import os, logging
from typing import Tuple, Union, List, Dict
from .schema import OrgConstraints

logger = logging.getLogger(__name__)

class OrgConstraintsDatabase:
    def __init__(self):
        uri = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        self.client = MongoClient(uri)
        self.db = self.client["orgs"]
        self.collection = self.db["org_constraints"]

    def insert(self, constraint: OrgConstraints) -> Tuple[bool, Union[str, None]]:
        try:
            result = self.collection.insert_one(constraint.to_dict())
            return True, str(result.inserted_id)
        except errors.PyMongoError as e:
            logger.error(f"Insert error: {e}")
            return False, str(e)

    def get_by_message_type(self, message_type: str) -> Tuple[bool, Union[OrgConstraints, str]]:
        try:
            doc = self.collection.find_one({"message_type": message_type})
            if doc:
                doc.pop('_id', None)
                return True, OrgConstraints.from_dict(doc)
            return False, "Not found"
        except errors.PyMongoError as e:
            logger.error(f"Get error: {e}")
            return False, str(e)

    def update(self, message_type: str, updates: Dict) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.update_one(
                {"message_type": message_type}, {"$set": updates}, upsert=False
            )
            if result.modified_count > 0:
                return True, result.modified_count
            return False, "No document modified"
        except errors.PyMongoError as e:
            return False, str(e)

    def delete(self, message_type: str) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.delete_one({"message_type": message_type})
            if result.deleted_count > 0:
                return True, result.deleted_count
            return False, "Not found"
        except errors.PyMongoError as e:
            return False, str(e)

    def query(self, filters: Dict) -> Tuple[bool, Union[List[Dict], str]]:
        try:
            cursor = self.collection.find(filters)
            results = []
            for doc in cursor:
                doc.pop('_id', None)
                results.append(doc)
            return True, results
        except errors.PyMongoError as e:
            return False, str(e)
