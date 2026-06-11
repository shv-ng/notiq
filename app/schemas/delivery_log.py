from datetime import datetime

from pydantic import BaseModel, computed_field


class DeliveryLogRead(BaseModel):
    id: int
    tenant_id: int
    subscription_id: int
    event_id: str
    attempt_no: int
    http_status: int | None
    response_time_ms: int | None
    err_msg: str | None
    success: bool
    created_at: datetime

    @computed_field
    @property
    def is_retried(self) -> bool:
        return self.attempt_no > 1


class DeliveryLogStats(BaseModel):
    total_attempts: int
    success_count: int
    failure_count: int
    avg_response_time_ms: int
