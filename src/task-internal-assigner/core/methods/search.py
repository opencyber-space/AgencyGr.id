import os
import logging
from typing import Optional, List
from ..schema import TaskEntry
from dsl_executor import new_dsl_workflow_executor, parse_dsl_output
from ..config import OrgExecutionConfigProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PlanRetrieveAgentSelector")

class PlanRetrieveAgentSelector:
    def __init__(self):
        self.config = OrgExecutionConfigProvider()
        self.default_dsl_base = os.getenv("ORG_PLAN_RETRIEVE_DSL_URL")
        self.is_remote = os.getenv("PLAN_DSL_REMOTE", "false").lower() == "true"

    def resolve_head_agent(self, task: TaskEntry, candidate_subject_ids: List[str]) -> Optional[str]:
        try:
            org_id = task.submitter_subject_id.split(":")[0]
            dsl_id = task.task_behavior_dsl_map.get("plan_retrieve_dsl_id")

            if not dsl_id:
                dsl_id = self.config.get(org_id, "plan_retrieve_dsl_id")

            if not dsl_id or not self.default_dsl_base:
                raise ValueError("Missing DSL ID or base URL for plan+retrieve")

            logger.info(f"Executing plan+retrieve DSL: {dsl_id} for org: {org_id}")

            executor = new_dsl_workflow_executor(
                workflow_id=dsl_id,
                workflows_base_uri=self.default_dsl_base,
                is_remote=self.is_remote
            )

            dsl_input = {
                "user_input": {
                    "task_id": task.task_id,
                    "goal": task.task_goal,
                    "intent": task.task_intent,
                    "submitter_subject_id": task.submitter_subject_id,
                    "candidate_subject_ids": candidate_subject_ids,
                    "job_space_id": task.task_job_submission_data.get("job_space_id"),
                }
            }

            output = executor.execute(dsl_input)
            result = parse_dsl_output(output)

            if not isinstance(result, dict) or "head_agent_subject_id" not in result:
                raise ValueError("Invalid DSL output: Missing 'head_agent_subject_id'")

            selected = result["head_agent_subject_id"]
            logger.info(f"Plan+Retrieve selected agent: {selected}")
            return selected

        except Exception as e:
            logger.exception("Plan+Retrieve strategy failed")
            return None
