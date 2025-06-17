import uuid
import logging
import os
from typing import Dict, Any, Optional, List

from .db.crud import RoleTypeAssignmentMappingDatabase
from .db.crud import SubjectRolesMappingDatabase
from .db.crud import RoleGroupMappingDatabase
from .clients.dsl import DSLExecutor
from .clients.auction import AuctionClient
from .clients.role_assoc import SubjectAssociationClient
from .db.schema import SubjectRolesMapping, RoleGroupMapping

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class AuctionBasedSubjectAssignmentHandler:
    def __init__(self):
        self.role_type_db = RoleTypeAssignmentMappingDatabase()
        self.subject_roles_db = SubjectRolesMappingDatabase()
        self.role_group_db = RoleGroupMappingDatabase()
        self.auction_client = AuctionClient(api_url=os.getenv(
            "AUCTION_API_URL", "http://localhost:7000"))

    def handle(
        self,
        role_application_id: str,
        application_data: Dict[str, Any],
        subject_list: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        try:
            role_type = application_data.get("role_type")
            if not role_type:
                raise ValueError("Missing role_type in application_data")

            # Step 1: Fetch role type metadata
            success, result = self.role_type_db.get_by_role_type(role_type)
            if not success:
                raise ValueError(f"Role type {role_type} not found")

            role_type_data = result
            role_assignment_type = role_type_data.role_assignment_type

            if role_assignment_type not in ["dynamic_single_subject", "dynamic_multi_subject"]:
                return {"success": False, "message": "Unsupported role assignment type"}

            if role_assignment_type == "dynamic_single_subject" and role_type_data.position_filled:
                return {"success": False, "message": "Role already filled"}

            # Step 2: Run role auction creation DSL
            auction_dsl_id = getattr(
                role_type_data, "role_auction_creation_dsl_workflow_id", "")
            if not auction_dsl_id:
                raise ValueError(
                    "Missing role_auction_creation_dsl_workflow_id")

            dsl_input = {
                "role_type_data": role_type_data.to_dict(),
                "subjects": subject_list
            }

            auction_dsl = DSLExecutor(workflow_id=auction_dsl_id)
            auction_payload = auction_dsl.get_final_output(
                auction_dsl.run(dsl_input))

            if not auction_payload:
                return {"success": False, "message": "Auction DSL failed to generate payload"}

            # Step 3: Submit auction task and wait
            logger.info("Submitting auction task")
            result = self.auction_client.submit_bid_and_wait(auction_payload)
            if not result or not result.get("success"):
                return {"success": False, "message": "Auction execution failed"}

            winner_subject_id = result["data"].get("winner_subject_id")
            if not winner_subject_id:
                return {"success": False, "message": "No winner selected in auction"}

            logger.info(f"Auction winner: {winner_subject_id}")

            # Step 4: Match subject info
            winner_subject_entry = next(
                (s for s in subject_list if s["subject_id"] == winner_subject_id), None)
            if not winner_subject_entry:
                return {"success": False, "message": "Winner subject not found in original list"}

            subject_data = winner_subject_entry["subject_data"]

            # Step 5: Evaluate subject with DSL
            eval_dsl_id = role_type_data.role_post_removal_dsl_workflow_id
            eval_executor = DSLExecutor(workflow_id=eval_dsl_id)
            eval_output = eval_executor.run({
                "role_type_data": role_type_data.to_dict(),
                "application_data": application_data
            })

            if not eval_executor.get_final_output(eval_output):
                return {"success": False, "message": "Evaluation failed for selected subject"}

            # Step 6: Associate subject and update DBs
            role_id = str(uuid.uuid4())
            role_data = {
                "role_id": role_id,
                "role_type": role_type,
                "role_application_id": role_application_id
            }

            assoc_client = SubjectAssociationClient(
                winner_subject_id, subject_data, role_data)
            assoc_result = assoc_client.create_association()
            if not assoc_result:
                return {"success": False, "message": "Subject association failed"}

            # SubjectRolesMapping
            success, subject_entry = self.subject_roles_db.get_by_subject_id(
                winner_subject_id)
            if success:
                updated_roles = list(set(subject_entry.role_ids + [role_id]))
                self.subject_roles_db.update(
                    winner_subject_id, {"role_ids": updated_roles})
            else:
                new_subject_entry = SubjectRolesMapping(
                    subject_id=winner_subject_id,
                    role_ids=[role_id],
                    subject_type=application_data.get("subject_type", ""),
                    job_space_id=""
                )
                self.subject_roles_db.insert(new_subject_entry)

            # RoleGroupMapping
            success, role_group = self.role_group_db.get_by_role_id(role_id)
            if not success:
                new_group_entry = RoleGroupMapping(
                    role_id=role_id,
                    role_type=role_type,
                    group_ids=application_data.get("group_ids", []),
                    job_space_id=""
                )
                self.role_group_db.insert(new_group_entry)

            if role_assignment_type == "dynamic_single_subject":
                self.role_type_db.update(role_type, {"position_filled": True})

            logger.info(
                f"Subject {winner_subject_id} assigned to role {role_id} via auction")
            return {"success": True, "role_id": role_id, "subject_id": winner_subject_id, "association": assoc_result}

        except Exception as e:
            logger.error(
                f"Auction-based subject assignment failed: {e}", exc_info=True)
            return {"success": False, "message": str(e)}
