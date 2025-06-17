import requests
from typing import List, Dict, Any
import uuid
from dataclasses import asdict, dataclass, field
import logging

from nats.aio.client import Client as NATS
from dataclasses import dataclass
import os
import asyncio
import json
import logging


@dataclass
class TaskResult:
    social_task_id: str
    social_task_data: dict
    voting_result: dict

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            social_task_id=data["social_task_id"],
            social_task_data=data["social_task_dat"],
            voting_result=data["voting_result"]
        )


@dataclass
class SocialTask:
    social_task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_by_subject_id: str = ""
    voting_type: str = ""
    invited_subject_ids: List[str] = field(default_factory=list)
    goal_data: Dict[str, Any] = field(default_factory=dict)
    status: str = ""
    report: Dict[str, Any] = field(default_factory=dict)
    voting_pqt_dsl_id: str = ""
    choice_evaluation_dsl: str = ""
    deadline_time: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        # Validate required fields
        required_fields = [
            "created_by_subject_id", "voting_type", "invited_subject_ids",
            "goal_data", "status", "report", "voting_pqt_dsl_id",
            "choice_evaluation_dsl", "deadline_time"
        ]
        for field_name in required_fields:
            if field_name not in data:
                raise ValueError(f"Missing required field: {field_name}")

        # Construct the instance
        return cls(
            social_task_id=data.get("social_task_id", str(uuid.uuid4())),
            created_by_subject_id=data["created_by_subject_id"],
            voting_type=data["voting_type"],
            invited_subject_ids=data["invited_subject_ids"],
            goal_data=data["goal_data"],
            status=data["status"],
            report=data["report"],
            voting_pqt_dsl_id=data["voting_pqt_dsl_id"],
            choice_evaluation_dsl=data["choice_evaluation_dsl"],
            deadline_time=data["deadline_time"]
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RestClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def _process_response(self, response):

        try:
            response_data = response.json()
            if response.status_code == 200 and response_data.get("success"):
                return response_data.get("data")
            return response_data.get("message", "Unknown error occurred")
        except ValueError:
            response.raise_for_status()
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def create_new_social_task(self, task_data):

        url = f"{self.base_url}/create_new_social_task"
        try:
            response = requests.post(url, json=task_data)
            return self._process_response(response)
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def create_new_vote(self, vote_data):

        url = f"{self.base_url}/create_new_vote"
        try:
            response = requests.post(url, json=vote_data)
            return self._process_response(response)
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def start_evaluation(self, social_task_id):

        url = f"{self.base_url}/start_evaluation/{social_task_id}"
        try:
            response = requests.get(url)
            return self._process_response(response)
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def create_social_task(self, task_data):

        url = f"{self.base_url}/social_tasks"
        try:
            response = requests.post(url, json=task_data)
            return self._process_response(response)
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def get_social_task(self, social_task_id):

        url = f"{self.base_url}/social_tasks/{social_task_id}"
        try:
            response = requests.get(url)
            return self._process_response(response)
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def update_social_task(self, social_task_id, update_data):

        url = f"{self.base_url}/social_tasks/{social_task_id}"
        try:
            response = requests.put(url, json=update_data)
            return self._process_response(response)
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def delete_social_task(self, social_task_id):

        url = f"{self.base_url}/social_tasks/{social_task_id}"
        try:
            response = requests.delete(url)
            return self._process_response(response)
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def query_social_tasks(self, query_filter):

        url = f"{self.base_url}/social_tasks/query"
        try:
            response = requests.post(url, json=query_filter)
            return self._process_response(response)
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def create_vote(self, vote_data):

        url = f"{self.base_url}/votes"
        try:
            response = requests.post(url, json=vote_data)
            return self._process_response(response)
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def get_vote(self, vote_id):

        url = f"{self.base_url}/votes/{vote_id}"
        try:
            response = requests.get(url)
            return self._process_response(response)
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def update_vote(self, vote_id, update_data):

        url = f"{self.base_url}/votes/{vote_id}"
        try:
            response = requests.put(url, json=update_data)
            return self._process_response(response)
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def delete_vote(self, vote_id):

        url = f"{self.base_url}/votes/{vote_id}"
        try:
            response = requests.delete(url)
            return self._process_response(response)
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def query_votes(self, query_filter):

        url = f"{self.base_url}/votes/query"
        try:
            response = requests.post(url, json=query_filter)
            return self._process_response(response)
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def get_votes_by_social_task_id(self, social_task_id):

        url = f"{self.base_url}/votes/social_task/{social_task_id}"
        try:
            response = requests.get(url)
            return self._process_response(response)
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


class TaskResultWaiter:
    def __init__(self, nats_host: str, subject_id: str, task_id: str = ""):
        self.nats_host = nats_host or os.getenv(
            "NATS_HOST", "nats://localhost:4222")
        self.nc = NATS()
        self.result = None
        self.topic = subject_id + "__" + task_id

    def get(self) -> TaskResult:

        try:
            asyncio.run(self._async_get(self.topic))
            if self.result:
                return TaskResult.from_dict(self.result)
            else:
                raise TimeoutError(
                    "No result received within the timeout period.")
        except Exception as e:
            logging.error(f"Error in TaskResultWaiter get method: {e}")
            raise

    async def _async_get(self, topic: str):
        try:
            if not self.nc.is_connected:
                await self.nc.connect(servers=[self.nats_host])

            async def message_handler(msg):
                self.result = json.loads(msg.data.decode('utf-8'))
                await self.nc.drain()  # Close the connection after receiving the message

            await self.nc.subscribe(topic, cb=message_handler)
            await self.nc.flush()

            while self.result is None:
                await asyncio.sleep(0.1)

        except Exception as e:
            logging.error(f"Error in TaskResultWaiter _async_get method: {e}")
            raise


class SocialTaskService:
    def __init__(self, social_task_service_url):
        self.rest_client = RestClient(social_task_service_url)

    def create_social_task(self, created_by_subject_id: str, voting_type: str, invited_subject_ids: List[str],
                           goal_data: Dict[str, Any], status: str, report: Dict[str, Any],
                           voting_pqt_dsl_id: str, choice_evaluation_dsl: str, deadline_time: int) -> SocialTask:

        payload = {
            "created_by_subject_id": created_by_subject_id,
            "voting_type": voting_type,
            "invited_subject_ids": invited_subject_ids,
            "goal_data": goal_data,
            "status": status,
            "report": report,
            "voting_pqt_dsl_id": voting_pqt_dsl_id,
            "choice_evaluation_dsl": choice_evaluation_dsl,
            "deadline_time": deadline_time
        }

        response = self.rest_client.create_new_social_task(payload)

        # Handle the API response
        if response:
            return SocialTask.from_dict(response)
        else:
            raise ValueError(
                "Failed to create social task. API response was invalid or empty.")

    def create_waiter_for_task(self, task_id):
        return TaskResultWaiter(
            nats_host=os.getenv("NATS_URL"), subject_id=os.getenv("SUBJECT_ID"),
            task_id=task_id
        )
