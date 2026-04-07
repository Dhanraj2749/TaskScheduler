import asyncio
import random
from app.core.models import Task, TaskType
import logging

logger = logging.getLogger(__name__)


class TaskExecutor:
    """
    Executes tasks by type. Each handler simulates real work.
    Production: replace with actual business logic per task type.
    """

    async def execute(self, task: Task) -> dict:
        handlers = {
            TaskType.DATA_PROCESSING:   self._handle_data_processing,
            TaskType.REPORT_GENERATION: self._handle_report_generation,
            TaskType.EMAIL_DISPATCH:    self._handle_email_dispatch,
            TaskType.FILE_EXPORT:       self._handle_file_export,
        }

        handler = handlers.get(task.type)
        if not handler:
            raise ValueError(f"No executor for task type: {task.type}")

        logger.info("Executing task %s | Type: %s", task.id[:8], task.type)
        return await handler(task)

    async def _handle_data_processing(self, task: Task) -> dict:
        await asyncio.sleep(random.uniform(0.5, 1.5))  # Simulate CPU work
        records = task.payload.get("record_count", 100)
        return {
            "processed_records": records,
            "status": "success",
            "summary": f"Processed {records} records successfully"
        }

    async def _handle_report_generation(self, task: Task) -> dict:
        await asyncio.sleep(random.uniform(0.8, 2.0))  # Simulate DB query + rendering
        report_type = task.payload.get("report_type", "summary")
        return {
            "report_type": report_type,
            "pages": random.randint(1, 10),
            "status": "generated",
            "download_url": f"/reports/{task.id}.pdf"
        }

    async def _handle_email_dispatch(self, task: Task) -> dict:
        await asyncio.sleep(random.uniform(0.2, 0.8))  # Simulate SMTP call
        recipient = task.payload.get("recipient", "user@example.com")
        return {
            "recipient": recipient,
            "status": "sent",
            "message_id": f"msg_{task.id[:8]}"
        }

    async def _handle_file_export(self, task: Task) -> dict:
        await asyncio.sleep(random.uniform(1.0, 2.5))  # Simulate file I/O
        format_ = task.payload.get("format", "csv")
        return {
            "format": format_,
            "file_size_kb": random.randint(10, 500),
            "status": "exported",
            "file_path": f"/exports/{task.id}.{format_}"
        }
