from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from app.core import get_current_tenant, get_session
from app.models import Subscription, Tenant
from app.schemas import EventCreate
from app.tasks import dispatch_event

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", status_code=202)
def create_events(
    events: EventCreate,
    response: Response,
    tenant_id: int = Depends(get_current_tenant),
    session: Session = Depends(get_session),
):
    try:
        session.exec(select(Tenant).where(Tenant.id == tenant_id)).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"tenant not found, id: {tenant_id}",
        )
    subscribers = session.exec(
        select(Subscription).where(
            Subscription.is_active,
            Subscription.tenant_id == tenant_id,
            Subscription.event_type == events.event_type,
        )
    ).all()

    if not subscribers:
        response.status_code = 200
        return {"status": "skipped", "reason": "no subscribers"}

    for subscriber in subscribers:
        dispatch_event.delay(
            subscription_id=subscriber.id,
            event_id=events.event_id,
            payload=events.payload,
        )

    return {
        "status": "accepted",
        "event_id": events.event_id,
    }
