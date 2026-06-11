import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from app.core import get_current_tenant, get_session
from app.models import Tenant
from app.schemas import TenantCreate, TenantCreated, TenantRead

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("/", response_model=TenantCreated, status_code=201)
def create_tenant(tenant: TenantCreate, session: Session = Depends(get_session)):
    api_key = secrets.token_hex(32)
    api_key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    new_tenant = Tenant(
        name=tenant.name,
        api_key_hash=api_key_hash,
    )

    session.add(new_tenant)
    session.commit()
    session.refresh(new_tenant)

    assert new_tenant.id is not None, "Database failed to generate a tenant ID"

    return TenantCreated(
        id=new_tenant.id,
        name=new_tenant.name,
        api_key=api_key,
    )


@router.get("/me", response_model=TenantRead)
def get_tenant(
    id: int = Depends(get_current_tenant),
    session: Session = Depends(get_session),
):
    query = select(Tenant).where(
        Tenant.id == id,
    )
    try:
        tenant = session.exec(query).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"tenant not found, id: {id}",
        )

    return tenant


@router.delete("/", status_code=204)
def delete_tenant(
    id: int = Depends(get_current_tenant),
    session: Session = Depends(get_session),
):
    query = select(Tenant).where(Tenant.id == id)
    try:
        tenant = session.exec(query).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"tenant not found, id: {id}",
        )

    session.delete(tenant)
    session.commit()

    return
