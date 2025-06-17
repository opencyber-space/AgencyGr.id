import uuid
import logging
from typing import Dict, Any, Optional

from .db.crud import RoleTypeAssignmentMappingDatabase
from .db.crud import SubjectRolesMappingDatabase
from .db.crud import RoleGroupMappingDatabase
from .clients.dsl import DSLExecutor
from .clients.subjects_search import SubjectsSearch
from .clients.role_assoc import SubjectAssociationClient

from .db.schema import RoleGroupMapping
from .db.schema import SubjectRolesMapping

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class CriteriaBasedSubjectAssignmentHandler:
    def __init__(self):
        self.role_type_db = RoleTypeAssignmentMappingDatabase()
        self.subject_roles_db = SubjectRolesMappingDatabase()
        self.role_group_db = RoleGroupMappingDatabase()

    def handle(
        self,
        role_application_id: str,
        application_data: Dict[str, Any],
        selection_criteria: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        try:
            role_type = application_data.get("role_type")
            if not role_type:
                raise ValueError("Missing role_type in application_data")

            # Step 1: Fetch role type data
            success, result = self.role_type_db.get_by_role_type(role_type)
            if not success:
                raise ValueError(f"Role type {role_type} not found")

            role_type_data = result
            role_assignment_type = role_type_data.role_assignment_type

            if role_assignment_type not in ["dynamic_single_subject", "dynamic_multi_subject"]:
                return {"success": False, "message": "Unsupported role assignment type"}

            if role_assignment_type == "dynamic_single_subject" and role_type_data.position_filled:
                return {"success": False, "message": "Role already filled"}

            # Step 2: Search for subjects
            filter_data = selection_criteria.get("filter_data", {})
            selection_dsl_workflow_id = selection_criteria.get("selection_dsl_workflow_id", "")
            if not selection_dsl_workflow_id:
                raise ValueError("Missing selection_dsl_workflow_id in selection_criteria")

            search = SubjectsSearch(search_filter=filter_data, dsl_workflow_id=selection_dsl_workflow_id)
            subjects = search.search()

            if not subjects:
                logger.warning("No subjects matched the criteria")
                return {"success": False, "message": "No eligible subjects found"}

            selected_subject_id = subjects[0]  # Selection policy: pick first
            subject_data = {"selection": "auto"}  # Placeholder metadata

            # Step 3: Run evaluation DSL
            eval_dsl_id = role_type_data.role_post_removal_dsl_workflow_id
            eval_executor = DSLExecutor(workflow_id=eval_dsl_id)
            eval_input = {"role_type_data": role_type_data.to_dict(), "application_data": application_data}
            eval_output = eval_executor.run(eval_input)

            if not eval_executor.get_final_output(eval_output):
                return {"success": False, "message": "Evaluation failed for selected subject"}

            # Step 4: Create association
            role_id = str(uuid.uuid4())
            role_data = {
                "role_id": role_id,
                "role_type": role_type,
                "role_application_id": role_application_id
            }

            assoc_client = SubjectAssociationClient(selected_subject_id, subject_data, role_data)
            assoc_result = assoc_client.create_association()
            if not assoc_result:
                return {"success": False, "message": "Subject association failed"}

            # Step 5: Update SubjectRolesMapping
            success, subject_entry = self.subject_roles_db.get_by_subject_id(selected_subject_id)
            if success:
                updated_roles = list(set(subject_entry.role_ids + [role_id]))
                self.subject_roles_db.update(selected_subject_id, {"role_ids": updated_roles})
            else:
                new_subject_entry = SubjectRolesMapping(
                    subject_id=selected_subject_id,
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

            # Step 6: Mark position filled
            if role_assignment_type == "dynamic_single_subject":
                self.role_type_db.update(role_type, {"position_filled": True})

            logger.info(f"Auto-selected subject {selected_subject_id} assigned to role {role_id}")
            return {"success": True, "role_id": role_id, "subject_id": selected_subject_id, "association": assoc_result}

        except Exception as e:
            logger.error(f"Criteria-based subject assignment failed: {e}", exc_info=True)
            return {"success": False, "message": str(e)}
