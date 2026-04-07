import asyncio
import uuid
from datetime import datetime
from app.core.models import Task, TaskStatus
from app.core.queue import PriorityTaskQueue
from app.core.executor import TaskExecutor
from app.db.repository import InMemoryTaskRepository
import logging

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
NUM_WORKERS = 3  # Concurrent workers


class TaskScheduler:
    """
    Manages a pool of async workers that pull from a priority queue.
    Handles retry with exponential backoff and dead-lettering.
    """

    def __init__(self, repository: InMemoryTaskRepository):
        self.repository = repository
        self.queue = PriorityTaskQueue()
        self.executor = TaskExecutor()
        self._workers: list[asyncio.Task] = []
        self._running = False

    async def start(self):
        self._running = True
        for i in range(NUM_WORKERS):
            worker_id = f"worker-{i+1}"
            task = asyncio.create_task(self._worker_loop(worker_id))
            self._workers.append(task)
            logger.info("%s started", worker_id)

    async def stop(self):
        self._running = False
        for w in self._workers:
            w.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        logger.info("All workers stopped")

    async def submit(self, task: Task) -> Task:
        task.status = TaskStatus.QUEUED
        await self.repository.save(task)
        await self.queue.enqueue(task)
        return task

    async def _worker_loop(self, worker_id: str):
        logger.info("%s listening for tasks...", worker_id)
        while self._running:
            try:
                task = await self.queue.dequeue(timeout=2.0)
                if task is None:
                    continue
                await self._process(task, worker_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("%s unexpected error: %s", worker_id, str(e))

    async def _process(self, task: Task, worker_id: str):
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        task.worker_id = worker_id
        await self.repository.update(task)

        logger.info("%s picked up task %s | Type: %s | Priority: %s",
                    worker_id, task.id[:8], task.type, task.priority)

        try:
            result = await self.executor.execute(task)
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = result
            await self.repository.update(task)
            logger.info("%s completed task %s", worker_id, task.id[:8])

        except Exception as e:
            task.retry_count += 1
            task.error_message = str(e)
            logger.warning("Task %s failed (attempt %d/%d): %s",
                           task.id[:8], task.retry_count, task.max_retries, str(e))

            if task.retry_count < task.max_retries:
                # Exponential backoff
                delay = 2 ** task.retry_count
                task.status = TaskStatus.RETRYING
                await self.repository.update(task)
                logger.info("Retrying task %s in %ds...", task.id[:8], delay)
                await asyncio.sleep(delay)
                await self.queue.requeue(task)
            else:
                # Dead letter
                task.status = TaskStatus.DEAD
                task.completed_at = datetime.utcnow()
                await self.repository.update(task)
                logger.error("Task %s dead-lettered after %d attempts",
                             task.id[:8], task.max_retries)
