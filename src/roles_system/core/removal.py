import logging
from typing import Dict, Any, Optional

from .db.crud import RoleGroupMappingDatabase
from .db.crud import RoleTypeAssignmentMappingDatabase
from .db.crud import SubjectRolesMappingDatabase
from dsl_executor import DSLExecutor

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class RoleRemovalHandler:
    def __init__(self):
        self.role_group_db = RoleGroupMappingDatabase()
        self.role_type_db = RoleTypeAssignmentMappingDatabase()
        self.subject_roles_db = SubjectRolesMappingDatabase()

    def remove_role(self, role_id: str, subject_id: str) -> Dict[str, Any]:
        try:
            # Step 1: Get role info
            success, role_entry = self.role_group_db.get_by_role_id(role_id)
            if not success:
                return {"success": False, "message": f"Role {role_id} not found"}

            role_type = role_entry.role_type
            role_data = role_entry.to_dict()

            # Step 2: Get role type metadata
            success, role_type_entry = self.role_type_db.get_by_role_type(
                role_type)
            if not success:
                return {"success": False, "message": f"Role type {role_type} not found"}

            if role_type_entry.role_assignment_type == "fixed":
                logger.warning(f"Cannot remove fixed role: {role_type}")
                return {"success": False, "message": "Role is fixed and cannot be removed"}

            # Step 3: Run role_removal_check_dsl
            removal_dsl_id = role_type_entry.role_post_removal_dsl_workflow_id
            if not removal_dsl_id:
                return {"success": False, "message": "No role_removal_check_dsl_workflow_id found"}

            executor = DSLExecutor(workflow_id=removal_dsl_id)
            dsl_input = {"subject_id": subject_id, "role_data": role_data}
            dsl_output = executor.run(dsl_input)

            if not executor.get_final_output(dsl_output):
                return {"success": False, "message": "DSL denied role removal"}

            # Step 4a: Remove role entry
            delete_success, delete_info = self.role_group_db.delete(role_id)
            if not delete_success:
                return {"success": False, "message": f"Failed to delete role {role_id}"}

            # Step 4b: Update subject_roles_mapping
            success, subject_entry = self.subject_roles_db.get_by_subject_id(
                subject_id)
            if not success:
                return {"success": False, "message": f"Subject {subject_id} not found"}

            updated_roles = [
                rid for rid in subject_entry.role_ids if rid != role_id]

            if updated_roles:
                self.subject_roles_db.update(
                    subject_id, {"role_ids": updated_roles})
            else:
                # Optional: delete subject entry if no roles left
                self.subject_roles_db.delete(subject_id)

            logger.info(
                f"Successfully removed role {role_id} from subject {subject_id}")
            return {"success": True, "message": "Role removed successfully"}

        except Exception as e:
            logger.error(f"Role removal failed: {e}", exc_info=True)
            return {"success": False, "message": str(e)}
