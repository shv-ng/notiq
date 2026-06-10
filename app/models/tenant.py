from sqlmodel import Field, SQLModel


class Tenant(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    api_key_hash: str = Field(index=True, unique=True)
