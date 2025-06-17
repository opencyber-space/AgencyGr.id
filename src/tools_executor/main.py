from threading import Thread
from .core import app 
from .core.ws import start_websocket_server  

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_flask_server():
    try:
        app.run(host="0.0.0.0", port=8000)
    except Exception as e:
        logger.error(f"Flask server error: {e}")


def main():
    flask_thread = Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    logger.info("Flask server started in background thread")

    start_websocket_server(host="0.0.0.0", port=8765)


if __name__ == "__main__":
    main()
