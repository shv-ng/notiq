from datetime import datetime

from pydantic import BaseModel


class SubscriptionCreate(BaseModel):
    tenant_id: int = 0
    event_type: str = "event_type"
    target_url: str = "target_url"


class SubscriptionRead(BaseModel):
    id: int
    tenant_id: int
    event_type: str
    target_url: str
    created_at: datetime
