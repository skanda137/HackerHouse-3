import sys
import json
from pathlib import Path

from face_pipeline.search import find_match, NoMatchFoundError
from consent_gate import ConsentRequiredError
from blockchain.verify import register_match, verify_match

def run_pipeline(image_path: str) -> dict:
    if not Path(image_path).exists():
        raise FileNotFoundError(f"No such image: {image_path}")

    print(f"[1/4] Detecting and encoding face from {image_path} ...")
    try:
        match = find_match(image_path)
    except ConsentRequiredError:
        print("This face is not on the consent allowlist — run register_cli.py first.")
        sys.exit(1)
    except NoMatchFoundError:
        print("No genuine match found for this face. Exiting.")
        sys.exit(1)

    print(f"[2/4] Match found: {match['matched_post_url']} "
          f"(platform={match['matched_platform']}, confidence={match['confidence']:.2f})")

    print("[3/4] Writing hash + post URL to blockchain ...")
    tx = register_match(match["image_hash"], match["matched_post_url"])
    print(f"       tx_hash={tx['tx_hash']}  block={tx['block_number']}  chain={tx['chain']}")

    print("[4/4] Re-verifying against on-chain record ...")
    verification = verify_match(match["image_hash"])
    print(f"       verified={verification['verified']}  "
          f"post_url={verification['post_url']}  block={verification['block_number']}")

    result = {
        "match": match,
        "registration": tx,
        "verification": verification,
    }
    return result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python integration/main.py path/to/face_image.jpg")
        sys.exit(1)

    output = run_pipeline(sys.argv[1])

    out_path = Path("artifacts") / "last_run_result.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\nFull result written to {out_path}")
