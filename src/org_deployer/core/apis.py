from flask import Flask, request, jsonify
from .schema import OrgCreationTask, OrgCreationStage
from .crud import OrgCreationTaskDatabase, OrgCreationStageDatabase
from .processor import (
    submit_task_for_creation,
    submit_task_resume,
    remove_org,
    StatusUpdateSystem,
)

import logging

app = Flask(__name__)
logger = logging.getLogger(__name__)

org_task_db = OrgCreationTaskDatabase()
org_stage_db = OrgCreationStageDatabase()
status_updater = StatusUpdateSystem()



@app.route('/org-task', methods=['POST'])
def create_org_task():
    try:
        task_data = request.json
        task = OrgCreationTask.from_dict(task_data)
        success, result = org_task_db.insert(task)
        if success:
            return jsonify({"success": True, "data": {"message": "Org task created", "id": result}}), 201
        else:
            return jsonify({"success": False, "error": result}), 400
    except Exception as e:
        logger.error(f"create_org_task error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/org-task/<string:task_id>', methods=['GET'])
def get_org_task(task_id):
    try:
        success, result = org_task_db.get_by_id(task_id)
        if success:
            return jsonify({"success": True, "data": result.to_dict()}), 200
        else:
            return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        logger.error(f"get_org_task error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/org-task/<string:task_id>', methods=['PUT'])
def update_org_task(task_id):
    try:
        update_data = request.json
        success, result = org_task_db.update(task_id, update_data)
        if success:
            return jsonify({"success": True, "data": {"message": "Org task updated"}}), 200
        else:
            return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        logger.error(f"update_org_task error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/org-task/<string:task_id>', methods=['DELETE'])
def delete_org_task(task_id):
    try:
        success, result = org_task_db.delete(task_id)
        if success:
            return jsonify({"success": True, "data": {"message": "Org task deleted"}}), 200
        else:
            return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        logger.error(f"delete_org_task error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/org-tasks', methods=['POST'])
def query_org_tasks():
    try:
        query_filter = request.json
        success, results = org_task_db.query(query_filter)
        if success:
            return jsonify({"success": True, "data": results}), 200
        else:
            return jsonify({"success": False, "error": results}), 400
    except Exception as e:
        logger.error(f"query_org_tasks error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/org-stage', methods=['POST'])
def create_org_stage():
    try:
        stage_data = request.json
        stage = OrgCreationStage.from_dict(stage_data)
        success, result = org_stage_db.insert(stage)
        if success:
            return jsonify({"success": True, "data": {"message": "Stage created", "id": result}}), 201
        else:
            return jsonify({"success": False, "error": result}), 400
    except Exception as e:
        logger.error(f"create_org_stage error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/org-stage/<string:stage_id>', methods=['GET'])
def get_org_stage(stage_id):
    try:
        success, result = org_stage_db.get_by_id(stage_id)
        if success:
            return jsonify({"success": True, "data": result.to_dict()}), 200
        else:
            return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        logger.error(f"get_org_stage error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/org-stage/<string:stage_id>', methods=['PUT'])
def update_org_stage(stage_id):
    try:
        update_data = request.json
        success, result = org_stage_db.update(stage_id, update_data)
        if success:
            return jsonify({"success": True, "data": {"message": "Stage updated"}}), 200
        else:
            return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        logger.error(f"update_org_stage error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/org-stage/<string:stage_id>', methods=['DELETE'])
def delete_org_stage(stage_id):
    try:
        success, result = org_stage_db.delete(stage_id)
        if success:
            return jsonify({"success": True, "data": {"message": "Stage deleted"}}), 200
        else:
            return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        logger.error(f"delete_org_stage error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/org-stages', methods=['POST'])
def query_org_stages():
    try:
        query_filter = request.json
        success, results = org_stage_db.query(query_filter)
        if success:
            return jsonify({"success": True, "data": results}), 200
        else:
            return jsonify({"success": False, "error": results}), 400
    except Exception as e:
        logger.error(f"query_org_stages error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/org-creation/submit/<string:org_creation_task_id>', methods=['POST'])
def api_submit_org_creation(org_creation_task_id):
    try:
        submit_task_for_creation(org_creation_task_id)
        return jsonify({"success": True, "message": "Org creation submitted"}), 200
    except Exception as e:
        logger.error(f"submit_task_for_creation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/org-creation/resume/<string:stage_id>', methods=['POST'])
def api_resume_org_creation(stage_id):
    try:
        submit_task_resume(stage_id)
        return jsonify({"success": True, "message": f"Org creation resumed from stage {stage_id}"}), 200
    except Exception as e:
        logger.error(f"submit_task_resume error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/org-creation/remove/<string:org_creation_task_id>', methods=['POST'])
def api_remove_org(org_creation_task_id):
    try:
        remove_org(org_creation_task_id)
        return jsonify({"success": True, "message": f"Org removal initiated for task {org_creation_task_id}"}), 200
    except Exception as e:
        logger.error(f"remove_org error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/org-creation/status-update/<string:stage_id>', methods=['POST'])
def api_update_stage_status(stage_id):
    try:
        data = request.json
        new_status = data.get("status")
        completion_time = data.get("completion_time", "")

        if not new_status:
            return jsonify({"success": False, "error": "Missing 'status' in request body"}), 400

        updated = status_updater.update_stage_status(stage_id, new_status, completion_time)
        if updated:
            return jsonify({"success": True, "message": f"Stage {stage_id} updated to {new_status}"}), 200
        else:
            return jsonify({"success": False, "message": "Stage update failed"}), 400

    except Exception as e:
        logger.error(f"update_stage_status error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500