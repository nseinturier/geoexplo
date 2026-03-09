import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from relational.database import get_db
from relational.models import Scenario, StabilitySnapshot

router = APIRouter()


class ScenarioFork(BaseModel):
    name: str
    description: str = ""


def _scenario_to_dict(s: Scenario) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "description": s.description,
        "forked_from": s.forked_from,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "is_production": s.is_production,
    }


@router.get("")
def list_scenarios(db: Session = Depends(get_db)):
    return [_scenario_to_dict(s) for s in db.query(Scenario).all()]


@router.post("/fork")
def fork_scenario(body: ScenarioFork, db: Session = Depends(get_db)):
    scenario_id = body.name.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8]
    scenario = Scenario(
        id=scenario_id,
        name=body.name,
        description=body.description,
        forked_from="production",
        created_at=datetime.utcnow(),
        is_production=False,
    )
    db.add(scenario)

    # Copy latest production snapshots into this scenario
    prod_snapshots = (
        db.query(StabilitySnapshot)
        .filter(StabilitySnapshot.scenario_id == "production")
        .all()
    )
    seen_uids = set()
    for snap in prod_snapshots:
        if snap.object_uid in seen_uids:
            continue
        seen_uids.add(snap.object_uid)
        cloned = StabilitySnapshot(
            id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
            scenario_id=scenario_id,
            object_uid=snap.object_uid,
            stability_score=snap.stability_score,
            water_stress=snap.water_stress,
            notes=f"Forked from production",
        )
        db.add(cloned)

    db.commit()
    db.refresh(scenario)
    return _scenario_to_dict(scenario)


@router.get("/{scenario_id}/compare")
def compare_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """Compare latest stability scores in scenario vs production."""
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    def latest_scores(sid: str) -> dict[str, float]:
        rows = (
            db.query(StabilitySnapshot)
            .filter(StabilitySnapshot.scenario_id == sid)
            .order_by(StabilitySnapshot.timestamp.desc())
            .all()
        )
        scores = {}
        for row in rows:
            if row.object_uid not in scores:
                scores[row.object_uid] = row.stability_score
        return scores

    prod_scores = latest_scores("production")
    scen_scores = latest_scores(scenario_id)

    all_uids = set(prod_scores) | set(scen_scores)
    diff = []
    for uid in all_uids:
        prod_val = prod_scores.get(uid)
        scen_val = scen_scores.get(uid)
        if prod_val is not None and scen_val is not None:
            delta = scen_val - prod_val
            diff.append({"uid": uid, "production": prod_val, "scenario": scen_val, "delta": delta})

    return sorted(diff, key=lambda x: abs(x["delta"]), reverse=True)


@router.get("/snapshots/{object_uid}")
def get_snapshots(object_uid: str, db: Session = Depends(get_db)):
    """Return all stability snapshots for a given object uid, all scenarios."""
    rows = (
        db.query(StabilitySnapshot)
        .filter(StabilitySnapshot.object_uid == object_uid)
        .order_by(StabilitySnapshot.timestamp.asc())
        .all()
    )
    return [
        {
            "id": str(r.id),
            "timestamp": r.timestamp.isoformat(),
            "scenario_id": r.scenario_id,
            "object_uid": r.object_uid,
            "stability_score": r.stability_score,
            "water_stress": r.water_stress,
            "notes": r.notes,
        }
        for r in rows
    ]


@router.delete("/{scenario_id}")
def delete_scenario(scenario_id: str, db: Session = Depends(get_db)):
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if scenario.is_production:
        raise HTTPException(status_code=400, detail="Cannot delete production scenario")

    db.query(StabilitySnapshot).filter(StabilitySnapshot.scenario_id == scenario_id).delete()
    db.delete(scenario)
    db.commit()
    return {"deleted": scenario_id}
