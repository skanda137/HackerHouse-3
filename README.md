# HH Goa 2026 — Task 3: Face Identification & Blockchain Verification

## What this does

Takes a face image, finds a real matching social media post via reverse image search,
and writes a tamper-evident record of that match to a blockchain — then re-verifies
the recorded data against the on-chain copy.

Pipeline: **face scan → web/social search → blockchain registration → re-verification**

Privacy note: raw face images and biometric embeddings are never written on-chain.
Only a SHA-256 hash of the input and the matched post URL are committed.

## Demo subjects

<!-- FILL IN: state clearly that face scans in the demo are of team members' own
     faces, matched against their own real, publicly-known social accounts (self-consent).
     This is a deliberate design choice, not a limitation — say so explicitly. -->

## How to run

```bash
git clone <repo_url>
cd hh_goa_task3
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Blockchain setup (see blockchain/ for details)
npm install

cp .env.example .env
# fill in .env with your API keys / RPC URL — see .env.example for what's required

python integration/main.py path/to/face_image.jpg
```

To run the tamper-evidence demo separately:

```bash
python integration/tamper_demo.py
```

## Which blockchain

<!-- FILL IN by Person B: e.g. "Polygon Amoy testnet. Contract address: 0x...
     Fallback: local Hardhat network if testnet RPC is unavailable." -->

## Architecture

- `face_pipeline/` — face detection/encoding + reverse image search (Person A)
- `blockchain/` — smart contract + register/verify logic (Person B)
- `integration/` — orchestrator CLI + tamper-evidence demo (Person C)
- `artifacts/` — output of pipeline runs, demo recordings

See `INTERFACE_CONTRACT.md` for the exact data shapes each module produces/consumes.

## Known limitations

<!-- FILL IN before submission. Be honest — judges will find gaps anyway; naming them
     yourself reads better than getting caught. Likely candidates:
     - reverse image search API rate limits / coverage gaps
     - demo restricted to self-consented team member faces, not arbitrary strangers
     - testnet vs mainnet tradeoffs
     - face match confidence threshold and false-positive rate -->

## Team

<!-- FILL IN: names, roles -->
