import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger("uvicorn.error")


async def integrity_exception_handler(request: Request, exc: Exception):
    orig_error = getattr(exc, "orig", None)
    error_name = type(orig_error).__name__

    detail_msg = getattr(orig_error, "diag", None)
    db_detail = detail_msg.message_detail if detail_msg else str(orig_error)

    logger.warning(f"Database Integrity Violation ({error_name}): {db_detail}")

    http_status = status.HTTP_400_BAD_REQUEST
    if error_name == "UniqueViolation":
        http_status = status.HTTP_409_CONFLICT

    messages = {
        "ForeignKeyViolation": "Invalid reference: A provided ID does not exist.",
        "UniqueViolation": "Conflict: This record already exists.",
        "NotNullViolation": "Missing required data.",
        "CheckViolation": "Data constraint violation.",
    }

    return JSONResponse(
        status_code=http_status,
        content={
            "detail": messages.get(error_name, "Database integrity error."),
            "database_detail": db_detail,
        },
    )


async def data_error_exception_handler(request: Request, exc: Exception):
    orig_error = getattr(exc, "orig", None)
    logger.warning(f"Database DataError intercepted: {orig_error}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Invalid data format or length provided to the database."},
    )


async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global crash intercepted: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )
