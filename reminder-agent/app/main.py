
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.reminders import router as reminders_router
from app.database.database import Base, engine
from app.database import models
from app.core.scheduler import start_scheduler, shutdown_scheduler


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()

    yield

    shutdown_scheduler()


app = FastAPI(
    title="Reminder Agent API",
    description="Independent Reminder Agent for ATO integration",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "reminder-agent"
    }


app.include_router(reminders_router)
