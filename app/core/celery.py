from celery import Celery

from .config import settings

app = Celery(
    "tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

app.autodiscover_tasks(["app.tasks"])
