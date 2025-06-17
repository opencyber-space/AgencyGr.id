from flask import Flask, request, jsonify
import uuid
import logging

from .executor import RolesExecutor
from .db.crud import *

app = Flask(__name__)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

executor = RolesExecutor()


subject_roles_db = SubjectRolesMappingDatabase()
role_group_db = RoleGroupMappingDatabase()
role_type_db = RoleTypeAssignmentMappingDatabase()
group_constraints_db = GroupConstraintsMappingDatabase()
role_app_db = RoleApplicationDatabase()

@app.route('/submit-role-task', methods=['POST'])
def submit_role_task():
    try:
        payload = request.json
        if not payload or not isinstance(payload, dict):
            return jsonify({"success": False, "message": "Invalid payload"}), 400

        role_application_id = str(uuid.uuid4())
        executor.submit_task(role_application_id, payload)

        return jsonify({"success": True, "role_application_id": role_application_id}), 200

    except Exception as e:
        logger.error(f"Error in /submit-role-task: {e}", exc_info=True)
        return jsonify({"success": False, "message": str(e)}), 500

# ---------------- SubjectRolesMapping ----------------

@app.route('/subject-roles', methods=['POST'])
def query_subject_roles():
    query_filter = request.json or {}
    success, result = subject_roles_db.query(query_filter)
    return jsonify({"success": success, "data": result if success else None, "error": None if success else result})


@app.route('/subject-roles/<string:subject_id>', methods=['GET'])
def get_subject_roles(subject_id):
    success, result = subject_roles_db.get_by_subject_id(subject_id)
    return jsonify({"success": success, "data": result.to_dict() if success else None, "error": None if success else result})


# ---------------- RoleGroupMapping ----------------

@app.route('/role-group', methods=['POST'])
def query_role_group():
    query_filter = request.json or {}
    success, result = role_group_db.query(query_filter)
    return jsonify({"success": success, "data": result if success else None, "error": None if success else result})


@app.route('/role-group/<string:role_id>', methods=['GET'])
def get_role_group(role_id):
    success, result = role_group_db.get_by_role_id(role_id)
    return jsonify({"success": success, "data": result.to_dict() if success else None, "error": None if success else result})


# ---------------- RoleTypeAssignmentMapping ----------------

@app.route('/role-type', methods=['POST'])
def insert_role_type():
    data = request.json or {}
    entry = RoleTypeAssignmentMapping.from_dict(data)
    success, result = role_type_db.insert(entry)
    return jsonify({"success": success, "data": result if success else None, "error": None if success else result})


@app.route('/role-type/<string:role_type>', methods=['PUT'])
def update_role_type(role_type):
    update_fields = request.json or {}
    success, result = role_type_db.update(role_type, update_fields)
    return jsonify({"success": success, "data": result if success else None, "error": None if success else result})


@app.route('/role-type/<string:role_type>', methods=['DELETE'])
def delete_role_type(role_type):
    success, result = role_type_db.delete(role_type)
    return jsonify({"success": success, "data": result if success else None, "error": None if success else result})


@app.route('/role-type', methods=['POST'])
def query_role_types():
    query_filter = request.json or {}
    success, result = role_type_db.query(query_filter)
    return jsonify({"success": success, "data": result if success else None, "error": None if success else result})


@app.route('/role-type/<string:role_type>', methods=['GET'])
def get_role_type(role_type):
    success, result = role_type_db.get_by_role_type(role_type)
    return jsonify({"success": success, "data": result.to_dict() if success else None, "error": None if success else result})


# ---------------- GroupConstraintsMapping ----------------

@app.route('/group-constraints', methods=['POST'])
def insert_group_constraints():
    data = request.json or {}
    entry = GroupConstraintsMapping.from_dict(data)
    success, result = group_constraints_db.insert(entry)
    return jsonify({"success": success, "data": result if success else None, "error": None if success else result})


@app.route('/group-constraints/<string:group_id>', methods=['PUT'])
def update_group_constraints(group_id):
    update_fields = request.json or {}
    success, result = group_constraints_db.update(group_id, update_fields)
    return jsonify({"success": success, "data": result if success else None, "error": None if success else result})


@app.route('/group-constraints/<string:group_id>', methods=['DELETE'])
def delete_group_constraints(group_id):
    success, result = group_constraints_db.delete(group_id)
    return jsonify({"success": success, "data": result if success else None, "error": None if success else result})


@app.route('/group-constraints', methods=['POST'])
def query_group_constraints():
    query_filter = request.json or {}
    success, result = group_constraints_db.query(query_filter)
    return jsonify({"success": success, "data": result if success else None, "error": None if success else result})


@app.route('/group-constraints/<string:group_id>', methods=['GET'])
def get_group_constraints(group_id):
    success, result = group_constraints_db.get_by_group_id(group_id)
    return jsonify({"success": success, "data": result.to_dict() if success else None, "error": None if success else result})


# ---------------- RoleApplication ----------------

@app.route('/role-applications', methods=['POST'])
def query_role_applications():
    query_filter = request.json or {}
    success, result = role_app_db.query(query_filter)
    return jsonify({"success": success, "data": result if success else None, "error": None if success else result})


@app.route('/role-applications/<string:role_application_id>', methods=['GET'])
def get_role_application(role_application_id):
    success, result = role_app_db.get_by_id(role_application_id)
    return jsonify({"success": success, "data": result.to_dict() if success else None, "error": None if success else result})



def run_server():
    app.run(port=5000)
