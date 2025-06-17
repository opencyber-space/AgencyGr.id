import threading
import time
import logging
from queue import Queue

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Timer:
    def __init__(self, queue: Queue, interval: float):
        self.queue = queue
        self.interval = interval
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._stop_event = threading.Event()
        logger.info(f"Timer initialized with interval {self.interval} seconds")

    def start(self):
        logger.info("Starting timer thread")
        self._thread.start()

    def stop(self):
        logger.info("Stopping timer thread")
        self._stop_event.set()
        self._thread.join()

    def run(self):
        logger.info("Timer thread running")
        while not self._stop_event.is_set():
            time.sleep(self.interval)
            logger.debug("Timer activated")
            self.queue.put("activate")
