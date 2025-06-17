import logging
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from typing import Optional, List

from .schema import APIRoleAssociation, APIConstraintMap

logger = logging.getLogger("DBAPI")
logging.basicConfig(level=logging.INFO)


class OrgAccessControlDB:
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017", db_name: str = "org_access_control_db"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.roles_collection: Collection = self.db["api_role_association_table"]
        self.constraints_collection: Collection = self.db["api_constraints_map"]


    def create_role_association(self, association: APIRoleAssociation) -> str:
        try:
            doc = association.to_dict()
            self.roles_collection.insert_one(doc)
            logger.info(f"Inserted role association for route: {association.api_route}")
            return association.api_route
        except PyMongoError as e:
            logger.error(f"Failed to insert role association: {e}")
            raise

    def get_role_association(self, api_route: str) -> Optional[APIRoleAssociation]:
        try:
            doc = self.roles_collection.find_one({"api_route": api_route})
            return APIRoleAssociation.from_dict(doc) if doc else None
        except PyMongoError as e:
            logger.error(f"Failed to fetch role association: {e}")
            raise

    def update_role_association(self, api_route: str, updated: dict) -> bool:
        try:
            result = self.roles_collection.update_one({"api_route": api_route}, {"$set": updated})
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Failed to update role association: {e}")
            raise

    def delete_role_association(self, api_route: str) -> bool:
        try:
            result = self.roles_collection.delete_one({"api_route": api_route})
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Failed to delete role association: {e}")
            raise

    def list_all_role_associations(self) -> List[APIRoleAssociation]:
        try:
            return [APIRoleAssociation.from_dict(doc) for doc in self.roles_collection.find()]
        except PyMongoError as e:
            logger.error(f"Failed to list role associations: {e}")
            raise

    def create_constraint(self, constraint: APIConstraintMap) -> str:
        try:
            doc = constraint.to_dict()
            self.constraints_collection.insert_one(doc)
            logger.info(f"Inserted constraint map for route: {constraint.api_route}")
            return constraint.api_route
        except PyMongoError as e:
            logger.error(f"Failed to insert constraint map: {e}")
            raise

    def get_constraint(self, api_route: str) -> Optional[APIConstraintMap]:
        try:
            doc = self.constraints_collection.find_one({"api_route": api_route})
            return APIConstraintMap.from_dict(doc) if doc else None
        except PyMongoError as e:
            logger.error(f"Failed to fetch constraint map: {e}")
            raise

    def update_constraint(self, api_route: str, updated: dict) -> bool:
        try:
            result = self.constraints_collection.update_one({"api_route": api_route}, {"$set": updated})
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Failed to update constraint map: {e}")
            raise

    def delete_constraint(self, api_route: str) -> bool:
        try:
            result = self.constraints_collection.delete_one({"api_route": api_route})
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Failed to delete constraint map: {e}")
            raise

    def list_all_constraints(self) -> List[APIConstraintMap]:
        try:
            return [APIConstraintMap.from_dict(doc) for doc in self.constraints_collection.find()]
        except PyMongoError as e:
            logger.error(f"Failed to list constraint maps: {e}")
            raise
