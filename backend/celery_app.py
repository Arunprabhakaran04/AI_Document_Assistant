from celery import Celery
import os

# Configure Celery
celery_app = Celery(
    "pdf_processor",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=["backend.tasks"]
)

# Configure Celery settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600, 
    broker_connection_retry_on_startup=True,  
    worker_max_tasks_per_child=1,
    task_routes={
        "backend.tasks.process_pdf_task": {"queue": "pdf_processing"},
    },
)

if __name__ == "__main__":
    celery_app.start() 