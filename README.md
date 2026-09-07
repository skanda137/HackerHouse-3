# HH Goa 2026 — Task 3: Face Identification & Blockchain Verification

## What this does

Takes a face image, finds a real matching social media post via reverse image search,
and writes a tamper-evident record of that match to a blockchain — then re-verifies
the recorded data against the on-chain copy.

Pipeline: **face scan → consent check → web/social search → face re-verification →
blockchain registration → re-verification**

Privacy note: raw face images and biometric embeddings are never written on-chain.
Only a SHA-256 hash of the input image and the matched post URL are committed.

**Status: fully working end-to-end on Polygon Amoy testnet.** A real run against a
real, consented face found a genuine match, registered it on-chain, and re-verified
it — see "Which blockchain" below for the actual transaction.

## How it works

1. **Face detection + embedding** (`face_pipeline/__init__.py`) — `insightface`
   (`buffalo_l` / ArcFace) detects the largest/most-confident face in the image and
   extracts a 512-dim embedding. Also crops the image tightly to the face bounding
   box (`crop_to_face()`) before it's ever sent out for search.
2. **Consent gate** (`consent_gate.py`) — the embedding is compared (cosine
   similarity, threshold 0.45) against a pre-registered allowlist in `registry.json`.
   If it doesn't match a consenting member, `find_match()` raises
   `ConsentRequiredError` and **stops before any search call is made** — enforced in
   code, not just documented.
3. **Reverse image search** (`reverse_search.py`) — the face-cropped image is
   uploaded to SerpApi's Image API and searched via Google Lens; the top visual
   matches (title, link, image, source) come back as candidates.
4. **Face re-verification** (`verify_match.py`) — each candidate's image is
   downloaded and re-run through the same face embedding model. Only candidates
   where a face was actually detected and its cosine similarity to the query clears
   0.40 are kept, sorted best-first. This is what makes "confidence" a real face
   comparison instead of a repackaged visual-similarity score from the search API.
5. **Orchestration** (`face_pipeline/search.py`, `find_match()`) — ties the above
   together, hashes the input image (SHA-256), and requires the best surviving
   candidate to clear `MATCH_CONFIDENCE_THRESHOLD = 0.6` before calling it a genuine
   match. If nothing clears that bar, it raises `NoMatchFoundError` rather than
   guessing.
6. **Blockchain registration + verification** (`blockchain/verify.py`,
   `blockchain/contracts/MatchRegistry.sol`) — `register_match()` writes
   `(dataHash → postUrl, blockNumber, timestamp, registeredBy)` on-chain via web3.py;
   `verify_match()` reads it back. The contract reverts with `AlreadyRegistered` if
   the same hash is registered twice, so a record can't be silently overwritten.
7. **CLI orchestrator** (`main.py`) — runs steps 1–6 as a 4-stage pipeline, prints
   progress, and writes the full result to `artifacts/last_run_result.json`.
8. **Tamper-evidence demo** (`tamper_demo.py`) — standalone script: register content
   → verify it matches → simulate tampering with the content → re-verify → show that
   the tampered hash no longer matches anything on-chain.

## Demo subjects & consent

Consent is structurally enforced: `find_match()` (`face_pipeline/search.py`) calls
`consent_gate.check_consent()` on the extracted face embedding *before* any search
runs, and raises `ConsentRequiredError` if the face isn't on the allowlist. This has
been verified by reading the actual function body, not assumed from a docstring.

Six team members are currently registered via `register_cli.py` (`registry.json`,
gitignored — not committed). The full pipeline has been run end-to-end against a
real, consented face and found a **real, genuine match**: a registered member's
photo was matched to their own public LinkedIn profile at confidence 0.96, the match
was written to Polygon Amoy, and the on-chain copy was successfully re-verified (see
"Which blockchain" for the transaction details). Demo subjects are team members' own
faces, matched against their own real, publicly-known social accounts (self-consent)
— for reliable results, use a photo that's already posted on that account rather than
a brand-new one (see Known Limitations for why that matters).

To register a new demo subject:

```bash
python register_cli.py --name YourName --photo your_consent_photo.jpg
```

## How to run

```bash
git clone <repo_url>
cd HackerHouse-3
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Blockchain setup (see blockchain/ for details)
cd blockchain && npm install && cd ..

cp .env.example .env
# fill in .env with your API keys / RPC URL / a funded wallet private key —
# see .env.example for what's required, and never commit a filled-in .env

python register_cli.py --name YourName --photo your_consent_photo.jpg
python main.py path/to/face_image.jpg
```

Each run writes the full match + registration + verification result to
`artifacts/last_run_result.json`.

To run the tamper-evidence demo separately:

```bash
python tamper_demo.py
```

To exercise the blockchain layer on its own (no face pipeline involved):

```bash
python blockchain/cli.py write --text "some content" --post-url "https://example.com/post"
python blockchain/cli.py read --text "some content"
```

## Which blockchain

**Polygon Amoy testnet** (chainId 80002), via a Solidity contract
(`blockchain/contracts/MatchRegistry.sol`) deployed and managed with Hardhat.
`registerMatch(bytes32 dataHash, string postUrl)` writes a record (reverts with the
custom error `AlreadyRegistered` if that exact hash was already registered — records
can't be silently overwritten); `verifyMatch(bytes32 dataHash)` reads one back.
`blockchain/verify.py` picks which deployment to talk to from `BLOCKCHAIN_NETWORK` in
`.env` and reads the deployed address + ABI from `blockchain/deployments/<network>.json`
— no code changes needed when switching networks or redeploying.

**Amoy testnet — deployed and confirmed working end-to-end.** Contract deployed at
`0xaF6F3acE84b9B7a934BacF80bf4dC2291f930203` (`blockchain/deployments/amoy.json`).
A real run of `python main.py` on 2026-09-06 detected a face, passed the consent
check, found a real matching LinkedIn post via reverse image search, registered
`(imageHash → postUrl)` on-chain (tx `0xe0155e0ada653417b5f55202e28c21ee838573d52b26701ca7f3f166df356871`,
block `46884868`), and successfully re-verified the record read back from-chain
matches what was written — full output captured in `artifacts/last_run_result.json`.
Set `BLOCKCHAIN_NETWORK=polygon_amoy` in `.env` to use it (needs `RPC_URL` and a
funded Amoy wallet `PRIVATE_KEY`).

**Local Hardhat network — also confirmed working**, and useful for fast iteration
without testnet gas: `npm run node` + `npm run deploy:local` inside `blockchain/`
starts a local chain and deploys to it (`blockchain/deployments/localhost.json`,
gitignored). `tamper_demo.py` has been run end-to-end against it: register → verify →
tamper → re-verify, no stubs involved. Set `BLOCKCHAIN_NETWORK=hardhat_local` in
`.env` to use it.

To redeploy the contract (e.g. to a fresh Amoy wallet), run `npm run deploy:amoy` or
`npm run deploy:local` from `blockchain/` — the script writes the new address + ABI
to `blockchain/deployments/<network>.json` automatically.

## Architecture

Flat layout at the repo root, except for `blockchain/`:

- `face_pipeline/` — `__init__.py` (face detection/encoding, `crop_to_face`) +
  `search.py` (`find_match()` orchestration, consent enforcement, match threshold)
- `reverse_search.py` — SerpApi Google Lens reverse image search
- `verify_match.py` — re-embeds search candidates and computes real face-similarity confidence
- `consent_gate.py`, `register_cli.py` — consent allowlist (`registry.json`,
  gitignored) and the CLI to register new consenting members
- `blockchain/` — Solidity contract (`contracts/MatchRegistry.sol`), Hardhat project
  (`hardhat.config.js`, `scripts/deploy.js`, `test/MatchRegistry.test.js`), deployed
  addresses + ABIs (`deployments/`), and `verify.py`/`cli.py` register/verify logic
- `main.py` — orchestrator CLI, runs the full pipeline and writes `artifacts/last_run_result.json`
- `tamper_demo.py` — standalone tamper-evidence demo
- `stubs.py` — no longer imported anywhere; kept only as a manual testing fixture

See `INTERFACE_CONTRACT.md` for the exact data shapes each module produces/consumes.

## Known limitations

- **web3.py version quirk**: the installed `hexbytes` 2.0.0's `.hex()` drops the `0x`
  prefix (older versions kept it). `blockchain/verify.py`'s `register_match()` explicitly
  strips-then-readds it — that line is a compatibility fix for this specific installed
  version, not dead or redundant code.
- **Google Lens matches general visual similarity, not faces specifically.** This is
  why the pipeline crops to the face bounding box before searching (`crop_to_face()`)
  and why `verify_match.py` re-embeds and re-scores every candidate by actual face
  similarity rather than trusting Lens's ranking — a real run without that
  cross-check previously returned visually-similar product listings instead of the
  actual person. Reverse image search still only works when the *exact query image
  (or something very similar to it)* is already public and indexed somewhere — a
  brand-new/private photo has little chance of surfacing a real post through this
  API. Use a photo that's already posted on the subject's own real social account.
- **`MATCH_CONFIDENCE_THRESHOLD` (0.6, in `face_pipeline/search.py`) and
  `verify_match`'s candidate filter (0.40)** are reasonable starting points for
  ArcFace cosine similarity but have not been formally validated against a labeled
  set of known-match/known-non-match photo pairs.
- **Amoy RPC**: the default `rpc-amoy.polygon.technology` endpoint does not
  currently resolve; `.env.example` points at a working public endpoint
  (`https://polygon-amoy-bor-rpc.publicnode.com`) instead. Use your own
  Alchemy/Infura endpoint if you need higher reliability/rate limits.
- **Consent registry and `.env` are gitignored on purpose** — `registry.json`
  (biometric embeddings) and `.env` (API keys, wallet private key) never get
  committed. Anyone cloning the repo must register their own consenting demo
  subjects and provide their own credentials before running the pipeline.

## Team

<!-- FILL IN: names, roles -->
