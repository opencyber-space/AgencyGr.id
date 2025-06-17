import logging
from typing import List, Optional, Dict
from dsl_executor import new_dsl_workflow_executor, parse_dsl_output
import json
import uuid
from .contracts_db import ContractsDBClient

from .initiator.spec import JobSpec
from .db import JobSpaceContractsMapping, JobSpaceContractsMappingDB

from .subject_intervention import SessionClient

logger = logging.getLogger(__name__)


TOP_LEVEL_REQUIRED_KEYS = [
    "contracts", "sub_contracts", "actions", "verification_entries", "constraints"
]

def validate_contract_spec_top_level(contract_spec: Dict):
    for key in TOP_LEVEL_REQUIRED_KEYS:
        if key not in contract_spec:
            raise ValueError(f"Missing required top-level key in contract_spec: '{key}'")

def create_and_map_contracts(
    spec: JobSpec,
    dsl_output: Dict,
    contracts_client: ContractsDBClient,
    mapping_db: JobSpaceContractsMappingDB
) -> str:
    try:
        contract_spec = dsl_output.get("contract_spec")
        if not contract_spec:
            raise ValueError("Missing 'contract_spec' in DSL output")

        validate_contract_spec_top_level(contract_spec)

        contracts: List[Dict] = contract_spec["contracts"]
        if not isinstance(contracts, list) or not contracts:
            raise ValueError("Expected non-empty 'contracts' list in contract_spec")

        contract_ids = []
        for idx, contract in enumerate(contracts):
            logger.info(f"Submitting contract {idx + 1}/{len(contracts)}: {contract.get('contract_id')}")
            result = contracts_client.create_contract(contract)
            created_id = result.get("result", {}).get("contract_id")
            if not created_id:
                raise ValueError(f"Contract {idx} creation failed or missing 'contract_id' in response")
            contract_ids.append(created_id)

        metadata = contracts[0].get("metadata", {}) if contracts else {}

        mapping = JobSpaceContractsMapping(
            task_id=spec.task_id,
            sub_task_id=spec.sub_task_id,
            contract_ids=contract_ids,
            metadata=metadata
        )
        mapping_db.create(mapping)

        logger.info(f"Successfully mapped {len(contract_ids)} contracts to job: {spec.task_id}")
        return mapping.key

    except Exception as e:
        logger.error(f"create_and_map_contracts failed: {e}", exc_info=True)
        raise



class SubjectInterventionSystem:
    def __init__(self, session_client: SessionClient, default_subject_id: Optional[str] = None):
        self.session_client = session_client
        self.default_subject_id = default_subject_id or "default-reviewer"

    def review_and_modify(self, spec: JobSpec) -> JobSpec:
        try:
            session_id = f"intervene-{spec.task_id}-{uuid.uuid4().hex[:8]}"
            logger.info(f"Starting intervention session: {session_id}")

            # Step 1: Create a session
            self.session_client.create_session(
                session_id=session_id,
                message_data=spec.to_dict(),
                subject_id=self.default_subject_id
            )

            # Step 2: Send message for review
            self.session_client.send_message(
                session_id=session_id,
                channel_id="review",
                message=json.dumps(spec.to_dict(), indent=2)
            )

            # Step 3: Wait for user modification
            response = self.session_client.send_and_wait_for_response(
                session_id=session_id,
                channel_id="review",
                message="Awaiting user intervention...",
                subject_id=self.default_subject_id,
                timeout=90
            )

            if response.get("status") == "REJECTED":
                self.session_client.reject_session(session_id)
                raise Exception("Intervention rejected by human reviewer.")

            modified_spec_data = response.get("job_spec", spec.to_dict())
            logger.info(f"Intervention complete. Modified spec: {modified_spec_data}")
            return JobSpec.from_dict(modified_spec_data)

        except Exception as e:
            logger.error(f"Intervention failed or timed out: {e}")
            return spec

class JobSpaceContractGeneratorDSLExecutor:

    def __init__(
        self,
        workflow_id: str,
        workflows_base_uri: str,
        contracts_client: ContractsDBClient,
        mapping_db: JobSpaceContractsMappingDB,
        intervention_system: Optional[SubjectInterventionSystem] = None,
        is_remote: bool = False,
        addons: dict = None
    ):
        self.executor = new_dsl_workflow_executor(
            workflow_id=workflow_id,
            workflows_base_uri=workflows_base_uri,
            is_remote=is_remote,
            addons=addons or {}
        )
        self.contracts_client = contracts_client
        self.mapping_db = mapping_db
        self.intervention_system = intervention_system

    def execute(self, spec: JobSpec) -> List[JobSpaceContractsMapping]:
        try:
            logger.info(f"Executing DSL for JobSpec: task={spec.task_id}, sub_task={spec.sub_task_id}")

            # Step 1: Optional human intervention
            if spec.human_intervention_required and self.intervention_system:
                logger.info("Human intervention triggered.")
                spec = self.intervention_system.review_and_modify(spec)

            # Step 2: Prepare DSL input
            dsl_input = {
                "job_spec": spec.to_dict()
            }

            output = self.executor.execute(dsl_input)

            result_data = parse_dsl_output(output)

            
            contract_mappings = []
            for item in result_data.get("contract_outputs", []):
                mapping = JobSpaceContractsMapping(
                    task_id=spec.task_id,
                    sub_task_id=spec.sub_task_id,
                    contract_ids=item.get("contract_ids", []),
                    metadata=item.get("metadata", {})
                )
                contract_mappings.append(mapping)

            logger.info(f"Generated {len(contract_mappings)} contract mappings.")
            return contract_mappings

        except Exception as e:
            logger.error(f"Error during DSL execution: {e}", exc_info=True)
            raise
