import logging
import time
from queue import Queue
from typing import Any, Dict, Tuple

from .dsl import OrgDSLWorkflowsDatabase

from dsl_executor import new_dsl_workflow_executor, parse_dsl_output


logger = logging.getLogger(__name__)


class DSLExecutor:
    def __init__(
        self,
        workflow_id: str,
        workflows_base_uri: str,
        is_remote: bool = False,
        addons: Dict[str, Any] = None
    ):
        
        try:
            self.executor = new_dsl_workflow_executor(
                workflow_id=workflow_id,
                workflows_base_uri=workflows_base_uri,
                is_remote=is_remote,
                addons=addons or {}
            )
            logger.info(f"DSLExecutor initialized for workflow_id: {workflow_id}")
        except Exception as e:
            logger.error(f"Failed to initialize DSLExecutor for {workflow_id}: {e}")
            raise

    def execute(self, input_data: Dict[str, Any], output_name: str) -> Any:
        try:
            logger.debug(f"Executing DSL with input: {input_data}")
            output = self.executor.execute(input_data)
            logger.info("DSL execution completed successfully")
            return parse_dsl_output(output, output_name)
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            raise



logger 

class DSLTaskExecutor:
    def __init__(self, producer_queue: Queue, workflows_base_uri: str, is_remote: bool = False):
       
        self.consumer_queue: Queue = Queue()
        self.producer_queue = producer_queue
        self.workflows_base_uri = workflows_base_uri
        self.is_remote = is_remote
        self.db = OrgDSLWorkflowsDatabase()

    def push_task_to_queue(self, uuid: str, workflow_id: str, input_data: Dict[str, Any], output_name: str) -> Tuple[bool, str]:
        
        found, _ = self.db.get_by_workflow_id(workflow_id)
        if not found:
            logger.warning(f"Workflow ID {workflow_id} not found in DB. Task {uuid} not queued.")
            return False, "Workflow not registered"

        self.consumer_queue.put({
            "uuid": uuid,
            "workflow_id": workflow_id,
            "input_data": input_data,
            "output_name": output_name
        })
        logger.info(f"Task {uuid} pushed to queue for workflow_id: {workflow_id}")
        return True, "Task queued"

    def run(self):
        
        logger.info("DSLTaskExecutor run loop started.")
        while True:
            try:
                task = self.consumer_queue.get(block=True)
                uuid = task["uuid"]
                workflow_id = task["workflow_id"]
                input_data = task["input_data"]
                output_name = task["output_name"]

                logger.debug(f"Processing task {uuid} for workflow {workflow_id}")

                executor = DSLExecutor(
                    workflow_id=workflow_id,
                    workflows_base_uri=self.workflows_base_uri,
                    is_remote=self.is_remote
                )

                output = executor.execute(input_data, output_name)
                self.producer_queue.put({"uuid": uuid, "output": output})
                logger.info(f"Task {uuid} completed and result pushed to producer queue")

            except Exception as e:
                logger.error(f"Error processing task: {e}")
                continue
            finally:
                time.sleep(0.1) 
