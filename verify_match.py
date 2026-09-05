"""
verify_match.py
This is what makes your "confidence score" real instead of decorative.
Reverse image search gives you visual-similarity candidates; this module
re-runs face embedding on each candidate and measures actual face distance
against the query. Only this number should ever be labeled "confidence."
"""
import cv2
import numpy as np
import requests
from face_pipeline import get_embedding_from_array, cosine_similarity


def _download_image_array(url: str, timeout: int = 10):
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        arr = np.frombuffer(resp.content, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None


def verify_candidates(query_embedding: np.ndarray, candidates: list, threshold: float = 0.40):
    """
    candidates: list of dicts from reverse_search.reverse_image_search()
    Returns candidates enriched with a real "confidence" (cosine similarity
    of face embeddings), sorted best-first, filtered to only those where a
    face was actually detected and matched above `threshold`.

    threshold=0.40 is a reasonable starting point for ArcFace cosine
    similarity — tune it against a few known-match / known-non-match pairs
    from your own test photos before the demo. Don't ship the default
    number unvalidated; state in your README what you tuned it against.
    """
    verified = []
    for cand in candidates:
        img_url = cand.get("image") or cand.get("thumbnail")
        if not img_url:
            continue
        img = _download_image_array(img_url)
        if img is None:
            continue
        emb = get_embedding_from_array(img)
        if emb is None:
            continue  # no face in this candidate image — not a face match
        sim = cosine_similarity(query_embedding, emb)
        print(
            "Candidate:",
            cand.get("title"),
            "| Similarity:",
            round(sim, 4)
        )
        if sim >= threshold:
            verified.append({**cand, "confidence": round(sim, 4)})

    verified.sort(key=lambda c: c["confidence"], reverse=True)
    return verified
