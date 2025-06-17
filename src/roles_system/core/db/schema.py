from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class SubjectRolesMapping:
    subject_id: str = ''
    role_ids: List[str] = field(default_factory=list)
    subject_type: str = ''
    job_space_id: str = ''

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubjectRolesMapping":
        return cls(
            subject_id=data.get("subject_id", ""),
            role_ids=data.get("role_ids", []),
            subject_type=data.get("subject_type", ""),
            job_space_id=data.get("job_space_id", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "role_ids": self.role_ids,
            "subject_type": self.subject_type,
            "job_space_id": self.job_space_id
        }


@dataclass
class RoleGroupMapping:
    role_id: str = ''
    role_type: str = ''
    group_ids: List[str] = field(default_factory=list)
    job_space_id: str = ''

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RoleGroupMapping":
        return cls(
            role_id=data.get("role_id", ""),
            role_type=data.get("role_type", ""),
            group_ids=data.get("group_ids", []),
            job_space_id=data.get("job_space_id", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_id": self.role_id,
            "role_type": self.role_type,
            "group_ids": self.group_ids,
            "job_space_id": self.job_space_id
        }


@dataclass
class RoleTypeAssignmentMapping:
    role_type: str = ''
    role_assignment_type: str = ''
    role_post_removal_dsl_workflow_id: str = ''
    role_post_addition_dsl_workflow_id: str = ''
    position_filled: bool = False
    job_space_id: str = ''

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RoleTypeAssignmentMapping":
        return cls(
            role_type=data.get("role_type", ""),
            role_assignment_type=data.get("role_assignment_type", ""),
            role_post_removal_dsl_workflow_id=data.get("role_post_removal_dsl_workflow_id", ""),
            role_post_addition_dsl_workflow_id=data.get("role_post_addition_dsl_workflow_id", ""),
            position_filled=data.get("position_filled", False),
            job_space_id=data.get("job_space_id", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_type": self.role_type,
            "role_assignment_type": self.role_assignment_type,
            "role_post_removal_dsl_workflow_id": self.role_post_removal_dsl_workflow_id,
            "role_post_addition_dsl_workflow_id": self.role_post_addition_dsl_workflow_id,
            "position_filled": self.position_filled,
            "job_space_id": self.job_space_id
        }

@dataclass
class GroupConstraintsMapping:
    group_id: str = ''
    group_type: str = ''
    constraint_ids: List[str] = field(default_factory=list)
    job_space_id: str = ''

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GroupConstraintsMapping":
        return cls(
            group_id=data.get("group_id", ""),
            group_type=data.get("group_type", ""),
            constraint_ids=data.get("constraint_ids", []),
            job_space_id=data.get("job_space_id", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "group_id": self.group_id,
            "group_type": self.group_type,
            "constraint_ids": self.constraint_ids,
            "job_space_id": self.job_space_id
        }

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class RoleApplication:
    role_application_id: str = ''
    application_data: Dict[str, Any] = field(default_factory=dict)
    submission_time: int = 0
    status: str = 'pending'  # Valid values: pending, failed, success
    response_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RoleApplication":
        return cls(
            role_application_id=data.get("role_application_id", ""),
            application_data=data.get("application_data", {}),
            submission_time=data.get("submission_time", 0),
            status=data.get("status", "pending"),
            response_data=data.get("response_data", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_application_id": self.role_application_id,
            "application_data": self.application_data,
            "submission_time": self.submission_time,
            "status": self.status,
            "response_data": self.response_data
        }


