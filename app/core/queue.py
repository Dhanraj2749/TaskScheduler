import asyncio
import heapq
from typing import Optional
from app.core.models import Task
import logging

logger = logging.getLogger(__name__)


class PriorityTaskQueue:
    """
    Thread-safe async priority queue.
    Higher priority tasks are dequeued first.
    Production swap: Azure Service Bus with message priority / Redis sorted sets.
    """

    def __init__(self):
        self._heap: list = []
        self._lock = asyncio.Lock()
        self._event = asyncio.Event()
        self._counter = 0  # Tiebreaker for same-priority tasks (FIFO within priority)

    async def enqueue(self, task: Task) -> None:
        async with self._lock:
            # Negate priority so higher value = higher priority in min-heap
            entry = (-task.priority, self._counter, task)
            heapq.heappush(self._heap, entry)
            self._counter += 1
            self._event.set()
            logger.info("Task %s enqueued | Priority: %s | Queue size: %d",
                        task.id[:8], task.priority, len(self._heap))

    async def dequeue(self, timeout: float = 5.0) -> Optional[Task]:
        try:
            await asyncio.wait_for(self._event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

        async with self._lock:
            if not self._heap:
                self._event.clear()
                return None
            _, _, task = heapq.heappop(self._heap)
            if not self._heap:
                self._event.clear()
            return task

    async def requeue(self, task: Task) -> None:
        """Re-enqueue a task for retry"""
        await self.enqueue(task)
        logger.info("Task %s requeued for retry (attempt %d)", task.id[:8], task.retry_count)

    @property
    def size(self) -> int:
        return len(self._heap)
