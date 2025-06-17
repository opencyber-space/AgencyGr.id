from flask import Flask, request, jsonify
from .processor import direct_task_assign  
from .processor import JobBiddingClient
from .processor import JobWinningHandler

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)


@app.route("/jobs/direct-assign", methods=["POST"])
def api_direct_assign():
    try:
        job_data = request.get_json()
        result = direct_task_assign(job_data)
        if result.get("success"):
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error in direct assignment API: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


def main():
    logger.info("Initializing job automation components...")

    # Start bidding client
    bidding_client = JobBiddingClient()
    bidding_client.start()
    logger.info("JobBiddingClient started.")

    # Start winning handler
    winning_handler = JobWinningHandler()
    winning_handler.start()
    logger.info("JobWinningHandler started.")

    # Start Flask app
    app.run(host="0.0.0.0", port=8000)

