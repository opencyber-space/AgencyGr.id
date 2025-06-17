import os
import logging
import uuid
from typing import Dict, Any
from flask import Flask, request, jsonify

from dsl_executor import new_dsl_workflow_executor, parse_dsl_output
from .alloc_client import SubjectResourceAllocator
from .alloc_client import QuotaClient

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class AutoscaleDSLExecutor:
    def __init__(self, workflow_id: str, is_remote: bool = False, addons: Dict[str, Any] = None):
        self.workflow_id = workflow_id
        self.workflows_base_uri = os.getenv("WORKFLOWS_API_URL", "http://localhost:8888").rstrip("/")
        self.executor = new_dsl_workflow_executor(
            workflow_id=self.workflow_id,
            workflows_base_uri=self.workflows_base_uri,
            is_remote=is_remote,
            addons=addons or {}
        )
        self.quota_client = QuotaClient()
        self.resource_allocator = SubjectResourceAllocator()
        logger.info(f"AutoscaleDSLExecutor initialized for workflow: {self.workflow_id}")

    def set_parameters(self, new_parameters: Dict[str, Any]):
        logger.info(f"Updating DSL parameters with: {new_parameters}")
        self.executor.parameters.update(new_parameters)

    def execute(self, execution_id: str = None) -> Dict[str, int]:
        execution_id = execution_id or str(uuid.uuid4())
        logger.info(f"Executing DSL workflow {self.workflow_id} with execution ID: {execution_id}")

        try:
            metrics_report = self.quota_client.get_metrics_report()
            input_data = {"metrics": metrics_report}
            logger.debug(f"Input to DSL: {input_data}")

            output = self.executor.execute(input_data)
            result = parse_dsl_output(output)
            logger.info(f"DSL execution result: {result}")

            if isinstance(result, dict) and result:
                for subject_id, new_replicas in result.items():
                    try:
                        logger.info(f"Allocating {new_replicas} replicas for subject {subject_id}")
                        self.resource_allocator.allocate_resources(subject_id, new_replicas)
                    except Exception as e:
                        logger.error(f"Resource allocation failed for {subject_id}: {e}")
            else:
                logger.info("No resource allocation changes returned by DSL.")

            return result
        except Exception as e:
            logger.error(f"DSL execution failed: {e}")
            raise

    # === Flask API Methods ===

    def set_config_api(self):
        try:
            new_config = request.json
            self.set_parameters(new_config)
            return jsonify({"success": True, "message": "Configuration updated"}), 200
        except Exception as e:
            logger.error(f"set_config_api error: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    def get_config_api(self):
        try:
            return jsonify({"success": True, "data": self.executor.parameters}), 200
        except Exception as e:
            logger.error(f"get_config_api error: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    # === Route Registration ===

    def register_routes(self, app: Flask):
        app.add_url_rule('/autoscale/config', view_func=self.set_config_api, methods=['POST'])
        app.add_url_rule('/autoscale/config', view_func=self.get_config_api, methods=['GET'])
        logger.info("AutoscaleDSLExecutor routes registered.")

