from celery import Celery

from app.core import settings

app = Celery(
    "tasks",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)
