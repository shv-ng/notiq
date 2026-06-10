import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from app.core import get_session
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

    try:
        session.add(new_tenant)
        session.commit()
        session.refresh(new_tenant)
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"fail to create tenant: {e}",
        )

    if not new_tenant or new_tenant.id is None:
        raise HTTPException(
            status_code=500,
            detail="fail to create tenant",
        )

    return TenantCreated(
        id=new_tenant.id,
        name=new_tenant.name,
        api_key_hash=new_tenant.api_key_hash,
    )


@router.get("/{id}", response_model=TenantRead)
def get_tenant(id: int, session: Session = Depends(get_session)):
    try:
        tenant = session.exec(
            select(Tenant).where(
                Tenant.id == id,
            )
        ).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"tenant not found, id: {id}",
        )

    return tenant


@router.delete("/{id}", status_code=204)
def delete_subscription(id: int, session: Session = Depends(get_session)):
    try:
        tenant = session.exec(
            select(Tenant).where(
                Tenant.id == id,
            )
        ).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"tenant not found, id: {id}",
        )

    session.delete(tenant)
    session.commit()

    return
