import asyncio
from typing import Optional
from app.core.models import Task, TaskStatus
import logging

logger = logging.getLogger(__name__)


class InMemoryTaskRepository:
    """
    Thread-safe in-memory store for task state.
    Production swap: PostgreSQL / Azure SQL / CosmosDB.
    """

    def __init__(self):
        self._store: dict[str, Task] = {}
        self._lock = asyncio.Lock()

    async def save(self, task: Task) -> Task:
        async with self._lock:
            self._store[task.id] = task.copy(deep=True)
            return task

    async def update(self, task: Task) -> Task:
        async with self._lock:
            self._store[task.id] = task.copy(deep=True)
            return task

    async def get_by_id(self, task_id: str) -> Optional[Task]:
        async with self._lock:
            return self._store.get(task_id)

    async def get_all(self, status: Optional[TaskStatus] = None) -> list[Task]:
        async with self._lock:
            tasks = list(self._store.values())
            if status:
                tasks = [t for t in tasks if t.status == status]
            return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    async def get_stats(self) -> dict:
        async with self._lock:
            all_tasks = list(self._store.values())
            return {
                "total": len(all_tasks),
                "pending":   sum(1 for t in all_tasks if t.status == TaskStatus.PENDING),
                "queued":    sum(1 for t in all_tasks if t.status == TaskStatus.QUEUED),
                "running":   sum(1 for t in all_tasks if t.status == TaskStatus.RUNNING),
                "retrying":  sum(1 for t in all_tasks if t.status == TaskStatus.RETRYING),
                "completed": sum(1 for t in all_tasks if t.status == TaskStatus.COMPLETED),
                "failed":    sum(1 for t in all_tasks if t.status == TaskStatus.FAILED),
                "dead":      sum(1 for t in all_tasks if t.status == TaskStatus.DEAD),
            }
