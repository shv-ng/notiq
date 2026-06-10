from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class DeliveryLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    tenant_id: int = Field(foreign_key="tenant.id", index=True)
    subscription_id: int = Field(foreign_key="subscription.id", index=True)
    event_id: str = Field(index=True)

    attempt_no: int = Field(default=1)
    http_status: int | None = Field(default=None)
    response_time_ms: int | None = Field(default=None)

    err_msg: str | None = Field(default=None)
    success: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
