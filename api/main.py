import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from neomodel import config as neomodel_config

from relational.database import engine, Base
from routers import objects, events, scenarios, simulation


def configure_neo4j():
    url = os.getenv("NEO4J_URL", "bolt://neo4j:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    # neomodel expects: bolt://user:pass@host:port
    bolt_url = url.replace("bolt://", f"bolt://{user}:{password}@")
    neomodel_config.DATABASE_URL = bolt_url


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_neo4j()
    # Create Postgres tables
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Geopolitical Intelligence API",
    description="Palantir-inspired conflict scenario modelling platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(objects.router, prefix="/objects", tags=["objects"])
app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])
app.include_router(simulation.router, prefix="/cascade", tags=["cascade"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/analytics/most_vulnerable")
def most_vulnerable():
    from graph.queries import get_most_vulnerable_infrastructure
    return get_most_vulnerable_infrastructure()


@app.get("/analytics/chokepoints")
def chokepoints():
    from graph.queries import get_chokepoints_with_dependency_count
    return get_chokepoints_with_dependency_count()


@app.get("/analytics/actor_risk/{uid}")
def actor_risk(uid: str):
    from graph.queries import get_actor_risk_score
    return get_actor_risk_score(uid)


@app.post("/analytics/notes")
def save_analyst_note(body: dict):
    from relational.database import SessionLocal
    from relational.models import AnalystNote
    import uuid
    from datetime import datetime
    db = SessionLocal()
    try:
        note = AnalystNote(
            id=uuid.uuid4(),
            object_uid=body.get("object_uid", ""),
            note=body.get("note", ""),
            author=body.get("author", "analyst"),
            created_at=datetime.utcnow(),
        )
        db.add(note)
        db.commit()
        return {"status": "saved"}
    finally:
        db.close()
