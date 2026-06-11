from fastapi import APIRouter, Depends
from sqlmodel import Session, case, col, func, select

from app.core import get_session
from app.models import DeliveryLog
from app.schemas import DeliveryLogRead
from app.schemas.delivery_log import DeliveryLogStats

router = APIRouter(prefix="/delivery-logs", tags=["delivery-logs"])


@router.get("/", response_model=list[DeliveryLogRead])
def get_delivery_logs(
    event_id: str | None = None,
    subscription_id: int | None = None,
    success: bool | None = None,
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_session),
):
    limit = min(limit, 200)

    tenant_id = 1  # TODO: get tenant id from auth header
    query = (
        select(DeliveryLog)
        .where(DeliveryLog.tenant_id == tenant_id)
        .order_by(col(DeliveryLog.created_at).desc())
        .limit(limit)
        .offset(offset)
    )
    if event_id is not None:
        query = query.where(DeliveryLog.event_id == event_id)
    if subscription_id is not None:
        query = query.where(DeliveryLog.subscription_id == subscription_id)
    if success is not None:
        query = query.where(DeliveryLog.success == success)

    delivery_logs = session.exec(query).all()
    return delivery_logs


@router.get("/stats", response_model=DeliveryLogStats)
def get_delivery_log_stats(
    session: Session = Depends(get_session),
):
    tenant_id = 1  # TODO: get tenant id from auth header

    query = select(
        func.coalesce(func.count(), 0).label("total_attempts"),
        func.coalesce(
            func.sum(
                case(
                    (DeliveryLog.success, 1),
                    else_=0,
                )
            ),
            0,
        ).label("success_count"),
        func.coalesce(
            func.sum(
                case(
                    (not DeliveryLog.success, 1),
                    else_=0,
                )
            ),
            0,
        ).label("failure_count"),
        func.coalesce(func.avg(DeliveryLog.response_time_ms), 0).label(
            "avg_response_time_ms"
        ),
    ).where(DeliveryLog.tenant_id == tenant_id)

    total_attempts, success_count, failure_count, avg_response_time_ms = session.exec(
        query
    ).one()

    return DeliveryLogStats(
        total_attempts=total_attempts,
        success_count=success_count,
        failure_count=failure_count,
        avg_response_time_ms=avg_response_time_ms,
    )
