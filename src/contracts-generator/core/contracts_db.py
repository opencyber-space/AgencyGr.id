import requests
import logging

logger = logging.getLogger(__name__)

class ContractsDBClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def create_contract(self, contract_spec: dict) -> dict:
        try:
            response = requests.post(f"{self.base_url}/contract", json=contract_spec)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create contract: {e}")
            raise

    def update_contract(self, contract_spec: dict) -> dict:
        try:
            response = requests.put(f"{self.base_url}/contract", json=contract_spec)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to update contract: {e}")
            raise

    def delete_contract(self, contract_id: str) -> dict:
        try:
            response = requests.delete(f"{self.base_url}/contract/{contract_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to delete contract {contract_id}: {e}")
            raise
