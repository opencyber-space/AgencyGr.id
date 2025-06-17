import os
import asyncio
import threading
import logging
import json
import uuid
from queue import Queue, Empty
from flask import Flask, request, jsonify
import websockets

from .scaler import AutoscaleDSLExecutor
from .alloc_client import SubjectResourceAllocator
from .alloc_client import AllocationResponseListener
from .timer import Timer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class OrgAutoscaler:
    def __init__(self, workflow_id: str, interval: float = 30.0):
        self.workflow_id = workflow_id
        self.interval = interval

        self.event_queue = Queue()
        self.response_queue = Queue()
        self.connections = {}  # uuid -> websocket connection

        self.executor = AutoscaleDSLExecutor(workflow_id=self.workflow_id)
        self.resource_allocator = SubjectResourceAllocator()
        self.listener = AllocationResponseListener(
            response_queue=self.response_queue)
        self.timer = Timer(self.event_queue, self.interval)

        self.flask_app = Flask(__name__)
        self.executor.register_routes(self.flask_app)
        self.register_internal_routes()

    def register_internal_routes(self):
        @self.flask_app.route('/autoscale/interval', methods=['POST'])
        def set_interval():
            try:
                data = request.json
                new_interval = data.get("interval")
                if not isinstance(new_interval, (int, float)) or new_interval <= 0:
                    return jsonify({"success": False, "error": "Interval must be a positive number"}), 400
                self.interval = new_interval
                self.timer.interval = new_interval
                logger.info(f"Interval updated to {new_interval} seconds")
                return jsonify({"success": True, "message": "Interval updated"}), 200
            except Exception as e:
                logger.error(f"set_interval error: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.flask_app.route('/autoscale/interval', methods=['GET'])
        def get_interval():
            try:
                return jsonify({"success": True, "data": {"interval": self.interval}}), 200
            except Exception as e:
                logger.error(f"get_interval error: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

    def start_flask_server(self):
        def _run():
            logger.info("Starting Flask config server on port 5000")
            self.flask_app.run(port=5000, debug=False, use_reloader=False)
        threading.Thread(target=_run, daemon=True).start()

    def start_queue_listener(self):
        def _listener():
            logger.info("Starting DSL execution queue listener")
            while True:
                event = self.event_queue.get()
                if event == "activate":
                    try:
                        execution_id = str(uuid.uuid4())
                        logger.info(
                            f"Triggering DSL execution: {execution_id}")
                        self.executor.execute(execution_id=execution_id)
                    except Exception as e:
                        logger.error(f"DSL execution error: {e}")
        threading.Thread(target=_listener, daemon=True).start()

    def start_response_router(self):
        def _response_loop():
            logger.info("Starting NATS response router thread")
            while True:
                try:
                    message = self.response_queue.get(timeout=1)
                    response_uuid = message.get("uuid")
                    if response_uuid and response_uuid in self.connections:
                        websocket = self.connections.pop(response_uuid)
                        asyncio.run(self._send_response(websocket, message))
                except Empty:
                    continue
                except Exception as e:
                    logger.error(f"Response router error: {e}")
        threading.Thread(target=_response_loop, daemon=True).start()

    async def _send_response(self, websocket, message):
        try:
            await websocket.send(json.dumps({"success": True, "response": message}))
        except Exception as e:
            logger.error(f"Error sending WebSocket response: {e}")
        finally:
            await websocket.close()

    def start_websocket_server(self):
        async def handler(websocket, _):
            try:
                raw = await websocket.recv()
                data = json.loads(raw)
                subject_id = data.get("subject_id")
                replica_count = data.get("replica_count")

                if not subject_id or not isinstance(replica_count, int):
                    await websocket.send(json.dumps({"success": False, "error": "Invalid input"}))
                    await websocket.close()
                    return

                request_id = str(uuid.uuid4())
                self.connections[request_id] = websocket
                logger.info(
                    f"WebSocket scale request: subject={subject_id}, count={replica_count}, uuid={request_id}")

                self.resource_allocator.allocate_resources(
                    subject_id, replica_count)
                # Response handled by response router
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.send(json.dumps({"success": False, "error": str(e)}))
                await websocket.close()

        async def run_ws():
            logger.info("WebSocket server listening on ws://0.0.0.0:6789")
            async with websockets.serve(handler, "0.0.0.0", 6789):
                await asyncio.Future()

        threading.Thread(target=lambda: asyncio.run(
            run_ws()), daemon=True).start()

    def start(self):
        self.start_flask_server()
        self.start_queue_listener()
        self.start_websocket_server()
        self.start_response_router()
        self.timer.start()
        self.listener.start()
        logger.info("OrgAutoscaler fully operational")
