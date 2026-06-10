from celery import Celery

from app.core import settings

app = Celery("tasks", broker=settings.redis_url)


@app.task
def send_event(event_id: str, tenant_id: int, event_type: str, payload: dict):
    print(f"Sending event: {event_id=}, {tenant_id=}, {event_type=}, {payload=}")
    print(payload)
