import os
import logging
from flask import Flask, request, jsonify

from .initiator.spec import JobSpec
from .contracts_db import ContractsDBClient
from .job_contracts import JobSpaceContractsMappingDB
from .subject_intervention import SessionClient
from .job_contracts import SubjectInterventionSystem
from .job_contracts import JobSpaceContractGeneratorDSLExecutor
from .ql import mount_graphql

from .db import JobSpaceContractsMapping, JobSpaceContractsMappingDB

# Setup
app = Flask(__name__)
mount_graphql(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


CONTRACTS_API_URL = os.getenv("CONTRACTS_API_URL", "http://localhost:5001")
WORKFLOW_REGISTRY_URL = os.getenv(
    "WORKFLOW_REGISTRY_URL", "http://localhost:6000")
DSL_WORKFLOW_ID = os.getenv("DSL_WORKFLOW_ID", "sample_workflow")
INTERVENTION_API_URL = os.getenv(
    "INTERVENTION_API_URL", "http://localhost:7000")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")


contracts_client = ContractsDBClient(base_url=CONTRACTS_API_URL)
mapping_db = JobSpaceContractsMappingDB(mongo_uri=MONGO_URI)

session_client = SessionClient(api_base_url=INTERVENTION_API_URL)
intervention_system = SubjectInterventionSystem(session_client=session_client)

dsl_executor = JobSpaceContractGeneratorDSLExecutor(
    workflow_id=DSL_WORKFLOW_ID,
    workflows_base_uri=WORKFLOW_REGISTRY_URL,
    contracts_client=contracts_client,
    mapping_db=mapping_db,
    intervention_system=intervention_system,
    is_remote=False,
    addons={"incr": 2}
)

# --- API Route ---


@app.route("/job/contract/generate", methods=["POST"])
def generate_job_contract():
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "Empty request body"}), 400

        spec = JobSpec.from_dict(data)
        logger.info(
            f"Received job spec: task_id={spec.task_id}, sub_task_id={spec.sub_task_id}")

        mappings = dsl_executor.execute(spec)

        return jsonify({
            "success": True,
            "message": "Contracts generated and mapped successfully",
            "mapping": [m.to_dict() for m in mappings]
        }), 200

    except Exception as e:
        logger.error(f"Job contract generation failed: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/mappings", methods=["POST"])
def create_mapping():
    try:
        data = request.json
        mapping = JobSpaceContractsMapping.from_dict(data)
        key = mapping_db.create(mapping)
        return jsonify({"success": True, "key": key}), 201
    except Exception as e:
        logger.error(f"Create mapping failed: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/mappings/<string:key>", methods=["GET"])
def get_mapping(key):
    try:
        result = mapping_db.get(key)
        if not result:
            return jsonify({"success": False, "error": "Mapping not found"}), 404
        return jsonify({"success": True, "mapping": result.to_dict()}), 200
    except Exception as e:
        logger.error(f"Get mapping failed: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/mappings/<string:key>", methods=["PUT"])
def update_mapping(key):
    try:
        data = request.json
        mapping = JobSpaceContractsMapping.from_dict(data)
        if mapping.key != key:
            return jsonify({"success": False, "error": "Key mismatch"}), 400
        updated = mapping_db.update(mapping)
        return jsonify({"success": True, "mapping": updated.to_dict()}), 200
    except Exception as e:
        logger.error(f"Update mapping failed: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/mappings/<string:key>", methods=["DELETE"])
def delete_mapping(key):
    try:
        success = mapping_db.delete(key)
        if not success:
            return jsonify({"success": False, "error": "Mapping not found"}), 404
        return jsonify({"success": True, "message": "Deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Delete mapping failed: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/mappings", methods=["GET"])
def list_mappings():
    try:
        all_mappings = mapping_db.list_all()
        return jsonify({
            "success": True,
            "mappings": [m.to_dict() for m in all_mappings]
        }), 200
    except Exception as e:
        logger.error(f"List mappings failed: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/mappings/by-task/<string:task_id>", methods=["GET"])
def get_mappings_by_task_id(task_id):
    try:
        results = mapping_db.list_all()
        filtered = [
            m.to_dict() for m in results if m.task_id == task_id
        ]
        return jsonify({"success": True, "mappings": filtered}), 200
    except Exception as e:
        logger.error(f"Failed to get mappings by task_id={task_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/mappings/by-task/<string:task_id>/<string:sub_task_id>", methods=["GET"])
def get_mapping_by_task_and_subtask(task_id, sub_task_id):
    try:
        key = f"{task_id}::{sub_task_id}" if sub_task_id else task_id
        result = mapping_db.get(key)
        if not result:
            return jsonify({"success": False, "error": "Mapping not found"}), 404
        return jsonify({"success": True, "mapping": result.to_dict()}), 200
    except Exception as e:
        logger.error(f"Failed to get mapping for task={task_id}, subtask={sub_task_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/mappings/query", methods=["POST"])
def query_mappings():
    try:
        query = request.json or {}
        if not isinstance(query, dict):
            return jsonify({"success": False, "error": "Query must be a JSON object"}), 400

        logger.info(f"Received query: {query}")
        cursor = mapping_db.collection.find(query)

        mappings = [JobSpaceContractsMapping.from_dict(doc).to_dict() for doc in cursor]
        return jsonify({"success": True, "results": mappings}), 200

    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


def run_server():
    app.run(host='0.0.0.0', port=5000)