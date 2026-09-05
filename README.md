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

**Still incomplete**: nobody has registered yet — `registry.json` does not exist in this
repo. Register a face with `python register_cli.py --name <you> --photo <your_own_consented_photo.jpg>`
to create it. Once that's done, demo subjects will be team members' own faces, matched
against their own real, publicly-known social accounts (self-consent) — that is the
intended design, but as of now it hasn't happened, so don't present it as already true.

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
- **Reverse-image-search coverage is uneven by platform.** LinkedIn in particular is a
  known weak case: profile photos are served from `media.licdn.com` behind mechanisms
  that resist generic scraping, and Google/Google Lens indexes very little of LinkedIn's
  photo content tied back to profile pages. Don't expect SerpApi's Google Lens to
  reliably surface LinkedIn matches even once fully wired up.
- **`MATCH_CONFIDENCE_THRESHOLD` (0.6, in `face_pipeline/search.py`) is not yet validated**
  against a labeled set of known-match/known-non-match photo pairs — it's a reasonable
  starting point for ArcFace cosine similarity, not a tuned number.
- **No demo subjects registered yet.** `registry.json` doesn't exist; nobody has run
  `register_cli.py`. `main.py` has not been run against a real face end-to-end for this
  reason, and also because `SEARCH_API_KEY` is not yet set in `.env`.
- **Amoy testnet deployment is pending** — see "Which blockchain" above; only the local
  Hardhat network has been exercised for real so far.
- **`main.py` only catches `NoMatchFoundError`**, not `ConsentRequiredError` — if
  `find_match()` is called on a face that isn't on the consent allowlist, `main.py` will
  currently crash with an unhandled traceback instead of a clean message.

## Team

<!-- FILL IN: names, roles -->
