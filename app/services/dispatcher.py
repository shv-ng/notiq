import json
import time

import httpx
from sqlmodel import Session

from app.core import engine, settings
from app.models import Subscription
from app.models.delivery_log import DeliveryLog

from .signer import sign_payload


async def deliver_event(
    subscription: Subscription, event_id: str, payload: dict, attempt_no: int = 1
) -> tuple[bool, int | None, str | None]:
    assert subscription.id is not None, "subscription don't have id"

    raw_payload = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    signature = sign_payload(raw_payload, settings.SECRET_KEY)

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
    }

    success: bool = False
    http_status: int | None = None
    err_msg: str | None = None

    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
            response = await client.post(
                subscription.target_url,
                json=payload,
                headers=headers,
            )

            http_status = response.status_code
            success = 200 <= response.status_code < 300
    except httpx.TimeoutException as e:
        err_msg = str(e)
    except httpx.ConnectError as e:
        err_msg = str(e)
    except httpx.RequestError as e:
        err_msg = str(e)
    finally:
        end = time.perf_counter()
        response_time_ms = int((end - start) * 1000)

        with Session(engine) as session:
            delivery_log = DeliveryLog(
                tenant_id=subscription.tenant_id,
                subscription_id=subscription.id,
                event_id=event_id,
                attempt_no=attempt_no,
                http_status=http_status,
                response_time_ms=response_time_ms,
                err_msg=err_msg,
                success=success,
            )

            session.add(delivery_log)
            session.commit()

    return (success, http_status, err_msg)
