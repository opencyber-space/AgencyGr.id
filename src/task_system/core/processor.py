from .utils import TaskCreationClient, DSLExecutor, BidSubmissionClient, JobInvitesListener, BidsWinnerListener
import uuid
import time
import os
import threading
import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def direct_task_assign(job_data: Dict[str, Any]) -> Dict[str, Any]:

    required_fields = [
        "jobId", "jobGoal", "jobObjectives", "jobPriorityValue",
        "jobCompletionMode", "submittedBy", "jobOutputTemplateId",
        "jobVerificationSubjectIds"
    ]

    # Step 1: Validate input
    missing_fields = [f for f in required_fields if f not in job_data]
    if missing_fields:
        return {
            "success": False,
            "message": f"Missing required job fields: {', '.join(missing_fields)}"
        }

    # Step 2: Execute DSL Workflow to authorize job
    workflow_id = os.getenv("ORG_MANUAL_JOB_ASSIGNMENT_DSL_WORKFLOW_ID")
    if not workflow_id:
        return {"success": False, "message": "Manual assignment DSL workflow ID not set in env"}

    try:
        dsl = DSLExecutor(workflow_id=workflow_id)
        dsl_output = dsl.run({"job_data": job_data})
        result = dsl.get_final_output(dsl_output)

        if not result.get("allowed", False):
            return {"success": False, "message": "Job not permitted by DSL evaluation"}

        # Step 3: Convert job to task structure
        task_id = f"task-{uuid.uuid4()}"
        task_data = {
            "task_id": task_id,
            "task_goal": job_data["jobGoal"]["type"],
            "task_intent": ",".join(job_data["jobObjectives"]),
            "task_priority_value": job_data["jobPriorityValue"],
            "task_streeability_data": {},
            "task_knowledgebase_ptr": None,
            "submitter_subject_id": job_data["submittedBy"],
            "task_op_convertor_dsl_id": "",
            "task_execution_dsl": "",
            "task_submission_ts": str(int(time.time())),
            "task_completion_timeline": {"mode": job_data["jobCompletionMode"]},
            "task_execution_mode": "manual",
            "task_behavior_dsl_map": {},
            "task_contracts_map": {},
            "task_verification_subject_id": job_data["jobVerificationSubjectIds"][0],
            "task_job_submission_data": {
                "job_id": job_data["jobId"],
                "output_template_id": job_data["jobOutputTemplateId"]
            }
        }

        # Step 4: Insert into task DB
        task_client = TaskCreationClient()
        insert_response = task_client.create_task(task_data)

        if insert_response.get("success"):
            return {
                "success": True,
                "task_id": task_id,
                "message": "Task created and inserted successfully"
            }
        else:
            return {
                "success": False,
                "message": f"Task insertion failed: {insert_response.get('error')}"
            }

    except Exception as e:
        return {"success": False, "message": f"Exception during task assignment: {str(e)}"}


class JobBiddingClient:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.listener = JobInvitesListener(self.queue)
        self.bid_submitter = BidSubmissionClient()

    def start(self):
        # Start JobInvitesListener in its own thread
        threading.Thread(target=self.listener.start, daemon=True).start()
        logger.info("JobInvitesListener started in a separate thread")

        # Start queue processing in another thread
        threading.Thread(target=self._start_listener_thread,
                         daemon=True).start()
        logger.info("JobBiddingClient listener thread started")

    def _start_listener_thread(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._listen_for_jobs())

    async def _listen_for_jobs(self):
        while True:
            try:
                job_event = await self.queue.get()
                logger.info(f"Processing job invite: {job_event}")

                # Step 1: Run DSL to create bid data
                workflow_id = os.getenv("ORG_JOB_BID_CREATOR_DSL_WORKFLOW_ID")
                if not workflow_id:
                    logger.error(
                        "ORG_JOB_BID_CREATOR_DSL_WORKFLOW_ID not set in env")
                    continue

                dsl = DSLExecutor(workflow_id=workflow_id)
                dsl_output = dsl.run({"job_data": job_event})
                bid_data = dsl.get_final_output(dsl_output)

                if not bid_data:
                    logger.warning("DSL produced no bid data")
                    continue

                # Step 2: Submit the bid
                response = self.bid_submitter.submit_bid(bid_data)
                if response.get("success"):
                    logger.info(f"Bid submitted successfully: {response}")
                else:
                    logger.warning(f"Bid submission failed: {response}")

            except Exception as e:
                logger.error(f"Error in job bidding loop: {e}")


class JobWinningHandler:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.listener = BidsWinnerListener(self.queue)
        self.task_client = TaskCreationClient()

    def start(self):
        # Start BidsWinnerListener in its own thread
        threading.Thread(target=self.listener.start, daemon=True).start()
        logger.info("BidsWinnerListener started in a separate thread")

        # Start queue processing in another thread
        threading.Thread(target=self._start_listener_thread,
                         daemon=True).start()
        logger.info("JobWinningHandler listener thread started")

    def _start_listener_thread(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._listen_for_winner_events())

    async def _listen_for_winner_events(self):
        while True:
            try:
                winner_event = await self.queue.get()
                logger.info(f"Processing bid winner event: {winner_event}")

                bid_data = winner_event.get("bid_data")
                if not bid_data:
                    logger.warning("No bid_data found in winner event")
                    continue

                # Convert bid_data to task_data
                task_id = f"task-{uuid.uuid4()}"
                task_data = {
                    "task_id": task_id,
                    "task_goal": bid_data.get("goal", ""),
                    "task_intent": bid_data.get("intent", ""),
                    "task_priority_value": bid_data.get("priority", 0),
                    "task_streeability_data": bid_data.get("streeability", {}),
                    "task_knowledgebase_ptr": bid_data.get("kb_ptr"),
                    "submitter_subject_id": bid_data.get("submitter"),
                    "task_op_convertor_dsl_id": bid_data.get("op_convertor_dsl_id", ""),
                    "task_execution_dsl": bid_data.get("execution_dsl_id", ""),
                    "task_submission_ts": str(int(time.time())),
                    "task_completion_timeline": bid_data.get("completion_timeline", {}),
                    "task_execution_mode": "auto",
                    "task_behavior_dsl_map": bid_data.get("behavior_map", {}),
                    "task_contracts_map": bid_data.get("contracts_map", {}),
                    "task_verification_subject_id": bid_data.get("verifier", ""),
                    "task_job_submission_data": {
                        "job_id": bid_data.get("job_id", ""),
                        "origin": "bid_selection"
                    }
                }

                response = self.task_client.create_task(task_data)
                if response.get("success"):
                    logger.info(f"Task created for winning bid: {response}")
                else:
                    logger.warning(
                        f"Failed to create task from bid: {response}")

            except Exception as e:
                logger.error(f"Error in winner task handler: {e}")
