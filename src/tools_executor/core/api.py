from flask import Flask, request, jsonify
import logging

from .crud import OrgTools, OrgFunctions, OrgToolsDatabase, OrgFunctionsDatabase
from .registry import register_tool_entry, register_function_entry

app = Flask(__name__)
logger = logging.getLogger(__name__)

tool_db = OrgToolsDatabase()
function_db = OrgFunctionsDatabase()

# -------------------------------
# Tool APIs
# -------------------------------

@app.route('/tool', methods=['POST'])
def create_tool():
    try:
        data = request.json
        tool = OrgTools.from_dict(data)
        success, result = tool_db.insert(tool)
        if success:
            return jsonify({"success": True, "data": {"message": "Tool created", "id": result}}), 201
        else:
            return jsonify({"success": False, "error": result}), 400
    except Exception as e:
        logger.error(f"create_tool error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/tool/<string:tool_id>', methods=['GET'])
def get_tool(tool_id):
    try:
        success, result = tool_db.get_by_tool_id(tool_id)
        if success:
            return jsonify({"success": True, "data": result.to_dict()}), 200
        else:
            return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        logger.error(f"get_tool error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/tool/<string:tool_id>', methods=['PUT'])
def update_tool(tool_id):
    try:
        update_data = request.json
        success, result = tool_db.update(tool_id, update_data)
        if success:
            return jsonify({"success": True, "data": {"message": "Tool updated"}}), 200
        else:
            return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        logger.error(f"update_tool error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/tool/<string:tool_id>', methods=['DELETE'])
def delete_tool(tool_id):
    try:
        success, result = tool_db.delete(tool_id)
        if success:
            return jsonify({"success": True, "data": {"message": "Tool deleted"}}), 200
        else:
            return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        logger.error(f"delete_tool error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/tools', methods=['POST'])
def query_tools():
    try:
        query_filter = request.json
        success, results = tool_db.query(query_filter)
        if success:
            return jsonify({"success": True, "data": results}), 200
        else:
            return jsonify({"success": False, "error": results}), 400
    except Exception as e:
        logger.error(f"query_tools error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/tool/register/<string:tool_id>', methods=['POST'])
def register_tool(tool_id):
    try:
        success, result = register_tool_entry(tool_id)
        if success:
            return jsonify({"success": True, "message": result}), 201
        else:
            return jsonify({"success": False, "error": result}), 400
    except Exception as e:
        logger.error(f"register_tool error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------
# Function APIs
# -------------------------------

@app.route('/function', methods=['POST'])
def create_function():
    try:
        data = request.json
        fn = OrgFunctions.from_dict(data)
        success, result = function_db.insert(fn)
        if success:
            return jsonify({"success": True, "data": {"message": "Function created", "id": result}}), 201
        else:
            return jsonify({"success": False, "error": result}), 400
    except Exception as e:
        logger.error(f"create_function error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/function/<string:function_id>', methods=['GET'])
def get_function(function_id):
    try:
        success, result = function_db.get_by_function_id(function_id)
        if success:
            return jsonify({"success": True, "data": result.to_dict()}), 200
        else:
            return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        logger.error(f"get_function error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/function/<string:function_id>', methods=['PUT'])
def update_function(function_id):
    try:
        update_data = request.json
        success, result = function_db.update(function_id, update_data)
        if success:
            return jsonify({"success": True, "data": {"message": "Function updated"}}), 200
        else:
            return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        logger.error(f"update_function error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/function/<string:function_id>', methods=['DELETE'])
def delete_function(function_id):
    try:
        success, result = function_db.delete(function_id)
        if success:
            return jsonify({"success": True, "data": {"message": "Function deleted"}}), 200
        else:
            return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        logger.error(f"delete_function error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/functions', methods=['POST'])
def query_functions():
    try:
        query_filter = request.json
        success, results = function_db.query(query_filter)
        if success:
            return jsonify({"success": True, "data": results}), 200
        else:
            return jsonify({"success": False, "error": results}), 400
    except Exception as e:
        logger.error(f"query_functions error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/function/register/<string:function_id>', methods=['POST'])
def register_function(function_id):
    try:
        success, result = register_function_entry(function_id)
        if success:
            return jsonify({"success": True, "message": result}), 201
        else:
            return jsonify({"success": False, "error": result}), 400
    except Exception as e:
        logger.error(f"register_function error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


