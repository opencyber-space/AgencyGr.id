import base64
import json
import tempfile
import os
from typing import List, Dict
from kubernetes import client, config
import logging

logger = logging.getLogger(__name__)

# inside org_creation_job.py

class OrgCreationJob:
    def __init__(self, kubeconfig_dict: Dict, org_task_id: str):
        self.kubeconfig_dict = kubeconfig_dict
        self.org_task_id = org_task_id
        self.namespace = "org-jobs"
        self.image = "agetspacev1/org-creation-job:v1"
        self.registry_api = os.getenv("ORG_CREATION_TASK_REGISTRY_API", "http://registry.default.svc.cluster.local")
        self.stage_ids: List[str] = []

        self.kubeconfig_file = self._write_temp_kubeconfig()
        config.load_kube_config(config_file=self.kubeconfig_file)
        self.batch_v1 = client.BatchV1Api()
        self.core_v1 = client.CoreV1Api()

    def _write_temp_kubeconfig(self) -> str:
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp:
            json.dump(self.kubeconfig_dict, temp)
            return temp.name

    def set_stage_ids(self, stage_ids: List[str]):
        self.stage_ids = stage_ids

    def _build_env_vars(self, resume_stage_id: str = "", mode: str = "create") -> List[Dict[str, str]]:
        env_vars = [
            {"name": "ORG_CREATION_TASK_ID", "value": self.org_task_id},
            {"name": "ORG_CREATION_TASK_REGISTRY_API", "value": self.registry_api},
            {"name": "STAGE_IDS", "value": json.dumps(self.stage_ids)},
            {"name": "MODE", "value": mode},
        ]
        if resume_stage_id:
            env_vars.append({"name": "RESUME_STAGE_ID", "value": resume_stage_id})
        return env_vars

    def _build_job_manifest(self, job_name: str, env_vars: List[Dict[str, str]]) -> Dict:
        return {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {"name": job_name, "namespace": self.namespace},
            "spec": {
                "template": {
                    "metadata": {"name": job_name},
                    "spec": {
                        "containers": [
                            {
                                "name": "org-creator",
                                "image": self.image,
                                "env": env_vars
                            }
                        ],
                        "restartPolicy": "Never"
                    }
                },
                "backoffLimit": 2
            }
        }

    def create_job(self) -> str:
        job_name = f"org-creation-{self.org_task_id[:8]}"
        env_vars = self._build_env_vars()
        manifest = self._build_job_manifest(job_name, env_vars)
        return self._submit_job(job_name, manifest)

    def resume_from_stage(self, resume_stage_id: str) -> str:
        job_name = f"org-resume-{resume_stage_id[:8]}"
        env_vars = self._build_env_vars(resume_stage_id=resume_stage_id)
        manifest = self._build_job_manifest(job_name, env_vars)
        return self._submit_job(job_name, manifest)
    
    def remove_org(self) -> str:
        job_name = f"org-remove-{self.org_task_id[:8]}"
        env_vars = self._build_env_vars(mode="remove")
        manifest = self._build_job_manifest(job_name, env_vars)
        return self._submit_job(job_name, manifest)

    def _submit_job(self, job_name: str, manifest: Dict) -> str:
        try:
            self._ensure_namespace()
            self.batch_v1.create_namespaced_job(namespace=self.namespace, body=manifest)
            logger.info(f"Kubernetes job {job_name} submitted")
            return job_name
        except client.rest.ApiException as e:
            logger.error(f"Failed to submit job {job_name}: {e}")
            raise

    def _ensure_namespace(self):
        try:
            self.core_v1.read_namespace(self.namespace)
        except client.exceptions.ApiException as e:
            if e.status == 404:
                self.core_v1.create_namespace(
                    client.V1Namespace(metadata=client.V1ObjectMeta(name=self.namespace))
                )
                logger.info(f"Namespace {self.namespace} created")
            else:
                raise

