from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class APIRoleAssociation:
    api_route: str
    role_id: str
    group_id: str

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "APIRoleAssociation":
        return APIRoleAssociation(
            api_route=data.get("api_route", ""),
            role_id=data.get("role_id", ""),
            group_id=data.get("group_id", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_route": self.api_route,
            "role_id": self.role_id,
            "group_id": self.group_id
        }


@dataclass
class APIConstraintMap:
    api_route: str
    constraints_map: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "APIConstraintMap":
        return APIConstraintMap(
            api_route=data.get("api_route", ""),
            constraints_map=data.get("constraints_map", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_route": self.api_route,
            "constraints_map": self.constraints_map
        }
