import hashlib

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlmodel import Session, select

from app.models import Tenant

from .db import get_session

API_KEY_NAME = "X-Api-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_current_tenant(
    api_key: str = Security(api_key_header), session: Session = Depends(get_session)
) -> int:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key header",
        )

    hashed_key = hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    tenant = session.exec(
        select(Tenant).where(Tenant.api_key_hash == hashed_key)
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    assert tenant.id is not None, "Database failed to generate a tenant ID"

    return tenant.id
