from pydantic import BaseModel


class TenantCreate(BaseModel):
    name: str = "name"


class TenantRead(BaseModel):
    id: int
    name: str


class TenantCreated(BaseModel):
    id: int
    name: str
    api_key: str
