import logging
from contextlib import asynccontextmanager

import requests
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from sqlmodel import Session, SQLModel, create_engine, select, text

from db import User
from telemetry import setup_opentelemetry

setup_opentelemetry()

LoggingInstrumentor().instrument(
    set_logging_format=True,
)

logger = logging.getLogger(__name__)

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def insert_initial_data():
    from db import User

    with Session(engine) as session:
        session.exec(text("DELETE FROM user"))
        for i in range(5):
            user = User(name=f"User {i + 1}")
            session.add(user)
        session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    insert_initial_data()
    yield


# FastAPI app
app = FastAPI(lifespan=lifespan)


FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()
SQLAlchemyInstrumentor().instrument(engine=engine)


@app.exception_handler(Exception)
async def unicorn_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )


@app.get("/")
def root():
    return {"message": "Hello, OpenTelemetry!"}


@app.get("/health")
def health():
    logger.info("Health check endpoint called")
    return {"status": "ok"}


@app.get("/users")
def read_users(session: Session = Depends(get_session)):
    logger.info("Fetching users from database")
    users = session.exec(select(User)).all()
    logger.info(f"Retrieved {len(users)} users")
    for user in users:
        logger.debug(f"Processing user: {user.name}")
        requests.get("https://randomuser.me/api/")
    logger.error("Simulated error for testing purposes")
    raise Exception("Simulated error for testing purposes")
