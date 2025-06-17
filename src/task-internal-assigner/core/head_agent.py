import os
import logging
import requests
from typing import List, Optional
from .schema import TaskEntry

from .config import OrgExecutionConfigProvider
from .db import TaskEntryDatabase
from .agent_input import AgentQueueClient
from .methods.bidding import AuctionBasedAgentSelector
from .methods.search import PlanRetrieveAgentSelector
from .methods.static import StaticAgentSelector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentCandidatePoolResolver")

class AgentCandidatePoolResolver:
    def __init__(self):
        self.role_group_api = os.getenv("ROLE_GROUP_API", "http://localhost:7000/role-group")
        self.subject_roles_api = os.getenv("SUBJECT_ROLES_API", "http://localhost:7000/subject-roles")

    def resolve(self, obj: TaskEntry) -> Optional[List[str]]:
        try:
            job_space_id = obj.task_job_submission_data.get("job_space_id")
            if not job_space_id:
                logger.warning("Missing job_space_id in task.")
                return []

            # Step 1: Query role-group for SCOUTING roles
            scout_roles_resp = requests.post(self.role_group_api, json={
                "role_type": "SCOUTING",
                "job_space_id": job_space_id
            })
            scout_roles_data = scout_roles_resp.json()
            if not scout_roles_data.get("success"):
                logger.error(f"Failed to fetch role groups: {scout_roles_data.get('error')}")
                return []

            role_ids = [r["role_id"] for r in scout_roles_data["data"]]
            logger.info(f"Found {len(role_ids)} SCOUTING roles.")

            if not role_ids:
                return []

            # Step 2: Query subject-role mappings for those roles
            subject_roles_resp = requests.post(self.subject_roles_api, json={
                "role_ids": {"$in": role_ids},
                "job_space_id": job_space_id
            })
            subject_roles_data = subject_roles_resp.json()
            if not subject_roles_data.get("success"):
                logger.error(f"Failed to fetch subject-role mappings: {subject_roles_data.get('error')}")
                return []

            subject_ids = [s["subject_id"] for s in subject_roles_data["data"]]
            logger.info(f"Found {len(subject_ids)} subject candidates for scouting.")

            return subject_ids

        except Exception as e:
            logger.exception("Error resolving agent candidate pool")
            return []


class HeadAgentAssociationModule:
    def __init__(self):
        self.pool_resolver = AgentCandidatePoolResolver()
        self.config_provider = OrgExecutionConfigProvider()
        self.task_db = TaskEntryDatabase()
        self.agent_queue = AgentQueueClient()
        self.auction_selector = AuctionBasedAgentSelector()
        self.plan_selector = PlanRetrieveAgentSelector()
        self.static_selector = StaticAgentSelector()

    def associate_and_dispatch(self, task: TaskEntry) -> Optional[str]:
        try:
            org_id = task.submitter_subject_id.split(":")[0]
            strategy = self.config_provider.get(org_id, "agent_resolution_strategy")
            if not strategy:
                raise ValueError(f"No agent resolution strategy configured for org {org_id}")

            candidate_subjects = self.pool_resolver.resolve(task)
            if not candidate_subjects:
                raise ValueError("No eligible agent candidates found")

            selected_subject_id = None

            if strategy == "auction":
                selected_subject_id = self.auction_selector.resolve_head_agent(task)
            elif strategy == "plan+retrieve":
                selected_subject_id = self.plan_selector.resolve_head_agent(task, candidate_subjects)
            elif strategy == "static":
                selected_subject_id = self.static_selector.resolve_head_agent(task, candidate_subjects)
            else:
                raise ValueError(f"Unsupported strategy: {strategy}")

            if not selected_subject_id:
                raise ValueError("Head agent resolution failed")

            logger.info(f"Task {task.task_id} assigned to {selected_subject_id}")

            # Update DB
            update_status = {
                "status": "assigned",
                "assigned_subject_id": selected_subject_id
            }
            self.task_db.update("task_id", task.task_id, update_status)

            # Push to agent queue
            self.agent_queue.push(subject_id=selected_subject_id, task_data=task.to_dict())

            return selected_subject_id

        except Exception as e:
            logger.exception("Head agent association and dispatch failed")
            return None

