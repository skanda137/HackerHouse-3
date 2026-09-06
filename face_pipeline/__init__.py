"""
face_pipeline.py
Face detection + embedding extraction using insightface (buffalo_l / ArcFace).
Confirmed working: model downloads from GitHub releases, 512-dim embeddings.
"""
import os
import tempfile

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


def get_face(image_path: str, min_det_score: float = 0.5):
    """
    Returns the insightface Face object (embedding + bbox) for the largest/
    most confident face in the image. Returns None if no face is detected
    above min_det_score.
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

    return best


def get_embedding(image_path: str, min_det_score: float = 0.5):
    """
    Returns the 512-d embedding of the largest/most confident face in the image.
    Returns None if no face is detected above min_det_score.
    """
    face = get_face(image_path, min_det_score)
    return face.embedding if face is not None else None  # np.ndarray, shape (512,)


def crop_to_face(image_path: str, bbox, margin: float = 0.3) -> str:
    """
    Crops image_path to the given face bbox (x1, y1, x2, y2), padded by
    `margin` (fraction of face width/height added on each side), writes the
    crop to a new temp file, and returns its path. Caller is responsible for
    deleting the temp file.

    Used to strip surrounding context (clothing, background) before reverse
    image search — see README "Known limitations": Google Lens matches on
    the most visually distinctive object in frame, not the face specifically.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    h, w = img.shape[:2]
    x1, y1, x2, y2 = bbox
    mx, my = (x2 - x1) * margin, (y2 - y1) * margin
    x1 = max(0, int(x1 - mx))
    y1 = max(0, int(y1 - my))
    x2 = min(w, int(x2 + mx))
    y2 = min(h, int(y2 + my))

    crop = img[y1:y2, x1:x2]
    fd, out_path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    cv2.imwrite(out_path, crop)
    return out_path


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
