from contextlib import asynccontextmanager

import requests
from fastapi import Depends, FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from sqlmodel import Session, SQLModel, create_engine, select, text

from db import User

# Resource identifies this service in Tempo/Grafana
resource = Resource.create(
    {
        "service.name": "fastapi-demo",
        "service.version": "0.1.0",
    }
)

# Tracer provider
trace.set_tracer_provider(TracerProvider(resource=resource))

# Exporter -> Alloy (OTLP gRPC)
otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:4317",
    insecure=True,
)

span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

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


@app.get("/")
def root():
    return {"message": "Hello, OpenTelemetry!"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/users")
def read_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    for user in users:
        mock_user = requests.get("https://randomuser.me/api/")
    return users
