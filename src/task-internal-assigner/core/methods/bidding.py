import os
import logging
from typing import Optional
from ..schema import TaskEntry
from ..config import OrgExecutionConfigProvider
from dsl_executor import new_dsl_workflow_executor, parse_dsl_output
from .auction_client import AuctionClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AuctionBasedAgentSelector")

class AuctionBasedAgentSelector:
    def __init__(self):
        self.auction_api = os.getenv("AUCTION_API", "http://localhost:9000")
        self.is_remote = os.getenv("AUCTION_DSL_REMOTE", "false").lower() == "true"
        self.default_dsl_url = os.getenv("ORG_TASK_AUCTION_INPUT_DSL_URL")
        self.config_provider = OrgExecutionConfigProvider()

    def resolve_head_agent(self, task: TaskEntry) -> Optional[str]:
        try:
            org_id = task.submitter_subject_id.split(":")[0]
            dsl_id = task.task_behavior_dsl_map.get("auction_input_dsl_id")

            if not dsl_id:
                dsl_id = self.config_provider.get(org_id, "auction_input_dsl_id")

            if not dsl_id:
                logger.warning(f"No DSL ID provided or configured for auction_input_dsl_id for org: {org_id}")
                return None

            base_url = self.default_dsl_url
            if not base_url:
                logger.warning("Missing DSL base URL for auction input DSL")
                return None

            # Step 2: Execute DSL
            logger.info(f"Running auction DSL: {dsl_id}")
            executor = new_dsl_workflow_executor(
                workflow_id=dsl_id,
                workflows_base_uri=base_url,
                is_remote=self.is_remote
            )
            output = executor.execute({
                "user_input": {
                    "task_id": task.task_id,
                    "goal": task.task_goal,
                    "intent": task.task_intent,
                    "submitter_subject_id": task.submitter_subject_id,
                    "job_space_id": task.task_job_submission_data.get("job_space_id"),
                }
            })
            auction_input = parse_dsl_output(output)
            logger.info(f"Generated auction input: {auction_input}")

            if not isinstance(auction_input, dict):
                logger.error("Auction DSL did not return a valid dict")
                return None

            # Step 3: Submit to auction client
            auction_client = AuctionClient(api_url=self.auction_api)
            result = auction_client.submit_bid_and_wait(auction_input)

            if not result or not result.get("success"):
                logger.warning("Auction result not received or failed")
                return None

            winner_id = result["data"].get("head_agent_subject_id")
            if not winner_id:
                logger.warning("No head_agent_subject_id found in auction result")
                return None

            logger.info(f"Auction winner: {winner_id}")
            return winner_id

        except Exception as e:
            logger.exception("Auction-based resolution failed")
            return None
