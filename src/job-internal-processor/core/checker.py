import os
import logging
from typing import Union, Dict, Any
from .tasks.schema import TaskEntry, SubTaskEntry
from dsl_executor import new_dsl_workflow_executor, parse_dsl_output

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TaskAcceptanceChecker")


class TaskAcceptanceChecker:
    def __init__(self, is_remote: bool = False):
        self.task_approval_dsl_url = os.getenv(
            "ORG_TASK_ACCEPT_REJECT_DSL_URL")
        self.sub_task_approval_dsl_url = os.getenv(
            "ORG_SUB_TASK_ACCEPT_REJECT_DSL_URL")
        self.is_remote = is_remote

    def check(self, obj: Union[TaskEntry, SubTaskEntry]) -> Dict[str, Any]:
        try:
            dsl_id = None
            base_url = None
            input_data = {}

            if isinstance(obj, TaskEntry):
                dsl_id = obj.task_op_convertor_dsl_id
                base_url = self.task_approval_dsl_url
                input_data = {
                    "task_id": obj.task_id,
                    "goal": obj.task_goal,
                    "intent": obj.task_intent,
                    "submitter_subject_id": obj.submitter_subject_id,
                    "metadata": obj.task_streeability_data,
                }

            elif isinstance(obj, SubTaskEntry):
                dsl_id = obj.sub_task_behavior_dsl_map.get("approval_dsl_id")
                base_url = self.sub_task_approval_dsl_url
                input_data = {
                    "sub_task_id": obj.sub_task_id,
                    "goal": obj.sub_task_goal,
                    "intent": obj.sub_task_intent,
                    "parent_subject_ids": obj.parent_subject_ids,
                    "metadata": obj.sub_task_streeability_data,
                }

            if not base_url:
                logger.warning("Approval DSL URL not defined in env.")
                return {"accepted": True, "reason": "No DSL, auto-accepted."}

            executor = new_dsl_workflow_executor(
                workflow_id=dsl_id if dsl_id else "default",
                workflows_base_uri=base_url,
                is_remote=self.is_remote
            )

            output = executor.execute({"user_input": input_data})
            result = parse_dsl_output(output)

            if not isinstance(result, dict) or "accepted" not in result:
                logger.warning(
                    "Invalid DSL output format, defaulting to accept.")
                return {"accepted": True, "reason": "Invalid DSL output"}

            return {
                "accepted": result["accepted"],
                "reason": result.get("reason", ""),
                "metadata": result.get("metadata", {})
            }

        except Exception as e:
            logger.exception("Error during DSL acceptance check.")
            return {"accepted": True, "reason": "DSL execution failed, fallback accept."}
