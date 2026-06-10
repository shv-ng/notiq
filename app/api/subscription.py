from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from app.core import get_session
from app.models import Subscription
from app.schemas import SubscriptionCreate, SubscriptionRead

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("/", response_model=SubscriptionRead, status_code=201)
def create_subscription(
    subs: SubscriptionCreate, session: Session = Depends(get_session)
):
    new_subscription = Subscription(
        tenant_id=subs.tenant_id,
        event_type=subs.event_type,
        target_url=subs.target_url,
    )

    session.add(new_subscription)
    session.commit()
    session.refresh(new_subscription)

    return new_subscription


@router.get("/", response_model=list[SubscriptionRead])
def get_subscriptions(
    event_type: str | None = None, session: Session = Depends(get_session)
):
    tenant_id = 1  # TODO: get tenant id from auth header

    query = select(Subscription).where(
        Subscription.tenant_id == tenant_id,
        Subscription.is_active,
    )

    if event_type:
        query = query.where(Subscription.event_type == event_type)

    subscriptions = session.exec(query)

    return subscriptions


@router.get("/{id}", response_model=SubscriptionRead)
def get_subscription(id: int, session: Session = Depends(get_session)):
    tenant_id = 1  # TODO: get tenant id from auth header
    query = select(Subscription).where(
        Subscription.tenant_id == tenant_id,
        Subscription.id == id,
        Subscription.is_active,
    )

    try:
        subscription = session.exec(query).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"subscription not found, id: {id}",
        )

    return subscription


@router.delete("/{id}", status_code=204)
def delete_subscription(id: int, session: Session = Depends(get_session)):
    tenant_id = 1  # TODO: get tenant id from auth header
    query = select(Subscription).where(
        Subscription.tenant_id == tenant_id,
        Subscription.id == id,
        Subscription.is_active,
    )
    try:
        subscription = session.exec(query).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"subscription not found, id: {id}",
        )

    subscription.is_active = False
    session.add(subscription)
    session.commit()

    return
