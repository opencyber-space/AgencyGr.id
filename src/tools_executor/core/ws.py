import asyncio
import websockets
import threading
import json
import os
import uuid
import logging
from queue import Queue
from typing import Dict, Any

from .executor import ToolTaskExecutor, FunctionTaskExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Shared producer queue for output
producer_queue = Queue()

# Connection map: UUID → websocket
uuid_connection_map: Dict[str, websockets.WebSocketServerProtocol] = {}

# Tool and Function executors
tool_executor = ToolTaskExecutor(
    producer_queue=producer_queue,
    base_url=os.getenv("TOOL_DB_SERVER", "http://localhost:3000")
)

function_executor = FunctionTaskExecutor(
    producer_queue=producer_queue,
    base_url=os.getenv("FUNCTION_DB_SERVER", "http://localhost:3000")
)

# Start task executor threads
def start_task_executors():
    threading.Thread(target=tool_executor.run, daemon=True).start()
    threading.Thread(target=function_executor.run, daemon=True).start()

# Dispatcher to return results over websocket
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
        logger.info("WebSocket connection closed")

# WebSocket handler (dispatches based on route)
async def handler(websocket, path):
    try:
        message = await websocket.recv()
        task = json.loads(message)
        task_uuid = str(uuid.uuid4())
        uuid_connection_map[task_uuid] = websocket

        success = False
        msg = "Invalid path"
        task_type = None

        if path == "/tool":
            tool_id = task.get("tool_id")
            input_data = task.get("input_data")

            if not all([tool_id, input_data]):
                msg = "Missing required fields for tool task"
            else:
                success, msg = tool_executor.push_task_to_queue(
                    uuid=task_uuid,
                    tool_id=tool_id,
                    input_data=input_data
                )
                task_type = "Tool"

        elif path == "/function":
            function_id = task.get("function_id")
            input_data = task.get("input_data")

            if not all([function_id, input_data]):
                msg = "Missing required fields for function task"
            else:
                success, msg = function_executor.push_task_to_queue(
                    uuid=task_uuid,
                    function_id=function_id,
                    input_data=input_data
                )
                task_type = "Function"

        if not success:
            await websocket.send(json.dumps({"success": False, "error": msg}))
            await websocket.close()
            uuid_connection_map.pop(task_uuid, None)
            return

        await websocket.send(json.dumps({"success": True, "uuid": task_uuid}))
        logger.info(f"{task_type} task {task_uuid} accepted")

    except Exception as e:
        logger.error(f"WebSocket handler error: {e}")
        await websocket.send(json.dumps({"success": False, "error": str(e)}))
        await websocket.close()

# Start the unified WebSocket server
def start_websocket_server(host="0.0.0.0", port=8765):
    start_task_executors()
    start_result_dispatcher()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ws_server = websockets.serve(handler, host, port)
    loop.run_until_complete(ws_server)
    logger.info(f"WebSocket server running on ws://{host}:{port}")
    loop.run_forever()
