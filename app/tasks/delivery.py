import asyncio
import logging

from celery import Task
from celery.exceptions import MaxRetriesExceededError
from sqlmodel import Session, select

from app.core import celery_app as app
from app.core import engine, settings
from app.models import Subscription
from app.services import deliver_event

logger = logging.getLogger(__name__)


@app.task(bind=True)
def dispatch_event(
    self: Task,
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

    current_attempt = self.request.retries + 1

    success, http_status, err_msg = asyncio.run(
        deliver_event(
            subscription=subscription,
            event_id=event_id,
            payload=payload,
            attempt_no=current_attempt,
        )
    )

    if success:
        logger.info(f"Event delivered: {event_id=}, {subscription_id=}, {http_status=}")
        return

    logger.error(
        f"Event delivery failed: {event_id=}, {subscription_id=}, {http_status=}, {err_msg=}"
    )

    next_retry_count = self.request.retries + 1
    calculated_countdown = 5**next_retry_count

    try:
        exc = Exception(err_msg or "Webhook delivery failed")

        raise self.retry(
            exc=exc,
            countdown=calculated_countdown,
            max_retries=settings.CELERY_MAX_RETRIES,
        )
    except MaxRetriesExceededError:
        logger.error(
            f"Max retries exhausted: {event_id=}, {subscription_id=}. Shipping to DLQ."
        )
        push_to_dlq(event_id, subscription.tenant_id, subscription_id, payload, err_msg)


def push_to_dlq(
    event_id: str,
    tenant_id: int,
    subscription_id: int,
    payload: dict,
    err_msg: str | None,
): ...
