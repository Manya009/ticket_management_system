# celery_worker.py

from celery import Celery
import os
from dotenv import load_dotenv
load_dotenv()

celery = Celery(
    "worker",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL"),
)

celery.conf.task_routes = {
    "tasks.*": {"queue": "default"}
}

celery.autodiscover_tasks(["app"])