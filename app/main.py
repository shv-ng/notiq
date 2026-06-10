import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlmodel import text

from app.api import events_router, subscription_router, tenant_router
from app.core import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    yield


app = FastAPI(lifespan=lifespan)
logger = logging.getLogger("uvicorn.error")

app.include_router(subscription_router)
app.include_router(tenant_router)
app.include_router(events_router)


@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global crash intercepted: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


@app.get("/")
def health():
    return {"status": "ok"}
