from datetime import datetime

from pydantic import BaseModel, HttpUrl


class SubscriptionCreate(BaseModel):
    event_type: str = "event_type"
    target_url: HttpUrl


class SubscriptionRead(BaseModel):
    id: int
    tenant_id: int
    event_type: str
    target_url: HttpUrl
    created_at: datetime
