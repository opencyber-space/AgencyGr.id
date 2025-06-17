import os
import time
import logging
from queue import Queue
from typing import Tuple, Dict

from agent_functions.sdk import FunctionExecutor
from agent_functions.db_client import FunctionsRegistryDB
from agents_tools_executor import ToolExecutor
from .crud import OrgFunctionsDatabase
from .crud import OrgToolsDatabase

from .tools_registry import ToolsRegistryClient

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class FunctionExecutorWrapper:
    def __init__(self, function_id: str, base_url: str):
        try:
            sdk = FunctionsRegistryDB(base_url)
            function_data = sdk.get_function_by_id(function_id)
            self.executor = FunctionExecutor(function_id, function_data)
            logger.info(f"FunctionExecutor initialized for {function_id}")
        except Exception as e:
            logger.error(
                f"Failed to initialize FunctionExecutor for {function_id}: {e}")
            raise

    def execute(self, input_data: dict) -> dict:
        try:
            logger.debug(f"Executing function with input: {input_data}")
            result = self.executor.execute(input_data)
            logger.info("Function execution completed successfully")
            return result
        except Exception as e:
            logger.error(f"Function execution failed: {e}")
            raise


class ToolExecutorWrapper:
    def __init__(self, tool_id: str, base_url: str):
        try:
            sdk = ToolsRegistryClient(base_url)
            tool_data = sdk.get_tool_by_id(tool_id)
            self.executor = ToolExecutor(tool_id=tool_id, tool_data=tool_data)
            logger.info(f"ToolExecutor initialized for {tool_id}")
        except Exception as e:
            logger.error(
                f"Failed to initialize ToolExecutor for {tool_id}: {e}")
            raise

    def execute(self, input_data: dict) -> dict:
        try:
            logger.debug(f"Executing tool with input: {input_data}")
            result = self.executor.execute(input_data)
            logger.info("Tool execution completed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            raise


class FunctionTaskExecutor:
    def __init__(self, producer_queue: Queue, base_url: str):
        self.consumer_queue: Queue = Queue()
        self.producer_queue = producer_queue
        self.base_url = base_url
        self.db = OrgFunctionsDatabase()

    def push_task_to_queue(self, uuid: str, function_id: str, input_data: dict) -> Tuple[bool, str]:
        found, _ = self.db.get_by_functsion_id(function_id)
        if not found:
            logger.warning(
                f"Function ID {function_id} not found. Task {uuid} not queued.")
            return False, "Function not registered"

        self.consumer_queue.put({
            "uuid": uuid,
            "function_id": function_id,
            "input_data": input_data
        })
        logger.info(
            f"Task {uuid} pushed to queue for function_id: {function_id}")
        return True, "Task queued"

    def run(self):
        logger.info("FunctionTaskExecutor run loop started.")
        while True:
            try:
                task = self.consumer_queue.get(block=True)
                uuid = task["uuid"]
                function_id = task["function_id"]
                input_data = task["input_data"]

                logger.debug(
                    f"Processing function task {uuid} for {function_id}")
                executor = FunctionExecutorWrapper(function_id, self.base_url)
                result = executor.execute(input_data)
                self.producer_queue.put({"uuid": uuid, "output": result})
                logger.info(f"Function task {uuid} completed")
            except Exception as e:
                logger.error(f"Error processing function task {uuid}: {e}")
            finally:
                time.sleep(0.1)


class ToolTaskExecutor:
    def __init__(self, producer_queue: Queue, base_url: str):
        self.consumer_queue: Queue = Queue()
        self.producer_queue = producer_queue
        self.base_url = base_url
        self.db = OrgToolsDatabase()

    def push_task_to_queue(self, uuid: str, tool_id: str, input_data: dict) -> Tuple[bool, str]:
        found, _ = self.db.get_by_tool_id(tool_id)
        if not found:
            logger.warning(
                f"Tool ID {tool_id} not found. Task {uuid} not queued.")
            return False, "Tool not registered"

        self.consumer_queue.put({
            "uuid": uuid,
            "tool_id": tool_id,
            "input_data": input_data
        })
        logger.info(f"Task {uuid} pushed to queue for tool_id: {tool_id}")
        return True, "Task queued"

    def run(self):
        logger.info("ToolTaskExecutor run loop started.")
        while True:
            try:
                task = self.consumer_queue.get(block=True)
                uuid = task["uuid"]
                tool_id = task["tool_id"]
                input_data = task["input_data"]

                logger.debug(f"Processing tool task {uuid} for {tool_id}")
                executor = ToolExecutorWrapper(tool_id, self.base_url)
                result = executor.execute(input_data)
                self.producer_queue.put({"uuid": uuid, "output": result})
                logger.info(f"Tool task {uuid} completed")
            except Exception as e:
                logger.error(f"Error processing tool task {uuid}: {e}")
            finally:
                time.sleep(0.1)
