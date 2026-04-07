from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
import uuid


class TaskStatus(str, Enum):
    PENDING   = "pending"
    QUEUED    = "queued"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"
    RETRYING  = "retrying"
    DEAD      = "dead"


class TaskPriority(int, Enum):
    LOW    = 1
    MEDIUM = 5
    HIGH   = 10


class TaskType(str, Enum):
    DATA_PROCESSING   = "data_processing"
    REPORT_GENERATION = "report_generation"
    EMAIL_DISPATCH    = "email_dispatch"
    FILE_EXPORT       = "file_export"


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: TaskType
    priority: int = 5
    payload: Dict[str, Any] = {}
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    worker_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

    def __lt__(self, other: "Task") -> bool:
        return self.priority > other.priority

    class Config:
        use_enum_values = True


class TaskRequest(BaseModel):
    type: TaskType
    priority: int = 5
    payload: Dict[str, Any] = {}
    max_retries: int = 3


class TaskSummary(BaseModel):
    id: str
    type: str
    priority: int
    status: str
    retry_count: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    worker_id: Optional[str] = None
    error_message: Optional[str] = None