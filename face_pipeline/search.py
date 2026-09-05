"""
face_pipeline/search.py
Implements find_match() per INTERFACE_CONTRACT.md: embed the input face,
enforce consent BEFORE any search, run reverse image search, re-verify
candidates by actual face similarity, and return the best genuine match.
"""
import hashlib
from datetime import datetime, timezone

from face_pipeline import get_embedding
from consent_gate import check_consent, ConsentRequiredError
from reverse_search import reverse_image_search
from verify_match import verify_candidates

# Minimum ArcFace cosine similarity to report a search result as a genuine
# identity match. This is deliberately higher than verify_match's internal
# candidate filter (0.40, in verify_match.py) — that filter only decides
# "a face was detected in this candidate image and is worth considering."
# This constant decides "confident enough to call it a match and write it
# to the blockchain." Not yet validated against a labeled set of known-
# match / known-non-match pairs — tune before the demo and record what you
# tuned it against in the README's known-limitations section.
MATCH_CONFIDENCE_THRESHOLD = 0.6


class NoMatchFoundError(Exception):
    """Raised by find_match when no candidate clears MATCH_CONFIDENCE_THRESHOLD."""
    pass


def _platform_from_candidate(candidate: dict) -> str:
    text = f"{candidate.get('link') or ''} {candidate.get('source') or ''}".lower()
    if "linkedin.com" in text:
        return "linkedin"
    if "instagram.com" in text:
        return "instagram"
    if "twitter.com" in text or "x.com" in text:
        return "twitter"
    return "other"


def find_match(image_path: str) -> dict:
    """
    Takes a path to a face image, returns a match record (see
    INTERFACE_CONTRACT.md for the exact shape).

    Raises:
        ConsentRequiredError: the face isn't on the consent allowlist.
            Checked BEFORE any search call — no search happens on a
            non-consenting face, not even to "just see what's there."
        NoMatchFoundError: no face was detected, or no search candidate
            cleared MATCH_CONFIDENCE_THRESHOLD. Never returns a low-
            confidence guess silently.
    """
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    image_hash = hashlib.sha256(image_bytes).hexdigest()

    embedding = get_embedding(image_path)
    if embedding is None:
        raise NoMatchFoundError(f"No face detected in {image_path}.")

    is_consented, member_name = check_consent(embedding)
    if not is_consented:
        raise ConsentRequiredError(
            f"Face in {image_path} is not on the consent allowlist. "
            "Register it first with register_cli.py before running a search."
        )

    candidates = reverse_image_search(image_path)
    verified = verify_candidates(embedding, candidates)

    strong_matches = [c for c in verified if c["confidence"] >= MATCH_CONFIDENCE_THRESHOLD]
    if not strong_matches:
        raise NoMatchFoundError(
            f"No candidate for {image_path} (consented member: {member_name}) "
            f"cleared confidence threshold {MATCH_CONFIDENCE_THRESHOLD}."
        )

    best = strong_matches[0]  # verify_candidates() already sorts best-first

    return {
        "image_hash": image_hash,
        "matched_post_url": best["link"],
        "matched_platform": _platform_from_candidate(best),
        "confidence": best["confidence"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
