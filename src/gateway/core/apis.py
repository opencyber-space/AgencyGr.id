from flask import Flask, request, jsonify
import logging

from .cache import AccessCache, CacheManager
from .mgmt_db import OrgAccessControlDB
from .rev_proxy import ReverseProxyInput
from .rev_proxy import ReverseProxyOutput
from .checker import RevProxyConstraintsChecker
from .schema import APIConstraintMap, APIRoleAssociation

logger = logging.getLogger("OrgAccessControlAPI")
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

db = OrgAccessControlDB()
cache = AccessCache(db=db)
checker = RevProxyConstraintsChecker(cache=cache, db=db)
cache_manager = CacheManager(cache, db)
output = ReverseProxyOutput()
proxy_input = ReverseProxyInput(constraint_checker=checker, proxy_output=output)

@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy_handler(path):
    return proxy_input.handle_request(request, f"/{path}")


@app.route("/internal/cache/init", methods=["POST"])
def initialize_cache():
    if cache_manager.initialize_cache():
        return jsonify({"status": "Cache initialized from DB"}), 200
    return jsonify({"error": "Failed to initialize cache"}), 500


@app.route("/internal/cache/flush", methods=["POST"])
def flush_cache():
    if cache_manager.flush_entire_cache():
        return jsonify({"status": "Cache flushed"}), 200
    return jsonify({"error": "Failed to flush cache"}), 500


@app.route("/internal/cache/refresh/<path:api_route>", methods=["POST"])
def refresh_cache(api_route):
    if cache_manager.refresh_cache_for_route("/" + api_route):
        return jsonify({"status": f"Cache refreshed for /{api_route}"}), 200
    return jsonify({"error": "Failed to refresh cache"}), 500


@app.route("/internal/cache/delete/<path:api_route>", methods=["POST"])
def delete_cache(api_route):
    if cache_manager.delete_cache_for_route("/" + api_route):
        return jsonify({"status": f"Cache deleted for /{api_route}"}), 200
    return jsonify({"error": "Failed to delete cache"}), 500


# ----------------------------------------
# DB CRUD: APIRoleAssociation
# ----------------------------------------

@app.route("/internal/db/role-association", methods=["POST"])
def create_role_association():
    try:
        obj = APIRoleAssociation.from_dict(request.json)
        db.create_role_association(obj)
        return jsonify({"status": "created", "api_route": obj.api_route}), 201
    except Exception as e:
        logger.exception("Failed to create role association")
        return jsonify({"error": str(e)}), 500


@app.route("/internal/db/role-association/<path:api_route>", methods=["GET"])
def get_role_association(api_route):
    try:
        result = db.get_role_association("/" + api_route)
        if not result:
            return jsonify({"error": "Not found"}), 404
        return jsonify(result.to_dict()), 200
    except Exception as e:
        logger.exception("Failed to get role association")
        return jsonify({"error": str(e)}), 500


@app.route("/internal/db/role-association/<path:api_route>", methods=["PUT"])
def update_role_association(api_route):
    try:
        updated = request.json
        if db.update_role_association("/" + api_route, updated):
            return jsonify({"status": "updated"}), 200
        return jsonify({"error": "No record updated"}), 404
    except Exception as e:
        logger.exception("Failed to update role association")
        return jsonify({"error": str(e)}), 500


@app.route("/internal/db/role-association/<path:api_route>", methods=["DELETE"])
def delete_role_association(api_route):
    try:
        if db.delete_role_association("/" + api_route):
            return jsonify({"status": "deleted"}), 200
        return jsonify({"error": "Not found"}), 404
    except Exception as e:
        logger.exception("Failed to delete role association")
        return jsonify({"error": str(e)}), 500




@app.route("/internal/db/constraint", methods=["POST"])
def create_constraint_map():
    try:
        obj = APIConstraintMap.from_dict(request.json)
        db.create_constraint(obj)
        return jsonify({"status": "created", "api_route": obj.api_route}), 201
    except Exception as e:
        logger.exception("Failed to create constraint map")
        return jsonify({"error": str(e)}), 500


@app.route("/internal/db/constraint/<path:api_route>", methods=["GET"])
def get_constraint_map(api_route):
    try:
        result = db.get_constraint("/" + api_route)
        if not result:
            return jsonify({"error": "Not found"}), 404
        return jsonify(result.to_dict()), 200
    except Exception as e:
        logger.exception("Failed to get constraint map")
        return jsonify({"error": str(e)}), 500


@app.route("/internal/db/constraint/<path:api_route>", methods=["PUT"])
def update_constraint_map(api_route):
    try:
        updated = request.json
        if db.update_constraint("/" + api_route, updated):
            return jsonify({"status": "updated"}), 200
        return jsonify({"error": "No record updated"}), 404
    except Exception as e:
        logger.exception("Failed to update constraint map")
        return jsonify({"error": str(e)}), 500


@app.route("/internal/db/constraint/<path:api_route>", methods=["DELETE"])
def delete_constraint_map(api_route):
    try:
        if db.delete_constraint("/" + api_route):
            return jsonify({"status": "deleted"}), 200
        return jsonify({"error": "Not found"}), 404
    except Exception as e:
        logger.exception("Failed to delete constraint map")
        return jsonify({"error": str(e)}), 500

def run_server():
    app.run(host='0.0.0.0', port=7000)