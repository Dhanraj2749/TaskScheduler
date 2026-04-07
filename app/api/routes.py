from fastapi import APIRouter, HTTPException, Request, Query
from typing import Optional
from app.core.models import Task, TaskRequest, TaskSummary, TaskStatus
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/tasks", response_model=TaskSummary, status_code=202)
async def submit_task(request: Request, body: TaskRequest):
    """Submit a new task to the scheduler"""
    scheduler = request.app.state.scheduler
    task = Task(
        type=body.type,
        priority=body.priority,
        payload=body.payload,
        max_retries=body.max_retries
    )
    submitted = await scheduler.submit(task)
    logger.info("Task %s submitted | Type: %s | Priority: %s",
                submitted.id[:8], submitted.type, submitted.priority)
    return submitted


@router.get("/tasks/{task_id}", response_model=TaskSummary)
async def get_task(request: Request, task_id: str):
    """Get task status and details by ID"""
    repo = request.app.state.repository
    task = await repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.get("/tasks/{task_id}/result")
async def get_task_result(request: Request, task_id: str):
    """Get the result of a completed task"""
    repo = request.app.state.repository
    task = await repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=409,
                            detail=f"Task is {task.status.value}, not completed yet")
    return {"task_id": task.id, "result": task.result, "completed_at": task.completed_at}


@router.get("/tasks", response_model=list[TaskSummary])
async def list_tasks(
    request: Request,
    status: Optional[TaskStatus] = Query(None, description="Filter by status")
):
    """List all tasks with optional status filter"""
    repo = request.app.state.repository
    return await repo.get_all(status)


@router.get("/stats")
async def get_stats(request: Request):
    """Real-time dashboard stats"""
    repo = request.app.state.repository
    scheduler = request.app.state.scheduler
    stats = await repo.get_stats()
    stats["queue_size"] = scheduler.queue.size
    stats["active_workers"] = 3
    return stats


@router.delete("/tasks/{task_id}")
async def cancel_task(request: Request, task_id: str):
    """Cancel a pending/queued task"""
    repo = request.app.state.repository
    task = await repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    if task.status not in [TaskStatus.PENDING, TaskStatus.QUEUED]:
        raise HTTPException(status_code=409,
                            detail=f"Cannot cancel task in {task.status.value} state")
    task.status = TaskStatus.FAILED
    task.error_message = "Cancelled by user"
    await repo.update(task)
    return {"message": f"Task {task_id} cancelled"}
