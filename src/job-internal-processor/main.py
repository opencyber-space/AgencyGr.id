import logging
import time
from .core.tasks_loader import TasksInitiator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TaskRuntime")

def main():
    logger.info("Starting Task Runtime System...")

    # Initialize everything (loader, listener, processor)
    initiator = TasksInitiator()

    try:
        while True:
            task = initiator.get_next_task()
            if task:
                priority, payload = task
                task_type = payload["type"]
                task_data = payload["data"]

                logger.info(f"[DISPATCH] {task_type.upper()} | Priority: {priority} | ID: {task_data.get('task_id') or task_data.get('sub_task_id')}")

            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down Task Runtime.")

if __name__ == "__main__":
    main()
