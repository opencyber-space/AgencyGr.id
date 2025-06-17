import os
import logging
from typing import Tuple, Union, List, Dict
from pymongo import MongoClient, errors
from .schema import OrgFunctions, OrgTools

logger = logging.getLogger(__name__)

class OrgFunctionsDatabase:
    def __init__(self):
        try:
            uri = os.getenv("MONGO_URL", "mongodb://localhost:27017")
            self.client = MongoClient(uri)
            self.db = self.client["orgs"]
            self.collection = self.db["org_functions"]
            logger.info("MongoDB connection established for OrgFunctionsDatabase")
        except errors.ConnectionFailure as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise

    def insert(self, function: OrgFunctions) -> Tuple[bool, Union[str, None]]:
        try:
            document = function.to_dict()
            result = self.collection.insert_one(document)
            logger.info(f"Function inserted with function_id: {function.function_id}")
            return True, str(result.inserted_id)
        except errors.PyMongoError as e:
            logger.error(f"Error inserting function: {e}")
            return False, str(e)

    def update(self, function_id: str, update_fields: Dict) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.update_one(
                {"function_id": function_id},
                {"$set": update_fields},
                upsert=True
            )
            if result.modified_count > 0:
                logger.info(f"Function with function_id {function_id} updated")
                return True, result.modified_count
            else:
                logger.info(f"No document found with function_id {function_id} to update")
                return False, "No document found to update"
        except errors.PyMongoError as e:
            logger.error(f"Error updating function: {e}")
            return False, str(e)

    def delete(self, function_id: str) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.delete_one({"function_id": function_id})
            if result.deleted_count > 0:
                logger.info(f"Function with function_id {function_id} deleted")
                return True, result.deleted_count
            else:
                logger.info(f"No document found with function_id {function_id} to delete")
                return False, "No document found to delete"
        except errors.PyMongoError as e:
            logger.error(f"Error deleting function: {e}")
            return False, str(e)

    def query(self, query_filter: Dict) -> Tuple[bool, Union[List[Dict], str]]:
        try:
            result = self.collection.find(query_filter)
            documents = []
            for doc in result:
                doc.pop('_id', None)
                documents.append(doc)
            logger.info(f"Query successful, found {len(documents)} functions")
            return True, documents
        except errors.PyMongoError as e:
            logger.error(f"Error querying functions: {e}")
            return False, str(e)

    def get_by_function_id(self, function_id: str) -> Tuple[bool, Union[OrgFunctions, str]]:
        try:
            doc = self.collection.find_one({"function_id": function_id})
            if doc:
                doc.pop('_id', None)
                function = OrgFunctions.from_dict(doc)
                logger.info(f"Function with function_id {function_id} retrieved")
                return True, function
            else:
                logger.info(f"No function found with function_id {function_id}")
                return False, "No document found"
        except errors.PyMongoError as e:
            logger.error(f"Error retrieving function: {e}")
            return False, str(e)


class OrgToolsDatabase:
    def __init__(self):
        try:
            uri = os.getenv("MONGO_URL", "mongodb://localhost:27017")
            self.client = MongoClient(uri)
            self.db = self.client["orgs"]
            self.collection = self.db["org_tools"]
            logger.info("MongoDB connection established for OrgToolsDatabase")
        except errors.ConnectionFailure as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise

    def insert(self, tool: OrgTools) -> Tuple[bool, Union[str, None]]:
        try:
            document = tool.to_dict()
            result = self.collection.insert_one(document)
            logger.info(f"Tool inserted with tool_id: {tool.tool_id}")
            return True, str(result.inserted_id)
        except errors.PyMongoError as e:
            logger.error(f"Error inserting tool: {e}")
            return False, str(e)

    def update(self, tool_id: str, update_fields: Dict) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.update_one(
                {"tool_id": tool_id},
                {"$set": update_fields},
                upsert=True
            )
            if result.modified_count > 0:
                logger.info(f"Tool with tool_id {tool_id} updated")
                return True, result.modified_count
            else:
                logger.info(f"No document found with tool_id {tool_id} to update")
                return False, "No document found to update"
        except errors.PyMongoError as e:
            logger.error(f"Error updating tool: {e}")
            return False, str(e)

    def delete(self, tool_id: str) -> Tuple[bool, Union[int, str]]:
        try:
            result = self.collection.delete_one({"tool_id": tool_id})
            if result.deleted_count > 0:
                logger.info(f"Tool with tool_id {tool_id} deleted")
                return True, result.deleted_count
            else:
                logger.info(f"No document found with tool_id {tool_id} to delete")
                return False, "No document found to delete"
        except errors.PyMongoError as e:
            logger.error(f"Error deleting tool: {e}")
            return False, str(e)

    def query(self, query_filter: Dict) -> Tuple[bool, Union[List[Dict], str]]:
        try:
            result = self.collection.find(query_filter)
            documents = []
            for doc in result:
                doc.pop('_id', None)
                documents.append(doc)
            logger.info(f"Query successful, found {len(documents)} tools")
            return True, documents
        except errors.PyMongoError as e:
            logger.error(f"Error querying tools: {e}")
            return False, str(e)

    def get_by_tool_id(self, tool_id: str) -> Tuple[bool, Union[OrgTools, str]]:
        try:
            doc = self.collection.find_one({"tool_id": tool_id})
            if doc:
                doc.pop('_id', None)
                tool = OrgTools.from_dict(doc)
                logger.info(f"Tool with tool_id {tool_id} retrieved")
                return True, tool
            else:
                logger.info(f"No tool found with tool_id {tool_id}")
                return False, "No document found"
        except errors.PyMongoError as e:
            logger.error(f"Error retrieving tool: {e}")
            return False, str(e)