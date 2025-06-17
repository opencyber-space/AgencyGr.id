from dataclasses import dataclass, field
from typing import List, Dict,  Optional
import logging

from pymongo import MongoClient, ReturnDocument
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)


@dataclass
class JobSpaceContractsMapping:
    task_id: str
    sub_task_id: str = ''
    contract_ids: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.task_id}::{self.sub_task_id}" if self.sub_task_id else self.task_id

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "sub_task_id": self.sub_task_id,
            "key": self.key,
            "contract_ids": self.contract_ids,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'JobSpaceContractsMapping':
        return cls(
            task_id=data.get("task_id", ""),
            sub_task_id=data.get("sub_task_id", ""),
            contract_ids=data.get("contract_ids", []),
            metadata=data.get("metadata", {})
        )


class JobSpaceContractsMappingDB:
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017", db_name: str = "contracts_db"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection: Collection = self.db["jobspace_contracts_mappings"]

    def create(self, mapping: JobSpaceContractsMapping) -> str:
        try:
            doc = mapping.to_dict()
            doc["_id"] = mapping.key
            self.collection.insert_one(doc)
            logger.info(f"Inserted mapping with key: {mapping.key}")
            return mapping.key
        except PyMongoError as e:
            logger.error(f"Failed to insert mapping: {e}")
            raise

    def get(self, key: str) -> Optional[JobSpaceContractsMapping]:
        try:
            doc = self.collection.find_one({"_id": key})
            if doc:
                return JobSpaceContractsMapping.from_dict(doc)
            return None
        except PyMongoError as e:
            logger.error(f"Failed to fetch mapping with key {key}: {e}")
            raise

    def update(self, mapping: JobSpaceContractsMapping) -> Optional[JobSpaceContractsMapping]:
        try:
            doc = mapping.to_dict()
            doc["_id"] = mapping.key
            updated = self.collection.find_one_and_replace(
                {"_id": mapping.key},
                doc,
                return_document=ReturnDocument.AFTER,
                upsert=True
            )
            logger.info(f"Updated mapping with key: {mapping.key}")
            return JobSpaceContractsMapping.from_dict(updated)
        except PyMongoError as e:
            logger.error(
                f"Failed to update mapping with key {mapping.key}: {e}")
            raise

    def delete(self, key: str) -> bool:
        try:
            result = self.collection.delete_one({"_id": key})
            if result.deleted_count:
                logger.info(f"Deleted mapping with key: {key}")
                return True
            logger.warning(f"No mapping found with key: {key}")
            return False
        except PyMongoError as e:
            logger.error(f"Failed to delete mapping with key {key}: {e}")
            raise

    def list_all(self) -> List[JobSpaceContractsMapping]:
        try:
            docs = self.collection.find()
            return [JobSpaceContractsMapping.from_dict(doc) for doc in docs]
        except PyMongoError as e:
            logger.error(f"Failed to list mappings: {e}")
            raise


