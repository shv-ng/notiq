import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core import get_session
from app.core.auth import get_current_tenant
from app.models import DeadLetterQueue
from app.schemas.dlq import DeadLetterQueueRead
from app.tasks import dispatch_event

router = APIRouter(prefix="/dlq", tags=["dead-letter-queue"])


@router.get("/", response_model=list[DeadLetterQueueRead])
def get_dlq(
    tenant_id: int = Depends(get_current_tenant),
    session: Session = Depends(get_session),
):
    dlq = session.exec(
        select(DeadLetterQueue).where(
            DeadLetterQueue.tenant_id == tenant_id,
            not DeadLetterQueue.is_resolved,
        )
    )
    return dlq


@router.post("/{id}/replay", status_code=204)
def replay_dlq(
    id: int,
    tenant_id: int = Depends(get_current_tenant),
    session: Session = Depends(get_session),
):
    query = select(DeadLetterQueue).where(
        DeadLetterQueue.tenant_id == tenant_id,
        DeadLetterQueue.id == id,
        not DeadLetterQueue.is_resolved,
    )

    dlq = session.exec(query).first()
    if not dlq:
        raise HTTPException(
            status_code=404,
            detail=f"dead letter queue record not found, id: {id}",
        )

    dlq.replayed_at = datetime.now(UTC)

    session.add(dlq)
    session.commit()
    session.refresh(dlq)

    payload = json.loads(dlq.payload)

    dispatch_event.delay(
        subscription_id=dlq.subscription_id,
        event_id=dlq.event_id,
        payload=payload,
    )

    return


@router.post("/{id}/resolve", status_code=204)
def resolve_dlq(
    id: int,
    tenant_id: int = Depends(get_current_tenant),
    session: Session = Depends(get_session),
):
    query = select(DeadLetterQueue).where(
        DeadLetterQueue.tenant_id == tenant_id,
        DeadLetterQueue.id == id,
        not DeadLetterQueue.is_resolved,
    )

    dlq = session.exec(query).first()
    if not dlq:
        raise HTTPException(
            status_code=404,
            detail=f"dead letter queue record not found, id: {id}",
        )

    dlq.is_resolved = True
    session.add(dlq)
    session.commit()

    return
