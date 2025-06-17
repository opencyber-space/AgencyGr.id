import os
from typing import Dict, Any

from dsl_executor import new_dsl_workflow_executor, parse_dsl_output


class DSLExecutor:
    def __init__(
        self,
        workflow_id: str,
        workflows_base_uri: str = "",
        is_remote: bool = False,
        addons: Dict[str, Any] = None,
    ):
       
        self.workflow_id = workflow_id
        self.workflows_base_uri = workflows_base_uri or os.getenv("WORKFLOWS_API_URL", "http://localhost:8000")
        self.is_remote = is_remote
        self.addons = addons or {}

        self.executor = new_dsl_workflow_executor(
            workflow_id=self.workflow_id,
            workflows_base_uri=self.workflows_base_uri,
            is_remote=self.is_remote,
            addons=self.addons
        )

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
      
        return self.executor.execute(input_data)

    def get_final_output(self, output: Dict[str, Any]) -> Any:
       
        return parse_dsl_output(output)

    def get_module_output(self, output: Dict[str, Any], module_name: str) -> Any:
       
        return parse_dsl_output(output, module_name=module_name)
