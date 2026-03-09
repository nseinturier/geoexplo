from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Any

from graph import queries

router = APIRouter()


class PatchBody(BaseModel):
    model_config = {"extra": "allow"}


@router.get("")
def list_objects(type: str | None = Query(None)):
    return queries.get_all_nodes(node_type=type)


@router.get("/edges/all")
def list_all_edges():
    """Return all graph edges for bulk visualization."""
    return queries.get_all_edges()


@router.get("/{uid}")
def get_object(uid: str):
    node = queries.get_node_with_relationships(uid)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.patch("/{uid}")
def patch_object(uid: str, body: PatchBody):
    props = body.model_dump(exclude_unset=True)
    if not props:
        raise HTTPException(status_code=400, detail="No properties to update")
    updated = queries.update_node_properties(uid, props)
    if not updated:
        raise HTTPException(status_code=404, detail="Node not found")
    return updated


@router.get("/{uid}/neighbors")
def get_neighbors(uid: str):
    return queries.get_neighbors(uid)
