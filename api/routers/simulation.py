from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from relational.database import get_db
from services.cascade import run_cascade
from graph.queries import get_shortest_path

router = APIRouter()


class SimulateBody(BaseModel):
    source_uid: str
    impact: float = 0.5
    max_depth: int = 6
    persist: bool = False
    scenario_id: str = "production"


@router.post("/simulate")
def simulate_cascade(body: SimulateBody, db: Session = Depends(get_db)):
    results = run_cascade(
        source_uid=body.source_uid,
        impact=body.impact,
        max_depth=body.max_depth,
        persist=body.persist,
        scenario_id=body.scenario_id,
        db=db if body.persist else None,
    )
    return {"source_uid": body.source_uid, "impact": body.impact, "affected": results}


@router.get("/path")
def influence_path(
    from_uid: str = Query(..., alias="from"),
    to_uid: str = Query(..., alias="to"),
):
    path = get_shortest_path(from_uid, to_uid)
    return {"from": from_uid, "to": to_uid, "path": path}
