"""
face_pipeline.py
Face detection + embedding extraction using insightface (buffalo_l / ArcFace).
Confirmed working: model downloads from GitHub releases, 512-dim embeddings.
"""
import cv2
import numpy as np
from insightface.app import FaceAnalysis

_app = None


def get_app():
    """Lazy-load the model once per process."""
    global _app
    if _app is None:
        _app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        _app.prepare(ctx_id=0, det_size=(640, 640))
    return _app


def get_embedding(image_path: str, min_det_score: float = 0.5):
    """
    Returns the 512-d embedding of the largest/most confident face in the image.
    Returns None if no face is detected above min_det_score.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    app = get_app()
    faces = app.get(img)
    if not faces:
        return None

    # pick the highest-confidence detection (handles group photos)
    best = max(faces, key=lambda f: f.det_score)
    if best.det_score < min_det_score:
        return None

    return best.embedding  # np.ndarray, shape (512,)


def get_embedding_from_array(img_array: np.ndarray, min_det_score: float = 0.5):
    """Same as get_embedding but takes a decoded image array (used for downloaded candidates)."""
    app = get_app()
    faces = app.get(img_array)
    if not faces:
        return None
    best = max(faces, key=lambda f: f.det_score)
    if best.det_score < min_det_score:
        return None
    return best.embedding


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
