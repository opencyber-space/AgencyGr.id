import os
import json
import logging
import requests
from urllib.parse import urljoin
from flask import Request, Response

from .checker import RevProxyConstraintsChecker

logger = logging.getLogger("ReverseProxyOutput")
logging.basicConfig(level=logging.INFO)


class ReverseProxyOutput:
    def __init__(self):
        try:
            service_map_str = os.getenv("SERVICE_MAP_JSON")
            if not service_map_str:
                raise ValueError("SERVICE_MAP_JSON not found in environment")

            self.service_map = json.loads(service_map_str)
            logger.info("Loaded service map from environment")
        except Exception as e:
            logger.exception("Failed to load service map")
            raise

    def _find_backend_url(self, api_route: str) -> str:
        # Match longest prefix
        matching_prefix = max(
            (prefix for prefix in self.service_map if api_route.startswith(prefix)),
            key=len,
            default=None
        )

        if not matching_prefix:
            raise ValueError(f"No matching backend service found for route '{api_route}'")

        base_url = self.service_map[matching_prefix]
        return urljoin(base_url, api_route[len(matching_prefix):])

    def forward_request(self, original_request: Request, api_route: str) -> Response:
        try:
            # Determine destination URL
            destination_url = self._find_backend_url(api_route)
            logger.info(f"Forwarding request to: {destination_url}")

            # Copy headers, remove Host
            headers = {k: v for k, v in original_request.headers.items() if k.lower() != "host"}

            # Send request
            resp = requests.request(
                method=original_request.method,
                url=destination_url,
                headers=headers,
                data=original_request.get_data(),
                params=original_request.args
            )

            # Return as Flask Response
            return Response(
                response=resp.content,
                status=resp.status_code,
                headers=dict(resp.headers)
            )

        except Exception as e:
            logger.exception(f"Failed to forward request for route '{api_route}'")
            return Response(
                response=json.dumps({"error": str(e)}),
                status=502,
                mimetype="application/json"
            )



class ReverseProxyInput:
    def __init__(self, constraint_checker: RevProxyConstraintsChecker, proxy_output: ReverseProxyOutput):
        self.constraint_checker = constraint_checker
        self.proxy_output = proxy_output

    def handle_request(self, request: Request, api_route: str) -> Response:
        try:
            logger.info(f"Processing incoming request for route: {api_route}")

            # Extract subject_id
            subject_id = request.headers.get("X-Subject-ID")
            if not subject_id and request.is_json:
                subject_id = request.json.get("subject_id")

            if not subject_id:
                logger.warning("Missing subject_id in request")
                return Response(
                    response='{"error": "Missing subject_id"}',
                    status=400,
                    mimetype="application/json"
                )

            # Extract payload (for POST/PUT)
            payload = None
            if request.method in ["POST", "PUT"] and request.is_json:
                payload = request.get_json()
            elif request.method in ["GET", "DELETE"]:
                payload = dict(request.args)

            # Run constraint checker
            self.constraint_checker.validate_request(
                api_route=api_route,
                input_data=payload,
                subject_id=subject_id
            )

            # Forward request to backend
            return self.proxy_output.forward_request(request, api_route)

        except Exception as e:
            logger.exception(f"Validation failed for route '{api_route}'")
            return Response(
                response=f'{{"error": "Request blocked by constraint", "details": "{str(e)}"}}',
                status=403,
                mimetype="application/json"
            )
