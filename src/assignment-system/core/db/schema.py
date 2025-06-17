from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class SubjectAssociation:
    subject_id: str = ''
    subject_type: str = ''
    subject_role_id: str = ''
    subject_group_id: str = ''
    subject_role_type: str = ''
    subject_job_space_id: str = ''
    subject_selection_dsl_id: str = ''
    parent_subject_ids: List[str] = field(default_factory=list)
    post_joining_dsl_id: str = ''
    post_leaving_dsl_id: str = ''
    association_payload_data: Dict[str, Any] = field(default_factory=dict)
    association_status: str = ''
    association_time: str = ''

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubjectAssociation":
        return cls(
            subject_id=data.get("subject_id", ""),
            subject_type=data.get("subject_type", ""),
            subject_role_id=data.get("subject_role_id", ""),
            subject_group_id=data.get("subject_group_id", ""),
            subject_role_type=data.get("subject_role_type", ""),
            subject_job_space_id=data.get("subject_job_space_id", ""),
            subject_selection_dsl_id=data.get("subject_selection_dsl_id", ""),
            parent_subject_ids=data.get("parent_subject_ids", []),
            post_joining_dsl_id=data.get("post_joining_dsl_id", ""),
            post_leaving_dsl_id=data.get("post_leaving_dsl_id", ""),
            association_payload_data=data.get("association_payload_data", {}),
            association_status=data.get("association_status", ""),
            association_time=data.get("association_time", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "subject_type": self.subject_type,
            "subject_role_id": self.subject_role_id,
            "subject_group_id": self.subject_group_id,
            "subject_role_type": self.subject_role_type,
            "subject_job_space_id": self.subject_job_space_id,
            "subject_selection_dsl_id": self.subject_selection_dsl_id,
            "parent_subject_ids": self.parent_subject_ids,
            "post_joining_dsl_id": self.post_joining_dsl_id,
            "post_leaving_dsl_id": self.post_leaving_dsl_id,
            "association_payload_data": self.association_payload_data,
            "association_status": self.association_status,
            "association_time": self.association_time
        }



@dataclass
class SubjectContractAssociation:
    subject_id: str = ''
    subject_contract_type: str = ''
    subject_contract_id: str = ''
    job_space_id: str = ''

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubjectContractAssociation":
        return cls(
            subject_id=data.get("subject_id", ""),
            subject_contract_type=data.get("subject_contract_type", ""),
            subject_contract_id=data.get("subject_contract_id", ""),
            job_space_id=data.get("job_space_id", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "subject_contract_type": self.subject_contract_type,
            "subject_contract_id": self.subject_contract_id,
            "job_space_id": self.job_space_id
        }

@dataclass
class SubjectMessageCommunication:
    messaging_id: str = ''
    subject_id: str = ''
    message_type: str = ''
    message_sub_type: str = ''
    channel_id: str = ''
    input_message_convertor_id: str = ''
    output_message_convertor_id: str = ''

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubjectMessageCommunication":
        return cls(
            messaging_id=data.get("messaging_id", ""),
            subject_id=data.get("subject_id", ""),
            message_type=data.get("message_type", ""),
            message_sub_type=data.get("message_sub_type", ""),
            channel_id=data.get("channel_id", ""),
            input_message_convertor_id=data.get("input_message_convertor_id", ""),
            output_message_convertor_id=data.get("output_message_convertor_id", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "messaging_id": self.messaging_id,
            "subject_id": self.subject_id,
            "message_type": self.message_type,
            "message_sub_type": self.message_sub_type,
            "channel_id": self.channel_id,
            "input_message_convertor_id": self.input_message_convertor_id,
            "output_message_convertor_id": self.output_message_convertor_id
        }

@dataclass
class SubjectAssociationConfig:
    config_id: str = ''
    subject_id: str = ''
    job_space_id: str = ''
    config_name: str = ''
    config_value: str = ''

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubjectAssociationConfig":
        return cls(
            config_id=data.get("config_id", ""),
            subject_id=data.get("subject_id", ""),
            job_space_id=data.get("job_space_id", ""),
            config_name=data.get("config_name", ""),
            config_value=data.get("config_value", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "config_id": self.config_id,
            "subject_id": self.subject_id,
            "job_space_id": self.job_space_id,
            "config_name": self.config_name,
            "config_value": self.config_value
        }
