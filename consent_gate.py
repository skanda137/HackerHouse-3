"""
consent_gate.py
Structural enforcement, not a verbal promise: the pipeline refuses to run
on any face that isn't in the pre-registered, consenting allowlist.

registry.json format:
{
  "members": [
    {"name": "Alice", "embedding": [...512 floats...]}
  ]
}

Build the registry once per team member with register_member(), using a
photo they've explicitly agreed to use for the demo.
"""
import json
import os
import numpy as np
from face_pipeline import get_embedding, cosine_similarity

REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "registry.json")
MATCH_THRESHOLD = 0.45  # cosine similarity floor for "this is the same registered person"


def _load_registry():
    if not os.path.exists(REGISTRY_PATH):
        return {"members": []}
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def _save_registry(registry):
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f)


def register_member(name: str, consent_photo_path: str):
    """Call this once per team member, on a photo they've agreed to use."""
    emb = get_embedding(consent_photo_path)
    if emb is None:
        raise ValueError(f"No face detected in {consent_photo_path} — registration failed.")
    registry = _load_registry()
    registry["members"] = [m for m in registry["members"] if m["name"] != name]
    registry["members"].append({"name": name, "embedding": emb.tolist()})
    _save_registry(registry)
    print(f"Registered {name}.")


def check_consent(query_embedding: np.ndarray):
    """
    Returns (True, name) if the query face matches a registered consenting member.
    Returns (False, None) otherwise — caller MUST refuse to proceed on False.
    """
    registry = _load_registry()
    for member in registry["members"]:
        sim = cosine_similarity(query_embedding, np.array(member["embedding"]))
        if sim >= MATCH_THRESHOLD:
            return True, member["name"]
    return False, None
