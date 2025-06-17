import asyncio
import websockets
import threading
import json
import os
import uuid
from queue import Queue
from typing import Dict, Any

from .task_processor import DSLTaskExecutor 
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Shared queues
producer_queue = Queue()

# Task executor instance
dsl_executor = DSLTaskExecutor(
    producer_queue=producer_queue,
    workflows_base_uri=os.getenv("DSL_DB_API_URL"),
    is_remote=False
)

# Maps UUID -> websocket connection
uuid_connection_map: Dict[str, websockets.WebSocketServerProtocol] = {}

# Start task executor in background
def start_task_executor():
    threading.Thread(target=dsl_executor.run, daemon=True).start()

# Watch for results and send over websocket
def start_result_dispatcher():
    def dispatch_loop():
        while True:
            result = producer_queue.get()
            task_uuid = result["uuid"]
            output = result["output"]

            if task_uuid in uuid_connection_map:
                ws = uuid_connection_map.pop(task_uuid)
                asyncio.run(send_result_and_close(ws, output))

    threading.Thread(target=dispatch_loop, daemon=True).start()

async def send_result_and_close(ws, output):
    try:
        await ws.send(json.dumps({"success": True, "output": output}))
    except Exception as e:
        logger.error(f"Error sending result: {e}")
    finally:
        await ws.close()
        logger.info("WebSocket connection closed after sending result")

# WebSocket handler
async def handler(websocket, path):
    try:
        message = await websocket.recv()
        task = json.loads(message)

        workflow_id = task.get("workflow_id")
        input_data = task.get("input_data")
        output_name = task.get("output_name")

        if not all([workflow_id, input_data, output_name]):
            await websocket.send(json.dumps({"success": False, "error": "Missing required fields"}))
            await websocket.close()
            return

        task_uuid = str(uuid.uuid4())
        uuid_connection_map[task_uuid] = websocket

        success, msg = dsl_executor.push_task_to_queue(
            uuid=task_uuid,
            workflow_id=workflow_id,
            input_data=input_data,
            output_name=output_name
        )

        if not success:
            await websocket.send(json.dumps({"success": False, "error": msg}))
            await websocket.close()
            uuid_connection_map.pop(task_uuid, None)
            return

        await websocket.send(json.dumps({"success": True, "uuid": task_uuid}))
        logger.info(f"Task {task_uuid} accepted for workflow {workflow_id}")

    except Exception as e:
        logger.error(f"WebSocket handler error: {e}")
        await websocket.send(json.dumps({"success": False, "error": str(e)}))
        await websocket.close()

# Start WebSocket server
def start_websocket_server(host="0.0.0.0", port=8765):
    start_task_executor()
    start_result_dispatcher()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ws_server = websockets.serve(handler, host, port)
    loop.run_until_complete(ws_server)
    logger.info(f"WebSocket server started on ws://{host}:{port}")
    loop.run_forever()
