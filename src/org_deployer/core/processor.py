import uuid
import logging
from typing import List

from .crud import OrgCreationTaskDatabase, OrgCreationStageDatabase
from .scheduler import OrgCreationStage, OrgCreationTask
from .k8s import OrgCreationJob

logger = logging.getLogger(__name__)

STAGE_TYPES = [
    "communication_system",
    "roles_management_system",
    "subject_association_system",
    "delegation_system",
    "job_space_controller",
    "resource_manager",
    "monitoring_system"
]

def submit_task_for_creation(org_creation_task_id: str):
    logger.info(f"Submitting org creation task {org_creation_task_id} for execution")

    task_db = OrgCreationTaskDatabase()
    stage_db = OrgCreationStageDatabase()

    # Step 1: Fetch the task
    success, task_or_err = task_db.get_by_id(org_creation_task_id)
    if not success:
        logger.error(f"Task {org_creation_task_id} not found: {task_or_err}")
        return

    task: OrgCreationTask = task_or_err

    # Step 2: Create stages and persist to DB
    stage_ids: List[str] = []
    for stage_type in STAGE_TYPES:
        stage_id = str(uuid.uuid4())
        stage = OrgCreationStage(
            stage_id=stage_id,
            org_creation_task_id=org_creation_task_id,
            stage_type=stage_type,
            status="pending",
            completion_time=""
        )
        insert_success, insert_result = stage_db.insert(stage)
        if insert_success:
            stage_ids.append(stage_id)
        else:
            logger.error(f"Failed to create stage {stage_type} for task {org_creation_task_id}: {insert_result}")

    if not stage_ids:
        logger.error(f"No stages created for task {org_creation_task_id}, aborting job submission")
        return

    # Step 3: Create Kubernetes job
    kubeconfig = task.spec_data.get("kubeconfig", {})
    if not kubeconfig:
        logger.error(f"Task {org_creation_task_id} has no kubeconfig in spec_data")
        return

    job = OrgCreationJob(kubeconfig_dict=kubeconfig, org_task_id=org_creation_task_id)
    job.set_stage_ids(stage_ids)
    try:
        job_name = job.create_job()
        logger.info(f"Job {job_name} created for task {org_creation_task_id}")
    except Exception as e:
        logger.error(f"Failed to create Kubernetes job for task {org_creation_task_id}: {e}")
        return

    # Step 4: Update task status to "processing"
    update_success, update_result = task_db.update(org_creation_task_id, {"status": "processing"})
    if update_success:
        logger.info(f"Task {org_creation_task_id} marked as processing")
    else:
        logger.error(f"Failed to update task {org_creation_task_id} status: {update_result}")


def submit_task_resume(stage_id: str):
    logger.info(f"Resuming task from stage {stage_id}")

    stage_db = OrgCreationStageDatabase()
    task_db = OrgCreationTaskDatabase()

    # Step 1: Get the stage
    stage_success, stage_or_err = stage_db.get_by_id(stage_id)
    if not stage_success:
        logger.error(f"Stage {stage_id} not found: {stage_or_err}")
        return

    stage = stage_or_err
    task_id = stage.org_creation_task_id

    # Step 2: Get the task
    task_success, task_or_err = task_db.get_by_id(task_id)
    if not task_success:
        logger.error(f"Task {task_id} not found for stage {stage_id}: {task_or_err}")
        return

    task: OrgCreationTask = task_or_err

    # Step 3: Get all stage IDs
    all_stages_success, all_stages_or_err = stage_db.query({"org_creation_task_id": task_id})
    if not all_stages_success:
        logger.error(f"Could not fetch all stages for task {task_id}: {all_stages_or_err}")
        return

    stage_ids = [s["stage_id"] for s in all_stages_or_err]

    # Step 4: Create Kubernetes job to resume
    kubeconfig = task.spec_data.get("kubeconfig", {})
    if not kubeconfig:
        logger.error(f"No kubeconfig found in task {task_id} spec_data")
        return

    try:
        job = OrgCreationJob(kubeconfig_dict=kubeconfig, org_task_id=task_id)
        job.set_stage_ids(stage_ids)
        job_name = job.resume_from_stage(stage_id)
        logger.info(f"Resumed task {task_id} from stage {stage_id} with job {job_name}")
    except Exception as e:
        logger.error(f"Failed to resume task {task_id} from stage {stage_id}: {e}")


def remove_org(org_task_id: str):
    logger.info(f"Initiating removal for org task {org_task_id}")

    task_db = OrgCreationTaskDatabase()

    # Step 1: Fetch task
    success, task_or_err = task_db.get_by_id(org_task_id)
    if not success:
        logger.error(f"Task {org_task_id} not found: {task_or_err}")
        return

    task = task_or_err

    # Step 2: Get kubeconfig
    kubeconfig = task.spec_data.get("kubeconfig", {})
    if not kubeconfig:
        logger.error(f"Missing kubeconfig for task {org_task_id}")
        return

    # Step 3: Launch removal job
    try:
        job = OrgCreationJob(kubeconfig_dict=kubeconfig, org_task_id=org_task_id)
        job.set_stage_ids([])  # optional, or include if needed during teardown
        job_name = job.remove_org()
        logger.info(f"Removal job {job_name} launched for task {org_task_id}")
    except Exception as e:
        logger.error(f"Failed to launch removal job for task {org_task_id}: {e}")



class StatusUpdateSystem:
    def __init__(self):
        self.task_db = OrgCreationTaskDatabase()
        self.stage_db = OrgCreationStageDatabase()

    def update_stage_status(self, stage_id: str, new_status: str, completion_time: str = "") -> bool:
        try:
            # Step 1: Update the stage status
            stage_success, stage_obj_or_err = self.stage_db.get_by_id(stage_id)
            if not stage_success:
                logger.error(f"Stage {stage_id} not found: {stage_obj_or_err}")
                return False

            stage: OrgCreationStage = stage_obj_or_err
            update_fields = {"status": new_status}
            if completion_time:
                update_fields["completion_time"] = completion_time

            update_success, update_result = self.stage_db.update(stage_id, update_fields)
            if not update_success:
                logger.error(f"Failed to update stage {stage_id}: {update_result}")
                return False

            logger.info(f"Stage {stage_id} updated to {new_status}")

            # Step 2: If stage failed, mark the entire task as failed
            if new_status == "failed":
                task_update_success, task_update_result = self.task_db.update(stage.org_creation_task_id, {"status": "failed"})
                if task_update_success:
                    logger.info(f"Org task {stage.org_creation_task_id} marked as failed due to failed stage {stage_id}")
                else:
                    logger.error(f"Failed to mark task {stage.org_creation_task_id} as failed: {task_update_result}")
                return True

            # Step 3: Check if all stages are complete
            all_stages_success, all_stages = self.stage_db.query({
                "org_creation_task_id": stage.org_creation_task_id
            })

            if not all_stages_success:
                logger.error(f"Failed to query stages for task {stage.org_creation_task_id}: {all_stages}")
                return False

            if all(stage["status"] == "complete" for stage in all_stages):
                task_update_success, task_update_result = self.task_db.update(stage.org_creation_task_id, {"status": "complete"})
                if task_update_success:
                    logger.info(f"All stages complete — Org task {stage.org_creation_task_id} marked as complete")
                else:
                    logger.error(f"Failed to update org task {stage.org_creation_task_id} to complete: {task_update_result}")

            return True

        except Exception as e:
            logger.error(f"Error in update_stage_status for stage {stage_id}: {e}")
            return False
