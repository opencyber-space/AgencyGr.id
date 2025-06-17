import os
import logging
from typing import Dict, Any

from .crud import OrgResourceQuotaDatabase
from .client import GlobalClusterMetricsClient
from .client import SubjectMetrics
from .client import SubjectsCache

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MetricsReport:
    def __init__(self):
        self.cluster_id = os.getenv("CLUSTER_ID")
        if not self.cluster_id:
            raise EnvironmentError("CLUSTER_ID environment variable not set")

        self.quota_db = OrgResourceQuotaDatabase()
        self.cluster_metrics_client = GlobalClusterMetricsClient()
        self.subject_metrics_client = SubjectMetrics()
        self.subjects_cache = SubjectsCache()

        logger.info("MetricsReport initialized")

    def generate_report(self) -> Dict[str, Any]:
        try:
            # Step 1: Get all subjects from quota DB
            success, quotas = self.quota_db.query({})
            if not success:
                raise RuntimeError(f"Failed to query quotas: {quotas}")

            subject_ids = list({q.get("subject_id") for q in quotas if q.get("subject_id")})
            logger.info(f"Found {len(subject_ids)} unique subject IDs")

            # Step 2: Get cluster metrics
            cluster_metrics = self.cluster_metrics_client.get_cluster(self.cluster_id)
            logger.info(f"Cluster metrics retrieved for cluster_id={self.cluster_id}")

            # Step 3: Get subject metrics
            subject_metrics = self.subject_metrics_client.get_all_subjects_metrics()
            logger.info(f"Subject metrics retrieved")

            # Step 4: Get subject data from cache
            subject_data_list = self.subjects_cache.get_subjects(subject_ids)
            subject_data_map = {s["subject_id"]: s for s in subject_data_list}

            # Step 5: Prepare final report
            subjects_combined = {
                "data": subject_data_map,
                "metrics": {m["subject_id"]: m for m in subject_metrics if "subject_id" in m}
            }

            return {
                "cluster_metrics": cluster_metrics,
                "subjects": subjects_combined
            }

        except Exception as e:
            logger.error(f"Failed to generate metrics report: {e}")
            raise

