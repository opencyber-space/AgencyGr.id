import logging
from typing import List, Tuple
from .schema import TaskEntry, SubTaskEntry
from .db import TaskEntryDatabase, SubTaskEntryDatabase

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TasksLoader:
    def __init__(self):
        self.task_db = TaskEntryDatabase()
        self.sub_task_db = SubTaskEntryDatabase()

    def load_pending_tasks(self) -> Tuple[List[TaskEntry], List[SubTaskEntry]]:
        pending_tasks: List[TaskEntry] = []
        pending_sub_tasks: List[SubTaskEntry] = []

        try:
            success, tasks = self.task_db.query({"status": "pending"})
            if success:
                for t in tasks:
                    try:
                        pending_tasks.append(TaskEntry.from_dict(t))
                    except Exception as e:
                        logger.error(f"Failed to load TaskEntry: {e}")
            else:
                logger.error(f"Failed to query tasks: {tasks}")

            success, sub_tasks = self.sub_task_db.query({"status": "pending"})
            if success:
                for st in sub_tasks:
                    try:
                        pending_sub_tasks.append(SubTaskEntry.from_dict(st))
                    except Exception as e:
                        logger.error(f"Failed to load SubTaskEntry: {e}")
            else:
                logger.error(f"Failed to query sub-tasks: {sub_tasks}")

        except Exception as e:
            logger.exception(
                f"Unexpected error while loading pending tasks: {e}")

        return pending_tasks, pending_sub_tasks
