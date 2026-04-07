from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routes import router
from app.workers.scheduler import TaskScheduler
from app.db.repository import InMemoryTaskRepository
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

repository = InMemoryTaskRepository()
scheduler = TaskScheduler(repository)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await scheduler.start()
    logging.info("Task Scheduler started — workers running")
    yield
    await scheduler.stop()
    logging.info("Task Scheduler stopped")

app = FastAPI(
    title="Distributed Task Scheduler",
    description="Cloud-native async task scheduling system with priority queues, retry logic, and fault tolerance.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router, prefix="/api")
app.state.repository = repository
app.state.scheduler = scheduler
