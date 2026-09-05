"""
register_cli.py
Run this once per team member, on a photo they've explicitly agreed to use
for the demo. This populates registry.json which main.py checks before
running any search.

Usage:
    python register_cli.py --name Alice --photo alice_consent.jpg
"""
import argparse
from consent_gate import register_member

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--photo", required=True)
    args = parser.parse_args()
    register_member(args.name, args.photo)
