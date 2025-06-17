from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class OrgConstraints:
    message_type: str = ''
    subject_id: str = ''
    dsl_workflow_id: str = ''
    constraint_metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrgConstraints":
        return cls(
            message_type=data.get("message_type", ""),
            subject_id=data.get("subject_id", ""),
            dsl_workflow_id=data.get("dsl_workflow_id", ""),
            constraint_metadata=data.get("constraint_metadata", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_type": self.message_type,
            "subject_id": self.subject_id,
            "dsl_workflow_id": self.dsl_workflow_id,
            "constraint_metadata": self.constraint_metadata
        }
