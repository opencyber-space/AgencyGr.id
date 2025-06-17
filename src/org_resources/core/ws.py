import asyncio
import websockets
import threading
import json
import logging
from urllib.parse import urlparse, parse_qs

from .metrics import MetricsReport  
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

report_generator = MetricsReport()
connected_clients = set()

async def send_report_periodically(websocket, interval: int):
    try:
        while True:
            report = report_generator.generate_report()
            await websocket.send(json.dumps(report))
            await asyncio.sleep(interval)
    except websockets.exceptions.ConnectionClosed:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Error in sending periodic report: {e}")

async def websocket_handler(websocket, path):
    try:
        query = parse_qs(urlparse(path).query)
        interval = int(query.get("interval", ["30"])[0])
        interval = max(5, min(interval, 300))  # enforce reasonable range

        logger.info(f"New WebSocket client connected with interval={interval}s")
        connected_clients.add(websocket)
        await send_report_periodically(websocket, interval)
    finally:
        connected_clients.discard(websocket)

def start_websocket_server(host="0.0.0.0", port=8765):
    logger.info(f"Starting WebSocket server at ws://{host}:{port}")
    server = websockets.serve(websocket_handler, host, port)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(server)
    loop.run_forever()
