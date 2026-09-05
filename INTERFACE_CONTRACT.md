# Interface Contract — HH Goa Task 3

This defines the exact I/O shape each module must produce/consume. If your module matches this,
integration at the sync point is a one-line import swap. If it doesn't, we find out now, not at hour 60.

## A's module: `face_pipeline/search.py`

Must expose a single function:

```python
def find_match(image_path: str) -> dict:
    """
    Takes a path to a face image, returns a match record.
    Must raise `NoMatchFoundError` (define this) if no genuine match is found —
    do not return a fake/empty match silently.
    """
```

Return shape (dict, JSON-serializable):

```json
{
  "image_hash": "sha256 hex string of the input image bytes",
  "matched_post_url": "https://... (real, working URL)",
  "matched_platform": "instagram | linkedin | twitter | other",
  "confidence": 0.0,
  "timestamp": "ISO 8601 string, UTC"
}
```

## B's module: `blockchain/verify.py`

Must expose two functions:

```python
def register_match(data_hash: str, post_url: str) -> dict:
    """Writes a record on-chain. Returns tx receipt info."""

def verify_match(data_hash: str) -> dict:
    """Reads back the on-chain record for a given hash."""
```

`register_match` return shape:

```json
{
  "tx_hash": "0x...",
  "block_number": 12345,
  "chain": "polygon_amoy",
  "contract_address": "0x..."
}
```

`verify_match` return shape:

```json
{
  "verified": true,
  "post_url": "https://...",
  "block_number": 12345,
  "registered_at": "ISO 8601 string"
}
```

## Sync point checklist (hour 24)

- [ ] A's `find_match()` returns real data matching the shape above, tested on at least one real image
- [ ] B's `register_match()` / `verify_match()` work against Polygon Amoy testnet (or local Hardhat as fallback)
- [ ] C swaps `integration/stubs.py` imports for the real modules in `integration/main.py`
- [ ] Full pipeline run end-to-end on one real example, output captured for the demo recording

If A or B's shape doesn't match this doc, **change the code to match the doc**, not the other way around —
C's orchestrator and tamper-demo logic are already built against this contract.
