from app.core import celery_app as app


@app.task(bind=True)
def dispatch_event(event_id: str, tenant_id: int, event_type: str, payload: dict):
    print(f"Sending event: {event_id=}, {tenant_id=}, {event_type=}, {payload=}")
    print(payload)
