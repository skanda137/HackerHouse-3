import hashlib

from blockchain.verify import register_match, verify_match

def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def demo():
    print("=== Tamper-Evidence Demo ===\n")

    original_post_content = "Original scraped post content, exact bytes as found."
    original_url = "https://example.com/original-post"

    print("[Step 1] Hashing and registering the ORIGINAL content on-chain...")
    original_hash = hash_content(original_post_content)
    reg = register_match(original_hash, original_url)
    print(f"   Registered. tx_hash={reg['tx_hash']}  block={reg['block_number']}\n")

    print("[Step 2] Re-verifying against the original, unaltered content...")
    check = verify_match(original_hash)
    print(f"   Hash of current content: {original_hash}")
    print(f"   On-chain verification result: verified={check['verified']}")
    print("   PASS — content matches the on-chain record.\n" if check["verified"]
          else "   FAIL — unexpected mismatch on unaltered data.\n")

    print("[Step 3] Simulating tampering: altering the content after the fact...")
    tampered_content = original_post_content.replace("Original", "Altered")
    tampered_hash = hash_content(tampered_content)
    print(f"   Original hash:  {original_hash}")
    print(f"   Tampered hash:  {tampered_hash}")

    print("\n[Step 4] Re-verifying the TAMPERED content against the on-chain record...")
    tampered_check = verify_match(tampered_hash)
    if not tampered_check["verified"]:
        print("   DETECTED — tampered content's hash has no matching on-chain record.")
        print("   This is the tamper-evidence property: any post-hoc alteration changes")
        print("   the hash, which no longer matches what was registered on-chain.\n")
    else:
        print("   WARNING — tampered content unexpectedly verified. Check hash logic.\n")

    print("=== Demo complete ===")


if __name__ == "__main__":
    demo()
