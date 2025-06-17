from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class JobSpec:
    task_id: str
    sub_task_id: Optional[str] = ''
    participants: List[str] = field(default_factory=list)
    contract_templates: List[str] = field(default_factory=list)  
    constraints: Dict[str, str] = field(default_factory=dict)     
    metadata: Dict[str, any] = field(default_factory=dict)        
    human_intervention_required: bool = False                     
    context: Dict[str, any] = field(default_factory=dict)       

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "sub_task_id": self.sub_task_id,
            "participants": self.participants,
            "contract_templates": self.contract_templates,
            "constraints": self.constraints,
            "metadata": self.metadata,
            "human_intervention_required": self.human_intervention_required,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'JobSpec':
        return cls(
            task_id=data.get("task_id", ""),
            sub_task_id=data.get("sub_task_id", ""),
            participants=data.get("participants", []),
            contract_templates=data.get("contract_templates", []),
            constraints=data.get("constraints", {}),
            metadata=data.get("metadata", {}),
            human_intervention_required=data.get("human_intervention_required", False),
            context=data.get("context", {}),
        )
