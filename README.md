# HH Goa 2026 — Task 3: Face Identification & Blockchain Verification

## What this does

Takes a face image, finds a real matching social media post via reverse image search,
and writes a tamper-evident record of that match to a blockchain — then re-verifies
the recorded data against the on-chain copy.

Pipeline: **face scan → web/social search → blockchain registration → re-verification**

Privacy note: raw face images and biometric embeddings are never written on-chain.
Only a SHA-256 hash of the input and the matched post URL are committed.

## Demo subjects

Consent is structurally enforced: `find_match()` (`face_pipeline/search.py`) calls
`consent_gate.check_consent()` on the extracted face embedding *before* any search runs,
and raises `ConsentRequiredError` if the face isn't on the allowlist. This has been
verified by reading the actual function body, not assumed from a docstring.

One team member is registered so far (via `register_cli.py`) and the full pipeline has
been run end-to-end against that real, consented face — `python main.py <photo>`
correctly ran real face detection, passed the consent check, ran a real reverse image
search, and correctly reported no match rather than a false positive (see Known
Limitations for why). Demo subjects are team members' own faces, matched against their
own real, publicly-known social accounts (self-consent) — for the demo recording, use a
photo that's already posted on that account, not a fresh one (see Known Limitations).

## How to run

```bash
git clone <repo_url>
cd HackerHouse-3
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Blockchain setup (see blockchain/ for details)
cd blockchain && npm install && cd ..

cp .env.example .env
# fill in .env with your API keys / RPC URL — see .env.example for what's required

python main.py path/to/face_image.jpg
```

To run the tamper-evidence demo separately:

```bash
python tamper_demo.py
```

## Which blockchain

**Polygon Amoy testnet** (chainId 80002), via a Solidity contract (`blockchain/contracts/MatchRegistry.sol`)
deployed and managed with Hardhat. `registerMatch(bytes32 dataHash, string postUrl)` writes a record
(reverts with the custom error `AlreadyRegistered` if that exact hash was already registered — records
can't be silently overwritten); `verifyMatch(bytes32 dataHash)` reads one back.

**Local Hardhat network — confirmed working.** `tamper_demo.py` has been run end-to-end for real
against a local node (`npm run node` + `npm run deploy:local` inside `blockchain/`): register → verify →
tamper → re-verify, no stubs involved. Set `BLOCKCHAIN_NETWORK=hardhat_local` in `.env` to use it.

**Amoy testnet — not yet deployed.** No `blockchain/deployments/amoy.json` exists yet. Deploy with
`npm run deploy:amoy` from `blockchain/` once `RPC_URL` and `PRIVATE_KEY` (a funded Amoy wallet) are
set in `.env`; the script writes the deployed address + ABI there automatically, and `verify.py` reads
it with no code changes needed. Set `BLOCKCHAIN_NETWORK=polygon_amoy` in `.env` to point at it once deployed.

## Architecture

Flat layout at the repo root, except for `blockchain/`:

- `face_pipeline/` — `__init__.py` (face detection/encoding) + `search.py` (`find_match()` orchestration) (Person A)
- `reverse_search.py`, `verify_match.py` — reverse image search + real confidence scoring (Person A)
- `consent_gate.py`, `register_cli.py` — consent allowlist, enforced inside `face_pipeline/search.py` (Person A)
- `blockchain/` — Solidity contract, Hardhat project, and `verify.py`/`cli.py` register/verify logic (Person B)
- `main.py`, `tamper_demo.py` — orchestrator CLI + tamper-evidence demo (Person C)
- `stubs.py` — no longer imported anywhere; kept only as a manual testing fixture

See `INTERFACE_CONTRACT.md` for the exact data shapes each module produces/consumes.

## Known limitations

- **web3.py version quirk**: the installed `hexbytes` 2.0.0's `.hex()` drops the `0x`
  prefix (older versions kept it). `blockchain/verify.py`'s `register_match()` explicitly
  strips-then-readds it — that line is a compatibility fix for this specific installed
  version, not dead or redundant code.
- **Google Lens matches general visual similarity, not faces specifically — confirmed
  empirically, not just theorized.** A real end-to-end run against a real registered
  face returned candidates that were visually-similar leather jacket product listings
  (the most visually distinctive object in the query photo), not the actual person.
  `verify_match.py`'s re-embedding step correctly rejected all of them (similarity
  scores of -0.05 to 0.04, nowhere near the 0.6 threshold) and `find_match()` correctly
  raised `NoMatchFoundError` rather than reporting a false positive — but this means a
  brand-new/private photo has little chance of surfacing a real post through this API.
  Google Lens (and reverse image search generally) works best when the *exact query
  image itself* is already public and indexed somewhere — for the demo, use a photo
  that's already posted on the subject's own real social account, not a fresh one.
- **`MATCH_CONFIDENCE_THRESHOLD` (0.6, in `face_pipeline/search.py`) is not yet validated**
  against a labeled set of known-match/known-non-match photo pairs — it's a reasonable
  starting point for ArcFace cosine similarity, not a tuned number.
- **Amoy testnet deployment is pending** — see "Which blockchain" above; only the local
  Hardhat network has been exercised for real so far.

## Team

<!-- FILL IN: names, roles -->
