import asyncio
import pytest
from app.core.models import Task, TaskType, TaskPriority, TaskStatus
from app.core.queue import PriorityTaskQueue
from app.db.repository import InMemoryTaskRepository


def make_task(type=TaskType.DATA_PROCESSING, priority=TaskPriority.MEDIUM) -> Task:
    return Task(type=type, priority=priority, payload={"record_count": 10})


# ── Queue Tests ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_enqueue_increases_size():
    queue = PriorityTaskQueue()
    await queue.enqueue(make_task())
    assert queue.size == 1


@pytest.mark.asyncio
async def test_dequeue_returns_task():
    queue = PriorityTaskQueue()
    task = make_task()
    await queue.enqueue(task)
    result = await queue.dequeue()
    assert result is not None
    assert result.id == task.id


@pytest.mark.asyncio
async def test_priority_ordering():
    """HIGH priority tasks should be dequeued before LOW"""
    queue = PriorityTaskQueue()
    low  = make_task(priority=TaskPriority.LOW)
    high = make_task(priority=TaskPriority.HIGH)
    med  = make_task(priority=TaskPriority.MEDIUM)

    await queue.enqueue(low)
    await queue.enqueue(high)
    await queue.enqueue(med)

    first  = await queue.dequeue()
    second = await queue.dequeue()
    third  = await queue.dequeue()

    assert first.priority  == TaskPriority.HIGH
    assert second.priority == TaskPriority.MEDIUM
    assert third.priority  == TaskPriority.LOW


@pytest.mark.asyncio
async def test_dequeue_timeout_returns_none():
    queue = PriorityTaskQueue()
    result = await queue.dequeue(timeout=0.1)
    assert result is None


# ── Repository Tests ─────────────────────────────────────

@pytest.mark.asyncio
async def test_save_and_get_by_id():
    repo = InMemoryTaskRepository()
    task = make_task()
    await repo.save(task)
    result = await repo.get_by_id(task.id)
    assert result is not None
    assert result.id == task.id


@pytest.mark.asyncio
async def test_update_changes_status():
    repo = InMemoryTaskRepository()
    task = make_task()
    await repo.save(task)

    task.status = TaskStatus.COMPLETED
    await repo.update(task)

    result = await repo.get_by_id(task.id)
    assert result.status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_get_all_with_status_filter():
    repo = InMemoryTaskRepository()
    t1 = make_task(); t1.status = TaskStatus.COMPLETED
    t2 = make_task(); t2.status = TaskStatus.DEAD
    await repo.save(t1)
    await repo.save(t2)

    completed = await repo.get_all(TaskStatus.COMPLETED)
    assert len(completed) == 1
    assert completed[0].id == t1.id


@pytest.mark.asyncio
async def test_get_stats():
    repo = InMemoryTaskRepository()
    t1 = make_task(); t1.status = TaskStatus.COMPLETED
    t2 = make_task(); t2.status = TaskStatus.RUNNING
    t3 = make_task(); t3.status = TaskStatus.DEAD
    await repo.save(t1)
    await repo.save(t2)
    await repo.save(t3)

    stats = await repo.get_stats()
    assert stats["total"] == 3
    assert stats["completed"] == 1
    assert stats["running"] == 1
    assert stats["dead"] == 1
