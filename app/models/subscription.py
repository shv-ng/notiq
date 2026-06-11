from datetime import UTC, datetime

from sqlmodel import Field, SQLModel, UniqueConstraint


class Subscription(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "event_type", "target_url", name="unique_tenant_event_url"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenant.id", index=True)

    event_type: str
    target_url: str

    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
