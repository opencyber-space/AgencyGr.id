import uuid
import logging
from typing import Dict, Any, Optional

from .db.crud import RoleTypeAssignmentMappingDatabase
from .db.crud import SubjectRolesMappingDatabase
from .db.crud import RoleGroupMappingDatabase
from .clients.dsl import DSLExecutor
from .clients.role_assoc import SubjectAssociationClient

from db.schema import RoleGroupMapping, SubjectRolesMapping

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class DirectSubjectAssignmentHandler:
    def __init__(self):
        self.role_type_db = RoleTypeAssignmentMappingDatabase()
        self.subject_roles_db = SubjectRolesMappingDatabase()
        self.role_group_db = RoleGroupMappingDatabase()

    def handle(self, role_application_id: str, application_data: Dict[str, Any], subject_id: str, subject_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            role_type = application_data.get("role_type")
            if not role_type:
                raise ValueError("role_type not found in application_data")

            # Step 1: Fetch role type assignment mapping
            success, result = self.role_type_db.get_by_role_type(role_type)
            if not success:
                raise ValueError(f"Role type {role_type} not found")

            role_type_data = result
            role_assignment_type = role_type_data.role_assignment_type

            if role_assignment_type not in ["dynamic_single_subject", "dynamic_multi_subject"]:
                logger.warning(
                    f"Invalid role_assignment_type: {role_assignment_type}")
                return {"success": False, "message": "Assignment type not permitted"}

            # Step 2: Check position filled for single-subject roles
            if role_assignment_type == "dynamic_single_subject" and role_type_data.position_filled:
                logger.warning(
                    f"Position already filled for role_type: {role_type}")
                return {"success": False, "message": "Position already filled"}

            # Step 3: Run initial PQT check
            pqt_dsl_id = role_type_data.role_post_addition_dsl_workflow_id
            if not pqt_dsl_id:
                raise ValueError("Missing role_initial_pqt_checker_dsl_id")

            pqt_executor = DSLExecutor(workflow_id=pqt_dsl_id)
            pqt_output = pqt_executor.run(
                {"role_type_data": role_type_data.to_dict(), "application_data": application_data})
            if not pqt_executor.get_final_output(pqt_output):
                logger.warning("PQT check failed")
                return {"success": False, "message": "PQT check failed"}

            # Step 4: Run application evaluation DSL
            eval_dsl_id = role_type_data.role_post_removal_dsl_workflow_id
            if not eval_dsl_id:
                raise ValueError("Missing role_application_eval_dsl_id")

            eval_executor = DSLExecutor(workflow_id=eval_dsl_id)
            eval_output = eval_executor.run(
                {"role_type_data": role_type_data.to_dict(), "application_data": application_data})
            if not eval_executor.get_final_output(eval_output):
                logger.warning("Application evaluation failed")
                return {"success": False, "message": "Application evaluation failed"}

            # Step 5: Create subject-role association
            role_id = str(uuid.uuid4())
            role_data = {
                "role_id": role_id,
                "role_type": role_type,
                "role_application_id": role_application_id
            }

            assoc_client = SubjectAssociationClient(
                subject_id, subject_data, role_data)
            assoc_result = assoc_client.create_association()
            if not assoc_result:
                return {"success": False, "message": "Subject association failed"}

            # Step 6: Update SubjectRolesMapping
            success, subject_entry = self.subject_roles_db.get_by_subject_id(
                subject_id)
            if success:
                updated_roles = list(set(subject_entry.role_ids + [role_id]))
                self.subject_roles_db.update(
                    subject_id, {"role_ids": updated_roles})
            else:
                new_subject_entry = SubjectRolesMapping(
                    subject_id=subject_id,
                    role_ids=[role_id],
                    subject_type=application_data.get("subject_type", ""),
                    job_space_id=""
                )
                self.subject_roles_db.insert(new_subject_entry)

            # Update RoleGroupMapping
            success, role_group = self.role_group_db.get_by_role_id(role_id)
            if not success:
                new_group_entry = RoleGroupMapping(
                    role_id=role_id,
                    role_type=role_type,
                    group_ids=application_data.get("group_ids", []),
                    job_space_id=""
                )
                self.role_group_db.insert(new_group_entry)

            # Step 7: Mark filled if applicable
            if role_assignment_type == "dynamic_single_subject":
                self.role_type_db.update(role_type, {"position_filled": True})

            logger.info(
                f"Subject {subject_id} successfully assigned to role {role_id}")
            return {"success": True, "role_id": role_id, "association": assoc_result}

        except Exception as e:
            logger.error(
                f"Direct subject assignment failed: {e}", exc_info=True)
            return {"success": False, "message": str(e)}
