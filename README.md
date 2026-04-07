# Distributed Task Scheduler

A cloud-native async task scheduling system built with **Python and FastAPI** — supports priority queues, concurrent workers, retry with exponential backoff, and a real-time REST dashboard.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              REST API (FastAPI)                          │
│   POST   /api/tasks          — submit task              │
│   GET    /api/tasks/{id}     — get status               │
│   GET    /api/tasks/{id}/result — get result            │
│   GET    /api/tasks          — list all tasks           │
│   GET    /api/stats          — live dashboard           │
│   DELETE /api/tasks/{id}     — cancel task              │
└───────────────────────┬─────────────────────────────────┘
                        │ Submit
                        ▼
┌─────────────────────────────────────────────────────────┐
│           Priority Task Queue (async heap)              │
│   HIGH (10) → MEDIUM (5) → LOW (1)                      │
│   FIFO within same priority level                        │
│   (Production: Redis sorted sets / Azure Service Bus)    │
└───────────┬───────────┬───────────┬─────────────────────┘
            │           │           │
            ▼           ▼           ▼
      [Worker 1]   [Worker 2]   [Worker 3]   (concurrent)
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│              Task Executor                              │
│   data_processing  → process records                   │
│   report_generation → generate PDF                     │
│   email_dispatch   → send email                        │
│   file_export      → export file                       │
└───────────────────────┬─────────────────────────────────┘
                        │ Retry Logic
            ┌───────────┴────────────┐
            │                        │
     Success ✅                 Failure ❌
            │                        │
     COMPLETED              retry_count < max_retries?
                                    │
                    YES ─── Exponential Backoff (2s/4s/8s)
                                    │
                    NO  ─── DEAD (Dead-lettered)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI, Pydantic v2 |
| Queue | Async priority heap (Redis-ready) |
| Workers | asyncio concurrent workers |
| Storage | In-memory (PostgreSQL/CosmosDB ready) |
| Testing | pytest, pytest-asyncio |
| Container | Docker |

## Getting Started

### Run locally
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open Swagger UI: http://localhost:8000/docs

### Run with Docker
```bash
docker build -t task-scheduler .
docker run -p 8000:8000 task-scheduler
```

### Run tests
```bash
pytest tests/ -v
```

## API Usage

### Submit a task
```json
POST /api/tasks
{
  "type": "data_processing",
  "priority": 10,
  "payload": { "record_count": 500 },
  "max_retries": 3
}
```

### Check status
```
GET /api/tasks/{task_id}
```

### Get result
```
GET /api/tasks/{task_id}/result
```

### Live dashboard
```
GET /api/stats
```
```json
{
  "total": 12,
  "queued": 3,
  "running": 2,
  "completed": 6,
  "dead": 1,
  "queue_size": 3,
  "active_workers": 3
}
```

## Key Features

- **Priority queue** — HIGH tasks always processed before LOW
- **3 concurrent async workers** — true parallel processing
- **Retry with exponential backoff** — 2s → 4s → 8s delays
- **Dead-letter tracking** — failed tasks preserved for inspection
- **Full status lifecycle** — Pending → Queued → Running → Completed/Dead
- **Task cancellation** — cancel queued tasks via API
- **Real-time stats dashboard** — live queue and worker metrics
- **Docker ready** — Azure Container Apps / Kubernetes deployable

## Production Swap Guide

| Current (Local) | Production |
|----------------|-----------|
| Async heap queue | Redis sorted sets / Azure Service Bus |
| InMemoryTaskRepository | PostgreSQL / Azure SQL / CosmosDB |
| asyncio workers | Celery workers / Azure Functions |
| Simulated executors | Real business logic per task type |
