from datetime import datetime

from pydantic import BaseModel


class DeadLetterQueueRead(BaseModel):
    id: int
    subscription_id: int
    event_id: str
    payload: str
    err_msg: str
    attempt_no: int
    created_at: datetime
    replayed_at: datetime | None
