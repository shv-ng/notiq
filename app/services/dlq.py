import json

from sqlmodel import Session

from app.core import engine
from app.models import DeadLetterQueue


def push_to_dlq(
    event_id: str,
    tenant_id: int,
    subscription_id: int,
    payload: dict,
    err_msg: str | None,
    attempt_no: int = 1,
):
    payload_str = json.dumps(payload, separators=(",", ":"))

    with Session(engine) as session:
        session.add(
            DeadLetterQueue(
                tenant_id=tenant_id,
                subscription_id=subscription_id,
                event_id=event_id,
                payload=payload_str,
                err_msg=err_msg or "Unknown error",
                attempt_no=attempt_no,
            )
        )
        session.commit()
