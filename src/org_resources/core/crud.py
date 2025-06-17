import os
import logging
from typing import Tuple, Union, Dict, List
from pymongo import MongoClient, errors
from .schema import OrgResourceQuota  

logger = logging.getLogger(__name__)


class OrgResourceQuotaDatabase:
    def __init__(self):
        try:
            uri = os.getenv("MONGO_URL", "mongodb://localhost:27017")
            self.client = MongoClient(uri)
            self.db = self.client["orgs"]
            self.collection = self.db["org_resource_quotas"]
            logger.info("MongoDB connection established for OrgResourceQuotaDatabase")
        except errors.ConnectionFailure as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise

    def insert(self, quota: OrgResourceQuota) -> Tuple[bool, Union[str, None]]:
        try:
            document = quota.to_dict()
            result = self.collection.insert_one(document)
            logger.info(f"Quota inserted with quota_id: {quota.quota_id}")
            return True, str(result.inserted_id)
        except errors.PyMongoError as e:
            logger.error(f"Error inserting quota: {e}")
            return False, str(e)

    def update(self, quota_id: str, update_fields: Dict) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.update_one(
                {"quota_id": quota_id},
                {"$set": update_fields},
                upsert=True
            )
            if result.modified_count > 0:
                logger.info(f"Quota with quota_id {quota_id} updated")
                return True, result.modified_count
            else:
                logger.info(f"No document found with quota_id {quota_id} to update")
                return False, "No document found to update"
        except errors.PyMongoError as e:
            logger.error(f"Error updating quota: {e}")
            return False, str(e)

    def delete(self, quota_id: str) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.delete_one({"quota_id": quota_id})
            if result.deleted_count > 0:
                logger.info(f"Quota with quota_id {quota_id} deleted")
                return True, result.deleted_count
            else:
                logger.info(f"No document found with quota_id {quota_id} to delete")
                return False, "No document found to delete"
        except errors.PyMongoError as e:
            logger.error(f"Error deleting quota: {e}")
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
            logger.error(f"Error querying quotas: {e}")
            return False, str(e)

    def get_by_quota_id(self, quota_id: str) -> Tuple[bool, Union[OrgResourceQuota, str]]:
        try:
            doc = self.collection.find_one({"quota_id": quota_id})
            if doc:
                doc.pop('_id', None)
                quota = OrgResourceQuota.from_dict(doc)
                logger.info(f"Quota with quota_id {quota_id} retrieved")
                return True, quota
            else:
                logger.info(f"No quota found with quota_id {quota_id}")
                return False, "No document found"
        except errors.PyMongoError as e:
            logger.error(f"Error retrieving quota: {e}")
            return False, str(e)
