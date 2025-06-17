from dataclasses import dataclass, field, asdict
from typing import Dict, Any
import uuid


@dataclass
class OrgCreationTask:
    org_creation_task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    org_spec_id: str = ''
    submission_time: int = 0
    status: str = ''
    completion_time: int = 0
    creation_schedule: str = ''
    spec_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrgCreationTask":
        return cls(
            org_creation_task_id=data.get("org_creation_task_id", str(uuid.uuid4())),
            org_spec_id=data.get("org_spec_id", ""),
            submission_time=data.get("submission_time", 0),
            status=data.get("status", ""),
            completion_time=data.get("completion_time", 0),
            creation_schedule=data.get("creation_schedule", ""),
            spec_data=data.get("spec_data", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OrgCreationStage:
    stage_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    org_creation_task_id: str = ''
    stage_type: str = ''
    status: str = ''
    completion_time: str = ''

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrgCreationStage":
        return cls(
            stage_id=data.get("stage_id", str(uuid.uuid4())),
            org_creation_task_id=data.get("org_creation_task_id", ""),
            stage_type=data.get("stage_type", ""),
            status=data.get("status", ""),
            completion_time=data.get("completion_time", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
