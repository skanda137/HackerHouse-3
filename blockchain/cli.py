"""
blockchain/cli.py
Standalone CLI for the blockchain layer, independent of the face pipeline —
hash arbitrary input (text or a file) and write/read it via
register_match()/verify_match(). Useful for testing the chain in isolation
before wiring it into the full pipeline.

Usage:
    python blockchain/cli.py write --text "some content" --post-url "https://example.com/post"
    python blockchain/cli.py write --file path/to/file.txt --post-url "https://example.com/post"
    python blockchain/cli.py read --text "some content"
    python blockchain/cli.py read --file path/to/file.txt
    python blockchain/cli.py read --hash <64-hex-char sha256 hash>
"""
import argparse
import hashlib
import json

from verify import register_match, verify_match


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hash_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _resolve_hash(args) -> str:
    if getattr(args, "hash", None):
        return args.hash[2:] if args.hash.startswith(("0x", "0X")) else args.hash
    if args.text is not None:
        return _hash_text(args.text)
    return _hash_file(args.file)


def main():
    parser = argparse.ArgumentParser(description="Hash arbitrary input and write/read it on-chain.")
    sub = parser.add_subparsers(dest="command", required=True)

    write_p = sub.add_parser("write", help="Hash input and register it on-chain.")
    write_group = write_p.add_mutually_exclusive_group(required=True)
    write_group.add_argument("--text", help="Arbitrary text to hash.")
    write_group.add_argument("--file", help="Path to a file to hash.")
    write_p.add_argument("--post-url", required=True, help="URL to associate with this hash.")

    read_p = sub.add_parser("read", help="Read back an on-chain record.")
    read_group = read_p.add_mutually_exclusive_group(required=True)
    read_group.add_argument("--text", help="Arbitrary text to hash and look up.")
    read_group.add_argument("--file", help="Path to a file to hash and look up.")
    read_group.add_argument("--hash", help="A raw sha256 hex hash to look up directly.")

    args = parser.parse_args()
    data_hash = _resolve_hash(args)
    print(f"Hash: 0x{data_hash}")

    if args.command == "write":
        result = register_match(data_hash, args.post_url)
    else:
        result = verify_match(data_hash)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
