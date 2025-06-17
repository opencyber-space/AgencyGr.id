from flask import Flask, request, jsonify
import logging

from .db.crud import (  
    SubjectAssociationDatabase,
    SubjectContractAssociationDatabase,
    SubjectMessageCommunicationDatabase,
    SubjectAssociationConfigDatabase
)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize DB handlers
subject_association_db = SubjectAssociationDatabase()
subject_contract_association_db = SubjectContractAssociationDatabase()
subject_message_communication_db = SubjectMessageCommunicationDatabase()
subject_association_config_db = SubjectAssociationConfigDatabase()

# Utility functions
def handle_get_by_id(db, key, value):
    success, result = db.get_by_id(key, value)
    if success:
        return jsonify({"success": True, "data": result}), 200
    return jsonify({"success": False, "error": result}), 404

def handle_query(db):
    filters = request.json or {}
    success, result = db.query(filters)
    if success:
        return jsonify({"success": True, "data": result}), 200
    return jsonify({"success": False, "error": result}), 400


# ------------------------------
@app.route("/subject-association/<string:subject_id>", methods=["GET"])
def get_subject_association(subject_id):
    return handle_get_by_id(subject_association_db, "subject_id", subject_id)

@app.route("/subject-association/query", methods=["POST"])
def query_subject_association():
    return handle_query(subject_association_db)

# ------------------------------
# Subject Contract Association APIs
# ------------------------------
@app.route("/subject-contract/<string:subject_id>", methods=["GET"])
def get_subject_contract(subject_id):
    return handle_get_by_id(subject_contract_association_db, "subject_id", subject_id)

@app.route("/subject-contract/query", methods=["POST"])
def query_subject_contract():
    return handle_query(subject_contract_association_db)


@app.route("/subject-message/<string:messaging_id>", methods=["GET"])
def get_subject_message(messaging_id):
    return handle_get_by_id(subject_message_communication_db, "messaging_id", messaging_id)

@app.route("/subject-message/query", methods=["POST"])
def query_subject_message():
    return handle_query(subject_message_communication_db)


@app.route("/subject-config/<string:config_id>", methods=["GET"])
def get_subject_config(config_id):
    return handle_get_by_id(subject_association_config_db, "config_id", config_id)

@app.route("/subject-config/query", methods=["POST"])
def query_subject_config():
    return handle_query(subject_association_config_db)


def run_server():
    app.run(host="0.0.0.0", port=8000, debug=True)
