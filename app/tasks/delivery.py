import asyncio

from sqlmodel import Session, select

from app.core import celery_app as app
from app.core import engine
from app.models import Subscription
from app.services import deliver_event


@app.task(bind=True)
def dispatch_event(
    self,
    subscription_id: int,
    event_id: str,
    payload: dict,
):
    with Session(engine) as session:
        subscription = session.exec(
            select(Subscription).where(Subscription.id == subscription_id)
        ).first()

        if not subscription:
            return

    success, http_status, err_msg = asyncio.run(
        deliver_event(
            subscription=subscription,
            event_id=event_id,
            payload=payload,
        )
    )

    if success:
        print(f"Event {event_id} delivered successfully")
    else:
        print(f"Event {event_id} failed to deliver")
        print(f"HTTP status: {http_status}")
        print(f"Error message: {err_msg}")
