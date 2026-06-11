from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.exc import DataError, IntegrityError
from sqlmodel import text

from app.api import (
    delivery_log_router,
    dlq_router,
    events_router,
    subscription_router,
    tenant_router,
)
from app.core import engine
from app.exceptions import (
    data_error_exception_handler,
    global_exception_handler,
    integrity_exception_handler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    yield


app = FastAPI(lifespan=lifespan)

app.add_exception_handler(IntegrityError, integrity_exception_handler)
app.add_exception_handler(DataError, data_error_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)


@app.get("/")
def health():
    return {"status": "ok"}


app.include_router(tenant_router)
app.include_router(subscription_router)
app.include_router(events_router)
app.include_router(dlq_router)
app.include_router(delivery_log_router)
