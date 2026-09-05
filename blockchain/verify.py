"""
blockchain/verify.py
Python (web3.py) client for the MatchRegistry contract. Implements
register_match()/verify_match() exactly per INTERFACE_CONTRACT.md.

Reads which network to talk to from BLOCKCHAIN_NETWORK in the repo root
.env, and reads that network's deployed address + ABI from
blockchain/deployments/<network>.json (written by scripts/deploy.js) —
so this file never needs editing when the contract is redeployed.
"""
import os
import json
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

_REPO_ROOT = Path(__file__).resolve().parent.parent
_BLOCKCHAIN_DIR = Path(__file__).resolve().parent
load_dotenv(_REPO_ROOT / ".env")

_CHAIN_DISPLAY_NAMES = {
    "amoy": "polygon_amoy",
    "localhost": "hardhat_local",
}

_deployment = None
_w3 = None
_contract = None


def _resolve_hardhat_network() -> str:
    """Maps the repo's BLOCKCHAIN_NETWORK env value to a Hardhat network name."""
    raw = os.environ.get("BLOCKCHAIN_NETWORK", "hardhat_local").strip().lower()
    if raw in ("polygon_amoy", "amoy"):
        return "amoy"
    return "localhost"


def _load_deployment() -> dict:
    network = _resolve_hardhat_network()
    deployment_path = _BLOCKCHAIN_DIR / "deployments" / f"{network}.json"
    if not deployment_path.exists():
        raise RuntimeError(
            f"No deployment found for network '{network}' at {deployment_path}. "
            f"From blockchain/, run either:\n"
            f"  npm run deploy:local   (starts a local Hardhat node first with `npm run node`)\n"
            f"  npm run deploy:amoy    (needs RPC_URL + PRIVATE_KEY in the repo root .env)"
        )
    with open(deployment_path) as f:
        return json.load(f)


def _get_contract():
    """Lazy-loads the deployment info, Web3 connection, and contract instance."""
    global _deployment, _w3, _contract
    if _contract is not None:
        return _contract

    _deployment = _load_deployment()
    network = _deployment["network"]
    rpc_url = "http://127.0.0.1:8545" if network == "localhost" else os.environ.get(
        "RPC_URL", "https://rpc-amoy.polygon.technology"
    )

    _w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not _w3.is_connected():
        raise RuntimeError(
            f"Could not connect to {network} at {rpc_url}. "
            + ("Is `npm run node` running?" if network == "localhost" else "Check RPC_URL in .env.")
        )

    _contract = _w3.eth.contract(address=_deployment["address"], abi=_deployment["abi"])
    return _contract


def _to_bytes32(data_hash: str) -> bytes:
    clean = data_hash[2:] if data_hash.startswith(("0x", "0X")) else data_hash
    try:
        raw = bytes.fromhex(clean)
    except ValueError as e:
        raise ValueError(f"data_hash must be a hex string: {data_hash!r}") from e
    if len(raw) != 32:
        raise ValueError(f"data_hash must be 32 bytes (64 hex chars); got {len(raw)} bytes.")
    return raw


def register_match(data_hash: str, post_url: str) -> dict:
    """Writes a record on-chain. Returns tx receipt info."""
    contract = _get_contract()
    private_key = os.environ["PRIVATE_KEY"]
    account = _w3.eth.account.from_key(private_key)

    tx = contract.functions.registerMatch(_to_bytes32(data_hash), post_url).build_transaction({
        "from": account.address,
        "nonce": _w3.eth.get_transaction_count(account.address),
        "chainId": _w3.eth.chain_id,
    })
    signed = account.sign_transaction(tx)
    tx_hash = _w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = _w3.eth.wait_for_transaction_receipt(tx_hash)

    return {
        # hexbytes 2.0.0's .hex() drops the "0x" prefix (unlike older versions) —
        # strip-then-readd makes this correct regardless of which behavior is installed.
        "tx_hash": "0x" + receipt.transactionHash.hex().removeprefix("0x"),
        "block_number": receipt.blockNumber,
        "chain": _CHAIN_DISPLAY_NAMES[_deployment["network"]],
        "contract_address": _deployment["address"],
    }


def verify_match(data_hash: str) -> dict:
    """Reads back the on-chain record for a given hash."""
    contract = _get_contract()
    verified, post_url, block_number, timestamp = contract.functions.verifyMatch(
        _to_bytes32(data_hash)
    ).call()

    if not verified:
        return {"verified": False, "post_url": None, "block_number": None, "registered_at": None}

    return {
        "verified": True,
        "post_url": post_url,
        "block_number": block_number,
        "registered_at": datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(),
    }
