from sqlmodel import text
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    from api.core.db import engine

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"status": "ok"}
