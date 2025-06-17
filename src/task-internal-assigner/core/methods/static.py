import logging
from typing import Optional, List
from ..schema import TaskEntry
from ..config import OrgExecutionConfigProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StaticAgentSelector")

class StaticAgentSelector:
    def __init__(self):
        self.config = OrgExecutionConfigProvider()

    def resolve_head_agent(self, task: TaskEntry, candidate_subject_ids: List[str]) -> Optional[str]:
        try:
            org_id = task.submitter_subject_id.split(":")[0]  
            head_subject_id = self.config.get(org_id, "static_head_agent_subject_id")

            if not head_subject_id:
                raise ValueError(f"Static agent subject ID not configured for org: {org_id}")

            if head_subject_id not in candidate_subject_ids:
                raise ValueError(f"Configured static subject_id '{head_subject_id}' is not in eligible pool: {candidate_subject_ids}")

            logger.info(f"Static head agent resolved: {head_subject_id}")
            return head_subject_id

        except Exception as e:
            logger.exception("Static head agent resolution failed")
            raise
