import logging
import os
import requests
from typing import Union, Dict, Tuple, Any
from queue import Queue, PriorityQueue, Empty

from .tasks.schema import TaskEntry, SubTaskEntry
from .tasks.db import TaskEntryDatabase, SubTaskEntryDatabase
from .checker import TaskAcceptanceChecker
from .tasks.db import TaskEntry, Tas

from dsl_executor import new_dsl_workflow_executor, parse_dsl_output

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PriorityReorganizer")


class PriorityReorganizer:
    def __init__(self, is_remote: bool = False):
        self.task_dsl_fallback = os.getenv("ORG_TASK_PRIORITY_ORGANIZER_URL")
        self.sub_task_dsl_fallback = os.getenv(
            "ORG_SUB_TASK_PRIORITY_ORGANIZER_URL")
        self.is_remote = is_remote

    def get_priority(self, obj: Union[TaskEntry, SubTaskEntry]) -> int:
        try:
            dsl_id = None
            workflows_base_uri = None
            base_priority = 0
            input_data: Dict = {}

            if isinstance(obj, TaskEntry):
                dsl_id = obj.task_behavior_dsl_map.get(
                    "priority_assigner_dsl_id")
                workflows_base_uri = self.task_dsl_fallback
                base_priority = obj.task_priority_value
                input_data = {
                    "task_id": obj.task_id,
                    "goal": obj.task_goal,
                    "intent": obj.task_intent,
                    "submitter_subject_id": obj.submitter_subject_id
                }

            elif isinstance(obj, SubTaskEntry):
                dsl_id = obj.sub_task_behavior_dsl_map.get(
                    "priority_assigner_dsl_id")
                workflows_base_uri = self.sub_task_dsl_fallback
                base_priority = obj.sub_task_priority_value
                input_data = {
                    "sub_task_id": obj.sub_task_id,
                    "goal": obj.sub_task_goal,
                    "intent": obj.sub_task_intent,
                    "parent_subject_ids": obj.parent_subject_ids
                }

            if not workflows_base_uri:
                logger.warning("No DSL workflow base URI found in env.")
                return base_priority

            executor = new_dsl_workflow_executor(
                workflow_id=dsl_id if dsl_id else "default",
                workflows_base_uri=workflows_base_uri,
                is_remote=self.is_remote
            )

            logger.info(f"Running priority DSL for: {input_data}")
            output = executor.execute({"user_input": input_data})
            parsed_output = parse_dsl_output(output)

            if isinstance(parsed_output, dict) and "priority" in parsed_output:
                return int(parsed_output["priority"])

            logger.warning(
                "DSL output missing 'priority'. Using fallback priority.")
            return base_priority

        except Exception as e:
            logger.exception(
                "Error running DSL. Falling back to base priority.")
            return base_priority


class TasksProcessor:
    def __init__(self, incoming_queue: Queue, final_priority_queue: PriorityQueue):
        self.incoming_queue = incoming_queue
        self.final_priority_queue = final_priority_queue
        self.reorganizer = PriorityReorganizer()
        self.acceptance_checker = TaskAcceptanceChecker()
        self.task_db = TaskEntryDatabase()
        self.sub_task_db = SubTaskEntryDatabase()
        self.process_api_url = os.getenv(
            "PROCESS_TASK_API", "http://localhost:7000/internal/process-task")

    def process_next(self):
        try:
            item: Tuple[int, Dict[str, Any]] = self.incoming_queue.get_nowait()
            _, payload = item

            task_type = payload.get("type")
            raw_data = payload.get("data")

            if task_type == "task":
                task = TaskEntry.from_dict(raw_data)
                result = self.acceptance_checker.check(task)

                if result["accepted"]:
                    self._update_status("task", task.task_id, "accepted")
                    self._submit_task(task_type, task)
                    new_priority = self.reorganizer.get_priority(task)
                    self.final_priority_queue.put(
                        (new_priority, {"type": "task", "data": task}))
                else:
                    self._update_status("task", task.task_id, "rejected")
                    logger.warning(
                        f"Task {task.task_id} rejected: {result.get('reason')}")

            elif task_type == "sub_task":
                sub_task = SubTaskEntry.from_dict(raw_data)
                result = self.acceptance_checker.check(sub_task)

                if result["accepted"]:
                    self._update_status(
                        "sub_task", sub_task.sub_task_id, "accepted")
                    self._submit_task(task_type, sub_task)
                    new_priority = self.reorganizer.get_priority(sub_task)
                    self.final_priority_queue.put(
                        (new_priority, {"type": "sub_task", "data": sub_task}))
                else:
                    self._update_status(
                        "sub_task", sub_task.sub_task_id, "rejected")
                    logger.warning(
                        f"Sub-task {sub_task.sub_task_id} rejected: {result.get('reason')}")

            else:
                logger.warning(f"Unknown task type received: {task_type}")

        except Empty:
            logger.debug("Incoming queue is empty.")
        except Exception as e:
            logger.exception("Unexpected error during task processing.")

    def _update_status(self, task_type: str, id_value: str, new_status: str):
        db = self.task_db if task_type == "task" else self.sub_task_db
        id_field = "task_id" if task_type == "task" else "sub_task_id"
        success, _ = db.update(id_field=id_field, id_value=id_value, update_fields={
                               "status": new_status})
        if success:
            logger.info(
                f"{task_type} {id_value} status updated to '{new_status}' in DB.")
        else:
            logger.error(
                f"Failed to update status for {task_type} {id_value}.")

    def _submit_task(self, task_type: str, obj: Any):
        try:
            response = requests.post(self.process_api_url, json={
                "type": task_type,
                "data": obj.to_dict()
            })
            if response.ok:
                logger.info(f"Submitted {task_type} to process-task API.")
            else:
                logger.warning(
                    f"Failed to submit {task_type}: {response.status_code} - {response.text}")
        except Exception as e:
            logger.exception(
                f"Exception while submitting {task_type} to process-task API.")
