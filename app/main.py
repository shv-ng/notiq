import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError, IntegrityError
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


@app.exception_handler(IntegrityError)
def integrity_exception_handler(request: Request, exc: Exception):
    orig_error = getattr(exc, "orig", None)
    error_name = type(orig_error).__name__

    detail_msg = getattr(orig_error, "diag", None)
    db_detail = detail_msg.message_detail if detail_msg else str(orig_error)

    logger.warning(f"Database Integrity Violation ({error_name}): {db_detail}")

    match error_name:
        case "ForeignKeyViolation":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": "Invalid reference: A provided ID does not exist.",
                    "database_detail": db_detail,
                },
            )

        case "UniqueViolation":
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "detail": "Conflict: This record already exists.",
                    "database_detail": db_detail,
                },
            )

        case "NotNullViolation":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": "Missing required data.",
                    "database_detail": db_detail,
                },
            )

        case "CheckViolation":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": "Data constraint violation.",
                    "database_detail": db_detail,
                },
            )

        case _:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": "Database integrity error.",
                    "database_detail": db_detail,
                },
            )


@app.exception_handler(DataError)
def data_error_exception_handler(request: Request, exc: Exception):
    orig_error = getattr(exc, "orig", None)
    logger.warning(f"Database DataError intercepted: {orig_error}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Invalid data format or length provided to the database."},
    )


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
