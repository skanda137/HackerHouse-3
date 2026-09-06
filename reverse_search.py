"""
Reverse image search via SerpApi Google Lens.

Accepts a local image file and uploads it to SerpApi's Image API,
then uses the returned image_id with Google Lens.
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Loaded here (not just in blockchain/verify.py) because this module reads its
# env var at import time, below — if main.py imports this before anything else
# has called load_dotenv(), SEARCH_API_KEY would be cached as None permanently
# for the process, regardless of what's in .env.
load_dotenv(Path(__file__).resolve().parent / ".env")

SERPAPI_KEY = os.environ.get("SEARCH_API_KEY")  # name matches .env/.env.example, not "SERPAPI_KEY"

SERPAPI_SEARCH_URL = "https://serpapi.com/search"
SERPAPI_IMAGE_URL = "https://serpapi.com/image"


def reverse_image_search(image_path: str, max_results: int = 10):
    """
    Search Google Lens using a local image file.

    Returns:
        [
            {
                "title": ...,
                "link": ...,
                "image": ...,
                "thumbnail": ...,
                "source": ...
            }
        ]
    """

    if not SERPAPI_KEY:
        raise RuntimeError(
            "SERPAPI_KEY not set. Set it in your PowerShell environment."
        )

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Step 1: Upload local image to SerpApi
    with open(image_path, "rb") as f:
        response = requests.post(
            SERPAPI_IMAGE_URL,
            params={"api_key": SERPAPI_KEY},
            files={"image": f},
            timeout=30,
        )

    response.raise_for_status()
    upload_data = response.json()

    image_id = upload_data.get("image_id")

    if not image_id:
        raise RuntimeError(
            f"SerpApi image upload failed: {upload_data}"
        )

    # Step 2: Search Google Lens using the uploaded image
    params = {
        "engine": "google_lens",
        "image_id": image_id,
        "api_key": SERPAPI_KEY,
    }

    response = requests.get(
        SERPAPI_SEARCH_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    # Step 3: Extract visual matches
    results = []

    for match in data.get("visual_matches", [])[:max_results]:
        results.append({
            "title": match.get("title"),
            "link": match.get("link"),
            "image": match.get("image"),
            "thumbnail": match.get("thumbnail"),
            "source": match.get("source"),
        })

    return results