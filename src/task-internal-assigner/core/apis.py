from flask import Flask, request, jsonify
import logging
from .schema import TaskEntry
from .head_agent import HeadAgentAssociationModule
from .config import OrgExecutionConfigProvider

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ProcessTaskAPI")

head_agent_associator = HeadAgentAssociationModule()
config_provider = OrgExecutionConfigProvider()

@app.route("/internal/process-task", methods=["POST"])
def process_task():
    try:
        payload = request.json
        if not payload or "type" not in payload or "data" not in payload:
            return jsonify({"error": "Missing 'type' or 'data' in payload"}), 400

        task_type = payload["type"]
        data = payload["data"]

        if task_type == "task":
            task = TaskEntry.from_dict(data)
            result_subject_id = head_agent_associator.associate_and_dispatch(task)

            if result_subject_id:
                return jsonify({"status": "assigned", "subject_id": result_subject_id}), 200
            else:
                return jsonify({"error": "No agent could be assigned"}), 422

        elif task_type == "sub_task":
            # Future: implement SubTask support
            return jsonify({"error": "Sub-task processing not implemented yet"}), 501

        else:
            return jsonify({"error": f"Unknown task type: {task_type}"}), 400

    except Exception as e:
        logger.exception("Failed to process task.")
        return jsonify({"error": str(e)}), 500

@app.route("/org-config/<org_id>/<key>", methods=["GET"])
def get_org_config(org_id, key):
    try:
        value = config_provider.get(org_id, key)
        if value is not None:
            return jsonify({"success": True, "key": key, "value": value})
        return jsonify({"success": False, "error": f"Key '{key}' not found for org {org_id}"}), 404
    except Exception as e:
        logger.exception("Error retrieving config")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/org-config/<org_id>/<key>", methods=["POST"])
def set_org_config(org_id, key):
    try:
        body = request.json
        if not body or "value" not in body:
            return jsonify({"success": False, "error": "Missing 'value' in request body"}), 400

        success = config_provider.set(org_id, key, body["value"])
        return jsonify({"success": success})
    except Exception as e:
        logger.exception("Error setting config")
        return jsonify({"success": False, "error": str(e)}), 500


def run_server():
    app.run(port=7000, debug=True)
