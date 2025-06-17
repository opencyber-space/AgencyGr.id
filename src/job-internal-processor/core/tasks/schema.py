from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class TaskEntry:
    task_id: str
    task_goal: str
    task_intent: str
    task_priority_value: int
    task_streeability_data: Dict[str, Any] = field(default_factory=dict)
    task_knowledgebase_ptr: Optional[str] = None
    submitter_subject_id: str = ''
    task_op_convertor_dsl_id: Optional[str] = None
    task_execution_dsl: Optional[str] = None
    task_submission_ts: str = ''
    task_completion_timeline: Dict[str, Any] = field(default_factory=dict)
    task_execution_mode: str = ''
    task_behavior_dsl_map: Dict[str, Any] = field(default_factory=dict)
    task_contracts_map: Dict[str, Any] = field(default_factory=dict)
    task_verification_subject_id: str = ''
    task_job_submission_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskEntry":
        return cls(
            task_id=data.get("task_id", ""),
            task_goal=data.get("task_goal", ""),
            task_intent=data.get("task_intent", ""),
            task_priority_value=data.get("task_priority_value", 0),
            task_streeability_data=data.get("task_streeability_data", {}),
            task_knowledgebase_ptr=data.get("task_knowledgebase_ptr"),
            submitter_subject_id=data.get("submitter_subject_id", ""),
            task_op_convertor_dsl_id=data.get("task_op_convertor_dsl_id"),
            task_execution_dsl=data.get("task_execution_dsl"),
            task_submission_ts=data.get("task_submission_ts", ""),
            task_completion_timeline=data.get("task_completion_timeline", {}),
            task_execution_mode=data.get("task_execution_mode", ""),
            task_behavior_dsl_map=data.get("task_behavior_dsl_map", {}),
            task_contracts_map=data.get("task_contracts_map", {}),
            task_verification_subject_id=data.get("task_verification_subject_id", ""),
            task_job_submission_data=data.get("task_job_submission_data", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SubTaskEntry:
    sub_task_id: str
    task_id: str
    sub_task_goal: str
    sub_task_intent: str
    sub_task_priority_value: int
    sub_task_streeability_data: Dict[str, Any] = field(default_factory=dict)
    sub_task_knowledgebase_ptr: Optional[str] = None
    parent_subject_ids: List[str] = field(default_factory=list)
    parent_input_data_ptr: Optional[str] = None
    assigned_subject_ids: List[str] = field(default_factory=list)
    sub_task_submission_ts: str = ''
    sub_task_completion_timeline: Dict[str, Any] = field(default_factory=dict)
    sub_task_behavior_dsl_map: Dict[str, Any] = field(default_factory=dict)
    sub_task_contracts_map: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubTaskEntry":
        return cls(
            sub_task_id=data.get("sub_task_id", ""),
            task_id=data.get("task_id", ""),
            sub_task_goal=data.get("sub_task_goal", ""),
            sub_task_intent=data.get("sub_task_intent", ""),
            sub_task_priority_value=data.get("sub_task_priority_value", 0),
            sub_task_streeability_data=data.get("sub_task_streeability_data", {}),
            sub_task_knowledgebase_ptr=data.get("sub_task_knowledgebase_ptr"),
            parent_subject_ids=data.get("parent_subject_ids", []),
            parent_input_data_ptr=data.get("parent_input_data_ptr"),
            assigned_subject_ids=data.get("assigned_subject_ids", []),
            sub_task_submission_ts=data.get("sub_task_submission_ts", ""),
            sub_task_completion_timeline=data.get("sub_task_completion_timeline", {}),
            sub_task_behavior_dsl_map=data.get("sub_task_behavior_dsl_map", {}),
            sub_task_contracts_map=data.get("sub_task_contracts_map", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)