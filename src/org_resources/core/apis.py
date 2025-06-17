from flask import Flask, request, jsonify
import logging
from .schema import OrgResourceQuota
from .metrics import MetricsReport
from .crud import OrgResourceQuotaDatabase 

app = Flask(__name__)
logger = logging.getLogger(__name__)
quota_db = OrgResourceQuotaDatabase()

report_generator = MetricsReport()

@app.route('/quota', methods=['POST'])
def create_resource_quota():
    try:
        data = request.json
        quota = OrgResourceQuota.from_dict(data)
        success, result = quota_db.insert(quota)
        if success:
            return jsonify({"success": True, "data": {"message": "Resource quota created", "id": result}}), 201
        else:
            return jsonify({"success": False, "error": result}), 400
    except Exception as e:
        logger.error(f"create_resource_quota error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/quota/<string:quota_id>', methods=['GET'])
def get_resource_quota(quota_id):
    try:
        success, result = quota_db.get_by_quota_id(quota_id)
        if success:
            return jsonify({"success": True, "data": result.to_dict()}), 200
        else:
            return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        logger.error(f"get_resource_quota error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/quota/<string:quota_id>', methods=['PUT'])
def update_resource_quota(quota_id):
    try:
        update_data = request.json
        success, result = quota_db.update(quota_id, update_data)
        if success:
            return jsonify({"success": True, "data": {"message": "Resource quota updated"}}), 200
        else:
            return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        logger.error(f"update_resource_quota error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/quota/<string:quota_id>', methods=['DELETE'])
def delete_resource_quota(quota_id):
    try:
        success, result = quota_db.delete(quota_id)
        if success:
            return jsonify({"success": True, "data": {"message": "Resource quota deleted"}}), 200
        else:
            return jsonify({"success": False, "error": result}), 404
    except Exception as e:
        logger.error(f"delete_resource_quota error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/quotas', methods=['POST'])
def query_resource_quotas():
    try:
        query_filter = request.json
        success, results = quota_db.query(query_filter)
        if success:
            return jsonify({"success": True, "data": results}), 200
        else:
            return jsonify({"success": False, "error": results}), 400
    except Exception as e:
        logger.error(f"query_resource_quotas error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/metrics/report', methods=['GET'])
def get_metrics_report():
    try:
        report = report_generator.generate_report()
        return jsonify({"success": True, "data": report}), 200
    except Exception as e:
        logger.error(f"get_metrics_report error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500