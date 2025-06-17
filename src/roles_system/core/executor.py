import logging
from typing import Dict, Any

import queue
import threading
import uuid

from .direct import DirectSubjectAssignmentHandler
from .search import CriteriaBasedSubjectAssignmentHandler
from .auction import AuctionBasedSubjectAssignmentHandler
from .removal import RoleRemovalHandler
from .db.crud import RoleApplicationDatabase
from .db.schema import RoleApplication

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def execute_roles_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        action = payload.get("action")
        if not action:
            return {"success": False, "message": "Missing 'action' field in payload"}

        # Dispatch table
        if action == "assign_direct":
            required_fields = ["role_application_id",
                               "application_data", "subject_id", "subject_data"]
            if not all(field in payload for field in required_fields):
                return {"success": False, "message": f"Missing required fields for {action}"}

            handler = DirectSubjectAssignmentHandler()
            return handler.handle(
                role_application_id=payload["role_application_id"],
                application_data=payload["application_data"],
                subject_id=payload["subject_id"],
                subject_data=payload["subject_data"]
            )

        elif action == "assign_by_criteria":
            required_fields = ["role_application_id",
                               "application_data", "selection_criteria"]
            if not all(field in payload for field in required_fields):
                return {"success": False, "message": f"Missing required fields for {action}"}

            handler = CriteriaBasedSubjectAssignmentHandler()
            return handler.handle(
                role_application_id=payload["role_application_id"],
                application_data=payload["application_data"],
                selection_criteria=payload["selection_criteria"]
            )

        elif action == "assign_by_auction":
            required_fields = ["role_application_id",
                               "application_data", "subject_list"]
            if not all(field in payload for field in required_fields):
                return {"success": False, "message": f"Missing required fields for {action}"}

            handler = AuctionBasedSubjectAssignmentHandler()
            return handler.handle(
                role_application_id=payload["role_application_id"],
                application_data=payload["application_data"],
                subject_list=payload["subject_list"]
            )

        elif action == "remove":
            required_fields = ["role_id", "subject_id"]
            if not all(field in payload for field in required_fields):
                return {"success": False, "message": f"Missing required fields for {action}"}

            handler = RoleRemovalHandler()
            return handler.remove_role(
                role_id=payload["role_id"],
                subject_id=payload["subject_id"]
            )

        else:
            return {"success": False, "message": f"Unknown action: {action}"}

    except Exception as e:
        logger.error(f"Error in execute_roles_action: {e}", exc_info=True)
        return {"success": False, "message": str(e)}



class RolesExecutor:
    def __init__(self):
        self.task_queue = queue.Queue()
        self.db = RoleApplicationDatabase()

        self.worker_thread = threading.Thread(target=self.run, daemon=True)
        self.worker_thread.start()
        logger.info("RolesExecutor started")

    def submit_task(self, role_application_id: str, input_payload: Dict[str, Any]):
        self.task_queue.put((role_application_id, input_payload))
        logger.info(f"Task submitted to executor with ID: {role_application_id}")

    def run(self):
        while True:
            try:
                role_application_id, input_payload = self.task_queue.get()
                logger.info(f"Processing task: {role_application_id}")

                # Step 1: Insert new role application with pending status
                role_application = RoleApplication(
                    role_application_id=role_application_id,
                    application_data=input_payload,
                    submission_time=int(uuid.uuid1().time),
                    status="pending",
                    response_data={}
                )
                self.db.insert(role_application)

                # Step 2: Execute role action
                result = execute_roles_action(input_payload)

                # Step 3: Update DB with result
                status = "success" if result.get("success") else "failed"
                self.db.update(role_application_id, {
                    "status": status,
                    "response_data": result
                })
                logger.info(f"Task {role_application_id} processed with status: {status}")

            except Exception as e:
                logger.error(f"Error processing task: {e}", exc_info=True)