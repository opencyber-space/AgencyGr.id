from typing import Tuple
import os
import requests
import logging
from .schema import OrgFunctions, OrgTools
from .crud import OrgFunctionsDatabase, OrgToolsDatabase

logger = logging.getLogger(__name__)

class FunctionDBClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def get_function_by_id(self, function_id: str) -> dict:
        url = f"{self.base_url}/{function_id}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()["data"]
            elif response.status_code == 404:
                raise Exception(f"Function '{function_id}' not found.")
            else:
                raise Exception(f"Error {response.status_code}: {response.text}")
        except requests.RequestException as e:
            logger.error(f"Request to {url} failed: {e}")
            raise Exception(f"Request failed: {str(e)}")


class ToolDBClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def get_tool_by_id(self, tool_id: str) -> dict:
        url = f"{self.base_url}/get/{tool_id}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()["data"]
            elif response.status_code == 404:
                raise Exception(f"Tool '{tool_id}' not found.")
            else:
                raise Exception(f"Error {response.status_code}: {response.text}")
        except requests.RequestException as e:
            logger.error(f"Request to {url} failed: {e}")
            raise Exception(f"Request failed: {str(e)}")


def register_function_entry(function_id: str) -> Tuple[bool, str]:
    try:
        client = FunctionDBClient(base_url=os.getenv("FUNCTION_DB_SERVER", "http://localhost:3000"))
        fn_data = client.get_function_by_id(function_id)

        function = OrgFunctions(
            function_id=fn_data.get("function_id", ""),
            function_search_tags=fn_data.get("function_tags", []),
            function_metadata={
                "name": fn_data.get("function_name", ""),
                "version": fn_data.get("function_version", {}),
                "type": fn_data.get("function_type", ""),
                "sub_type": fn_data.get("function_sub_type", ""),
                "api_spec": fn_data.get("function_api_spec", {}),
                "protocol_type": fn_data.get("function_protocol_type", ""),
                "calling_data": fn_data.get("function_calling_data", {}),
                "url": fn_data.get("function_url", ""),
                "man_page": fn_data.get("function_man_page", "")
            },
            function_description=fn_data.get("function_description", ""),
            function_default_params={}  # Fill as required
        )

        db = OrgFunctionsDatabase()
        success, result = db.insert(function)

        if success:
            logger.info(f"Successfully registered function entry {function_id}")
            return True, f"Inserted function with id: {result}"
        else:
            logger.warning(f"Failed to insert function entry {function_id}: {result}")
            return False, result

    except Exception as e:
        logger.error(f"register_function_entry error for {function_id}: {e}")
        return False, str(e)


def register_tool_entry(tool_id: str) -> Tuple[bool, str]:
    try:
        client = ToolDBClient(base_url=os.getenv("TOOL_DB_SERVER", "http://localhost:3000"))
        tool_data = client.get_tool_by_id(tool_id)

        tool = OrgTools(
            tool_id=tool_data.get("tool_id", ""),
            tool_search_tags=tool_data.get("tool_tags", []),
            tool_metadata={
                "description": tool_data.get("tool_search_description", ""),
                "type": tool_data.get("tool_type", ""),
                "sub_type": tool_data.get("tool_sub_type", ""),
                "runtime_type": tool_data.get("tool_runtime_type", ""),
                "input_schema": tool_data.get("tool_input_schema", {}),
                "output_schema": tool_data.get("tool_output_schema", {}),
                "data": tool_data.get("tool_data", {}),
                "source_code_link": tool_data.get("tool_source_code_link", ""),
                "man_page_doc_link": tool_data.get("tool_man_page_doc_link", "")
            },
            tool_description=tool_data.get("tool_search_description", ""),
            tool_default_params={}  # You can customize this if needed
        )

        db = OrgToolsDatabase()
        success, result = db.insert(tool)

        if success:
            logger.info(f"Successfully registered tool entry {tool_id}")
            return True, f"Inserted tool with id: {result}"
        else:
            logger.warning(f"Failed to insert tool entry {tool_id}: {result}")
            return False, result

    except Exception as e:
        logger.error(f"register_tool_entry error for {tool_id}: {e}")
        return False, str(e)