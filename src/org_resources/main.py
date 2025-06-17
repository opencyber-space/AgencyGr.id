import threading
import logging

from core.apis import app  
from core.ws import start_websocket_server  

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_websocket_server():
    try:
        start_websocket_server(host="0.0.0.0", port=8765)
    except Exception as e:
        logger.error(f"WebSocket server failed to start: {e}")


if __name__ == "__main__":
    
    ws_thread = threading.Thread(target=run_websocket_server, daemon=True)
    ws_thread.start()

   
    logger.info("Starting Flask app on http://0.0.0.0:8000")
    app.run(host="0.0.0.0", port=8000, debug=False)
