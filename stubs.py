import hashlib
import time
from datetime import datetime, timezone


class NoMatchFoundError(Exception):
    """Raised by find_match when no genuine match is found for the input image."""
    pass


# In-memory fake "chain" so register/verify are consistent within one run
_fake_chain_state = {}


def find_match(image_path: str) -> dict:
    """
    STUB. Real version lives in face_pipeline/search.py (Person A).
    Returns a fake but well-formed match record so downstream code can be tested.
    """
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    image_hash = hashlib.sha256(image_bytes).hexdigest()

    return {
        "image_hash": image_hash,
        "matched_post_url": "https://example.com/fake-matched-post-for-testing",
        "matched_platform": "instagram",
        "confidence": 0.91,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def register_match(data_hash: str, post_url: str) -> dict:
    """
    STUB. Real version lives in blockchain/verify.py (Person B).
    Simulates a blockchain write with a fake but consistent tx record.
    """
    fake_tx_hash = "0x" + hashlib.sha256(f"{data_hash}{post_url}{time.time()}".encode()).hexdigest()
    fake_block = 1_000_000 + len(_fake_chain_state)

    record = {
        "tx_hash": fake_tx_hash,
        "block_number": fake_block,
        "chain": "local_stub",
        "contract_address": "0x0000000000000000000000000000000000dEaD",
    }

    _fake_chain_state[data_hash] = {
        "post_url": post_url,
        "block_number": fake_block,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }

    return record


def verify_match(data_hash: str) -> dict:
    """
    STUB. Real version lives in blockchain/verify.py (Person B).
    Reads back from the in-memory fake chain state.
    """
    record = _fake_chain_state.get(data_hash)
    if record is None:
        return {"verified": False, "post_url": None, "block_number": None, "registered_at": None}

    return {
        "verified": True,
        "post_url": record["post_url"],
        "block_number": record["block_number"],
        "registered_at": record["registered_at"],
    }
