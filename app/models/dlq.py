from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class DeadLetterQueue(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenant.id", index=True)

    subscription_id: int = Field(foreign_key="subscription.id", index=True)
    event_id: str = Field(index=True)
    payload: str = Field(index=True)
    err_msg: str = Field(index=True)
    attempt_no: int = Field(index=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    replayed_at: datetime | None = Field(default=None)
    is_resolved: bool = Field(default=False)
