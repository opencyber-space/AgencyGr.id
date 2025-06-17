import os
import logging
from typing import Tuple, Union, List, Dict
from pymongo import MongoClient, errors
import logging

from .schema import (
    SubjectRolesMapping,
    RoleGroupMapping,
    RoleTypeAssignmentMapping,
    GroupConstraintsMapping,
    RoleApplication
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SubjectRolesMappingDatabase:
    def __init__(self):
        try:
            uri = os.getenv("MONGO_URL", "mongodb://localhost:27017")
            self.client = MongoClient(uri)
            self.db = self.client["orgs"]
            self.collection = self.db["subject_roles_mapping"]
            logger.info("MongoDB connection established for SubjectRolesMappingDatabase")
        except errors.ConnectionFailure as e:
            logger.error(f"Mongo connection failed: {e}")
            raise

    def insert(self, obj: SubjectRolesMapping) -> Tuple[bool, Union[str, None]]:
        try:
            result = self.collection.insert_one(obj.to_dict())
            return True, str(result.inserted_id)
        except errors.PyMongoError as e:
            logger.error(f"Insertion error: {e}")
            return False, str(e)

    def update(self, subject_id: str, update_fields: Dict) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.update_one(
                {"subject_id": subject_id},
                {"$set": update_fields},
                upsert=True
            )
            return (True, result.modified_count) if result.modified_count else (False, "No document found to update")
        except errors.PyMongoError as e:
            return False, str(e)

    def delete(self, subject_id: str) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.delete_one({"subject_id": subject_id})
            return (True, result.deleted_count) if result.deleted_count else (False, "No document found to delete")
        except errors.PyMongoError as e:
            return False, str(e)

    def query(self, query_filter: Dict) -> Tuple[bool, Union[List[Dict], str]]:
        try:
            docs = list(self.collection.find(query_filter))
            for d in docs:
                d.pop("_id", None)
            return True, docs
        except errors.PyMongoError as e:
            return False, str(e)

    def get_by_subject_id(self, subject_id: str) -> Tuple[bool, Union[SubjectRolesMapping, str]]:
        try:
            doc = self.collection.find_one({"subject_id": subject_id})
            if doc:
                doc.pop("_id", None)
                return True, SubjectRolesMapping.from_dict(doc)
            return False, "No document found"
        except errors.PyMongoError as e:
            return False, str(e)


class RoleGroupMappingDatabase:
    def __init__(self):
        uri = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        self.client = MongoClient(uri)
        self.db = self.client["orgs"]
        self.collection = self.db["role_group_mapping"]
        logger.info("MongoDB connected for RoleGroupMappingDatabase")

    def insert(self, obj: RoleGroupMapping) -> Tuple[bool, Union[str, None]]:
        try:
            result = self.collection.insert_one(obj.to_dict())
            return True, str(result.inserted_id)
        except errors.PyMongoError as e:
            return False, str(e)

    def update(self, role_id: str, update_fields: Dict) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.update_one({"role_id": role_id}, {"$set": update_fields}, upsert=True)
            return (True, result.modified_count) if result.modified_count else (False, "No document found to update")
        except errors.PyMongoError as e:
            return False, str(e)

    def delete(self, role_id: str) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.delete_one({"role_id": role_id})
            return (True, result.deleted_count) if result.deleted_count else (False, "No document found to delete")
        except errors.PyMongoError as e:
            return False, str(e)

    def query(self, query_filter: Dict) -> Tuple[bool, Union[List[Dict], str]]:
        try:
            docs = list(self.collection.find(query_filter))
            for d in docs:
                d.pop("_id", None)
            return True, docs
        except errors.PyMongoError as e:
            return False, str(e)

    def get_by_role_id(self, role_id: str) -> Tuple[bool, Union[RoleGroupMapping, str]]:
        try:
            doc = self.collection.find_one({"role_id": role_id})
            if doc:
                doc.pop("_id", None)
                return True, RoleGroupMapping.from_dict(doc)
            return False, "No document found"
        except errors.PyMongoError as e:
            return False, str(e)


class RoleTypeAssignmentMappingDatabase:
    def __init__(self):
        uri = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        self.client = MongoClient(uri)
        self.db = self.client["orgs"]
        self.collection = self.db["role_type_assignment_mapping"]
        logger.info("MongoDB connected for RoleTypeAssignmentMappingDatabase")

    def insert(self, obj: RoleTypeAssignmentMapping) -> Tuple[bool, Union[str, None]]:
        try:
            result = self.collection.insert_one(obj.to_dict())
            return True, str(result.inserted_id)
        except errors.PyMongoError as e:
            return False, str(e)

    def update(self, role_type: str, update_fields: Dict) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.update_one({"role_type": role_type}, {"$set": update_fields}, upsert=True)
            return (True, result.modified_count) if result.modified_count else (False, "No document found to update")
        except errors.PyMongoError as e:
            return False, str(e)

    def delete(self, role_type: str) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.delete_one({"role_type": role_type})
            return (True, result.deleted_count) if result.deleted_count else (False, "No document found to delete")
        except errors.PyMongoError as e:
            return False, str(e)

    def query(self, query_filter: Dict) -> Tuple[bool, Union[List[Dict], str]]:
        try:
            docs = list(self.collection.find(query_filter))
            for d in docs:
                d.pop("_id", None)
            return True, docs
        except errors.PyMongoError as e:
            return False, str(e)

    def get_by_role_type(self, role_type: str) -> Tuple[bool, Union[RoleTypeAssignmentMapping, str]]:
        try:
            doc = self.collection.find_one({"role_type": role_type})
            if doc:
                doc.pop("_id", None)
                return True, RoleTypeAssignmentMapping.from_dict(doc)
            return False, "No document found"
        except errors.PyMongoError as e:
            return False, str(e)

class GroupConstraintsMappingDatabase:
    def __init__(self):
        uri = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        self.client = MongoClient(uri)
        self.db = self.client["orgs"]
        self.collection = self.db["group_constraints_mapping"]
        logger.info("MongoDB connected for GroupConstraintsMappingDatabase")

    def insert(self, obj: GroupConstraintsMapping) -> Tuple[bool, Union[str, None]]:
        try:
            result = self.collection.insert_one(obj.to_dict())
            return True, str(result.inserted_id)
        except errors.PyMongoError as e:
            return False, str(e)

    def update(self, group_id: str, update_fields: Dict) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.update_one({"group_id": group_id}, {"$set": update_fields}, upsert=True)
            return (True, result.modified_count) if result.modified_count else (False, "No document found to update")
        except errors.PyMongoError as e:
            return False, str(e)

    def delete(self, group_id: str) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.delete_one({"group_id": group_id})
            return (True, result.deleted_count) if result.deleted_count else (False, "No document found to delete")
        except errors.PyMongoError as e:
            return False, str(e)

    def query(self, query_filter: Dict) -> Tuple[bool, Union[List[Dict], str]]:
        try:
            docs = list(self.collection.find(query_filter))
            for d in docs:
                d.pop("_id", None)
            return True, docs
        except errors.PyMongoError as e:
            return False, str(e)

    def get_by_group_id(self, group_id: str) -> Tuple[bool, Union[GroupConstraintsMapping, str]]:
        try:
            doc = self.collection.find_one({"group_id": group_id})
            if doc:
                doc.pop("_id", None)
                return True, GroupConstraintsMapping.from_dict(doc)
            return False, "No document found"
        except errors.PyMongoError as e:
            return False, str(e)


class RoleApplicationDatabase:
    def __init__(self):
        try:
            uri = os.getenv("MONGO_URL", "mongodb://localhost:27017")
            self.client = MongoClient(uri)
            self.db = self.client["orgs"]
            self.collection = self.db["role_applications"]
            logger.info("MongoDB connection established for RoleApplicationDatabase")
        except errors.ConnectionFailure as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise

    def insert(self, app: RoleApplication) -> Tuple[bool, Union[str, None]]:
        try:
            document = app.to_dict()
            result = self.collection.insert_one(document)
            logger.info(f"RoleApplication inserted with ID: {app.role_application_id}")
            return True, str(result.inserted_id)
        except errors.PyMongoError as e:
            logger.error(f"Error inserting RoleApplication: {e}")
            return False, str(e)

    def update(self, role_application_id: str, update_fields: Dict) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.update_one(
                {"role_application_id": role_application_id},
                {"$set": update_fields},
                upsert=True
            )
            if result.modified_count > 0:
                logger.info(f"Updated RoleApplication with ID {role_application_id}")
                return True, result.modified_count
            else:
                return False, "No document found to update"
        except errors.PyMongoError as e:
            logger.error(f"Error updating RoleApplication: {e}")
            return False, str(e)

    def delete(self, role_application_id: str) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.delete_one({"role_application_id": role_application_id})
            if result.deleted_count > 0:
                logger.info(f"Deleted RoleApplication with ID {role_application_id}")
                return True, result.deleted_count
            else:
                return False, "No document found to delete"
        except errors.PyMongoError as e:
            logger.error(f"Error deleting RoleApplication: {e}")
            return False, str(e)

    def query(self, query_filter: Dict) -> Tuple[bool, Union[List[Dict], str]]:
        try:
            result = self.collection.find(query_filter)
            documents = []
            for doc in result:
                doc.pop("_id", None)
                documents.append(doc)
            logger.info(f"Query returned {len(documents)} RoleApplications")
            return True, documents
        except errors.PyMongoError as e:
            logger.error(f"Error querying RoleApplication: {e}")
            return False, str(e)

    def get_by_id(self, role_application_id: str) -> Tuple[bool, Union[RoleApplication, str]]:
        try:
            doc = self.collection.find_one({"role_application_id": role_application_id})
            if doc:
                doc.pop("_id", None)
                return True, RoleApplication.from_dict(doc)
            return False, "No document found"
        except errors.PyMongoError as e:
            logger.error(f"Error retrieving RoleApplication: {e}")
            return False, str(e)
