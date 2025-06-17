from flask import Flask, request, jsonify
import logging

from .schema import OrgConstraints
from .db import OrgConstraintsDatabase
from constraints_manager import ConstraintsManager

app = Flask(__name__)
logger = logging.getLogger(__name__)
db = OrgConstraintsDatabase()
executor = ConstraintsManager()

@app.route("/constraint", methods=["POST"])
def create_constraint():
    try:
        data = request.json
        constraint = OrgConstraints.from_dict(data)
        success, result = db.insert(constraint)
        if success:
            return jsonify({"success": True, "data": {"message": "Constraint registered", "id": result}}), 201
        return jsonify({"success": False, "error": result}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/constraint/<string:message_type>", methods=["GET"])
def get_constraint(message_type):
    try:
        success, result = db.get_by_message_type(message_type)
        if success:
            return jsonify({"success": True, "data": result.to_dict()}), 200
        return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/constraint/<string:message_type>", methods=["PUT"])
def update_constraint(message_type):
    try:
        updates = request.json
        success, result = db.update(message_type, updates)
        if success:
            return jsonify({"success": True, "message": "Constraint updated"}), 200
        return jsonify({"success": False, "error": result}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/constraint/<string:message_type>", methods=["DELETE"])
def delete_constraint(message_type):
    try:
        success, result = db.delete(message_type)
        if success:
            return jsonify({"success": True, "message": "Constraint deleted"}), 200
        return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/constraints", methods=["POST"])
def query_constraints():
    try:
        filters = request.json
        success, result = db.query(filters)
        if success:
            return jsonify({"success": True, "data": result}), 200
        return jsonify({"success": False, "error": result}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/constraint/execute/<string:message_type>", methods=["POST"])
def execute_constraint(message_type):
    try:
        payload = request.json
        subject_id = payload["subject_id"]
        dsl_workflow_id = payload["dsl_workflow_id"]
        input_data = payload["input_data"]

        result = executor.check_constraint_and_convert_packet(
            message_type=message_type,
            input_data=input_data,
            subject_id=subject_id,
            dsl_workflow_id=dsl_workflow_id
        )
        return jsonify({"success": True, "output": result}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/constraint/metadata/<string:message_type>", methods=["GET"])
def get_constraint_metadata(message_type):
    try:
        result = executor.get_metadata(message_type)
        return jsonify({"success": True, "metadata": result}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
