from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import text

from app.api import subscription_router, tenant_router
from app.core import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    yield


app = FastAPI(lifespan=lifespan)

app.include_router(subscription_router)
app.include_router(tenant_router)


@app.get("/")
def health():
    return {"status": "ok"}
