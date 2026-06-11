from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from app.core import get_current_tenant, get_session
from app.models import Subscription
from app.schemas import SubscriptionCreate, SubscriptionRead

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("/", response_model=SubscriptionRead, status_code=201)
def create_subscription(
    subs: SubscriptionCreate,
    tenant_id: int = Depends(get_current_tenant),
    session: Session = Depends(get_session),
):
    data = subs.model_dump(mode="json")
    new_subscription = Subscription(**data)
    new_subscription.tenant_id = tenant_id

    session.add(new_subscription)
    session.commit()
    session.refresh(new_subscription)

    return new_subscription


@router.get("/", response_model=list[SubscriptionRead])
def get_subscriptions(
    event_type: str | None = None,
    tenant_id: int = Depends(get_current_tenant),
    session: Session = Depends(get_session),
):
    query = select(Subscription).where(
        Subscription.tenant_id == tenant_id,
        Subscription.is_active,
    )

    if event_type:
        query = query.where(Subscription.event_type == event_type)

    subscriptions = session.exec(query)

    return subscriptions


@router.get("/{id}", response_model=SubscriptionRead)
def get_subscription(
    id: int,
    tenant_id: int = Depends(get_current_tenant),
    session: Session = Depends(get_session),
):
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
def delete_subscription(
    id: int,
    tenant_id: int = Depends(get_current_tenant),
    session: Session = Depends(get_session),
):
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
