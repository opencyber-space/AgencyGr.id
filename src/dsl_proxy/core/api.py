from flask import Flask, request, jsonify
import logging

from .dsl import register_dsl_entry
from .crud import OrgDSLWorkflows, OrgDSLWorkflowsDatabase 

app = Flask(__name__)
logger = logging.getLogger(__name__)
dsl_db = OrgDSLWorkflowsDatabase()

@app.route('/dsl', methods=['POST'])
def create_dsl_workflow():
    try:
        data = request.json
        workflow = OrgDSLWorkflows.from_dict(data)
        success, result = dsl_db.insert(workflow)
        if success:
            return jsonify({"success": True, "data": {"message": "DSL workflow created", "id": result}}), 201
        else:
            return jsonify({"success": False, "error": result}), 400
    except Exception as e:
        logger.error(f"create_dsl_workflow error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/dsl/<string:workflow_id>', methods=['GET'])
def get_dsl_workflow(workflow_id):
    try:
        success, result = dsl_db.get_by_workflow_id(workflow_id)
        if success:
            return jsonify({"success": True, "data": result.to_dict()}), 200
        else:
            return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        logger.error(f"get_dsl_workflow error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/dsl/<string:workflow_id>', methods=['PUT'])
def update_dsl_workflow(workflow_id):
    try:
        update_data = request.json
        success, result = dsl_db.update(workflow_id, update_data)
        if success:
            return jsonify({"success": True, "data": {"message": "DSL workflow updated"}}), 200
        else:
            return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        logger.error(f"update_dsl_workflow error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/dsl/<string:workflow_id>', methods=['DELETE'])
def delete_dsl_workflow(workflow_id):
    try:
        success, result = dsl_db.delete(workflow_id)
        if success:
            return jsonify({"success": True, "data": {"message": "DSL workflow deleted"}}), 200
        else:
            return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        logger.error(f"delete_dsl_workflow error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/dsls', methods=['POST'])
def query_dsl_workflows():
    try:
        query_filter = request.json
        success, results = dsl_db.query(query_filter)
        if success:
            return jsonify({"success": True, "data": results}), 200
        else:
            return jsonify({"success": False, "error": results}), 400
    except Exception as e:
        logger.error(f"query_dsl_workflows error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/dsl/register/<string:dsl_id>', methods=['POST'])
def api_register_dsl_entry(dsl_id):
    try:
        success, result = register_dsl_entry(dsl_id)
        if success:
            return jsonify({"success": True, "message": result}), 201
        else:
            return jsonify({"success": False, "error": result}), 400
    except Exception as e:
        logger.error(f"api_register_dsl_entry error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500