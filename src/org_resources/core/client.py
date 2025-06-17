from typing import List
import requests
import logging
from typing import Dict
import os

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class APIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class GlobalClusterMetricsClient:
    def __init__(self):
        self.base_url = os.getenv(
            "GLOBAL_CLUSTER_METRICS_URL", "http://localhost:8888").rstrip('/')
        logger.info(
            f"GlobalClusterMetricsClient initialized with base URL: {self.base_url}")

    def _handle_response(self, response):
        try:
            response.raise_for_status()
            json_data = response.json()
            if not json_data.get("success", False):
                raise APIError(json_data.get(
                    "error", "Unknown error"), response.status_code)
            return json_data.get("data")
        except requests.RequestException as e:
            logger.error(f"HTTP error: {e}")
            raise
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise

    def get_cluster(self, cluster_id):
        url = f"{self.base_url}/cluster/{cluster_id}"
        response = requests.get(url)
        return self._handle_response(response)


class SubjectMetrics:
    def __init__(self):
        self.base_url = os.getenv(
            "SUBJECT_METRICS_DB_URL", "http://localhost:8891").rstrip('/')
        logger.info(
            f"SubjectMetrics initialized with base URL: {self.base_url}")

    def _handle_response(self, response):
        try:
            response.raise_for_status()
            json_data = response.json()
            if not json_data.get("success", False):
                raise APIError(json_data.get(
                    "error", "Unknown error"), response.status_code)
            return json_data.get("data")
        except requests.RequestException as e:
            logger.error(f"HTTP error: {e}")
            raise
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise

    def get_all_subjects_metrics(self):
        url = f"{self.base_url}/subjects"
        response = requests.get(url)
        return self._handle_response(response)


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class APIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class SubjectsDBClient:
    def __init__(self):
        self.base_url = os.getenv(
            "SUBJECTS_DB_URL", "http://localhost:8892").rstrip('/')
        logger.info(
            f"SubjectsDBClient initialized with base URL: {self.base_url}")

    def _handle_response(self, response):
        try:
            response.raise_for_status()
            json_data = response.json()
            if not json_data.get("success", False):
                raise APIError(json_data.get(
                    "error", "Unknown error"), response.status_code)
            return json_data.get("data")
        except requests.RequestException as e:
            logger.error(f"HTTP error: {e}")
            raise
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise

    def get_subjects(self, subject_ids: List[str]):
        try:
            params = {"subject_id": subject_ids}
            url = f"{self.base_url}/subjects"
            response = requests.get(url, params=params)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"get_subjects error: {e}")
            raise

class SubjectsCache:
    def __init__(self):
        self.cache: Dict[str, dict] = {}
        self.db_client = SubjectsDBClient()
        logger.info("SubjectsCache initialized")

    def get_subjects(self, subject_ids: List[str]) -> List[dict]:
        result = []
        missing_ids = []

        for sid in subject_ids:
            if sid in self.cache:
                result.append(self.cache[sid])
            else:
                missing_ids.append(sid)

        if missing_ids:
            logger.info(f"Fetching missing subjects from DB: {missing_ids}")
            try:
                fetched_subjects = self.db_client.get_subjects(missing_ids)
                for subject in fetched_subjects:
                    sid = subject.get("subject_id")
                    if sid:
                        self.cache[sid] = subject
                        result.append(subject)
            except Exception as e:
                logger.error(f"Error fetching subjects from DB: {e}")
                raise

        return result

    def add_subject(self, subject_id: str):
        if subject_id in self.cache:
            logger.info(f"Subject {subject_id} already in cache")
            return

        try:
            subject_list = self.db_client.get_subjects([subject_id])
            if subject_list:
                subject = subject_list[0]
                self.cache[subject_id] = subject
                logger.info(f"Subject {subject_id} added to cache")
        except Exception as e:
            logger.error(f"Failed to add subject {subject_id} to cache: {e}")
            raise
