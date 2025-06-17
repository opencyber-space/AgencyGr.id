from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class OrgResourceQuota:
    subject_id: str = ''
    quota_id: str = ''
    allocation_info: str = ''
    replica_count: str = ''

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrgResourceQuota":
        return cls(
            subject_id=data.get("subject_id", ""),
            quota_id=data.get("quota_id", ""),
            allocation_info=data.get("allocation_info", ""),
            replica_count=data.get("replica_count", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "quota_id": self.quota_id,
            "allocation_info": self.allocation_info,
            "replica_count": self.replica_count
        }
