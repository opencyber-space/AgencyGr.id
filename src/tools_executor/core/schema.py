from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class OrgFunctions:
    function_id: str = ''
    function_search_tags: List[str] = field(default_factory=list)
    function_metadata: Dict[str, Any] = field(default_factory=dict)
    function_description: str = ''
    function_default_params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrgFunctions":
        return cls(
            function_id=data.get("function_id", ""),
            function_search_tags=data.get("function_search_tags", []),
            function_metadata=data.get("function_metadata", {}),
            function_description=data.get("function_description", ""),
            function_default_params=data.get("function_default_params", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "function_id": self.function_id,
            "function_search_tags": self.function_search_tags,
            "function_metadata": self.function_metadata,
            "function_description": self.function_description,
            "function_default_params": self.function_default_params
        }


@dataclass
class OrgTools:
    tool_id: str = ''
    tool_search_tags: List[str] = field(default_factory=list)
    tool_metadata: Dict[str, Any] = field(default_factory=dict)
    tool_description: str = ''
    tool_default_params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrgTools":
        return cls(
            tool_id=data.get("tool_id", ""),
            tool_search_tags=data.get("tool_search_tags", []),
            tool_metadata=data.get("tool_metadata", {}),
            tool_description=data.get("tool_description", ""),
            tool_default_params=data.get("tool_default_params", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "tool_search_tags": self.tool_search_tags,
            "tool_metadata": self.tool_metadata,
            "tool_description": self.tool_description,
            "tool_default_params": self.tool_default_params
        }