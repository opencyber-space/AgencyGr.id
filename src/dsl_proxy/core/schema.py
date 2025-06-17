from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any


@dataclass
class OrgDSLWorkflows:
    workflow_id: str = ''
    workflow_search_tags: List[str] = field(default_factory=list)
    workflow_metadata: Dict[str, Any] = field(default_factory=dict)
    workflow_description: str = ''
    workflow_default_params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrgDSLWorkflows":
        return cls(
            workflow_id=data.get("workflow_id", ""),
            workflow_search_tags=data.get("workflow_search_tags", []),
            workflow_metadata=data.get("workflow_metadata", {}),
            workflow_description=data.get("workflow_description", ""),
            workflow_default_params=data.get("workflow_default_params", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "workflow_search_tags": self.workflow_search_tags,
            "workflow_metadata": self.workflow_metadata,
            "workflow_description": self.workflow_description,
            "workflow_default_params": self.workflow_default_params
        }
