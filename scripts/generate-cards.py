#!/usr/bin/env python3
"""Generate unique AI card backgrounds for AIE Europe '26 sessions using FLUX API.

Usage:
    export BFL_API_KEY=your_key_here
    python3 scripts/generate-cards.py

Generates 480x640 abstract art images, one per session, saved to data/card-images/.
Supports resume — skips already-generated images.
"""

import asyncio
import base64
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path

import httpx

# ── Config ──
API_URL = "https://api.bfl.ai/v1/flux-2-pro"
IMG_DIR = Path("data/card-images")
SESSIONS_FILE = Path("data/sessions.json")
WIDTH, HEIGHT = 480, 640
MAX_CONCURRENT = 20
POLL_INTERVAL = 1.5  # seconds between polls
MAX_POLL_TIME = 120  # seconds before giving up on one image

# ── Track color descriptions for prompts ──
TRACK_COLORS = {
    "Context Engineering": "electric blue and violet",
    "MCP": "emerald green and cyan",
    "Coding Agents": "orange and warm red",
    "Harness Engineering": "magenta pink and rose",
    "Evals & Observability": "amber gold and yellow",
    "Voice & Vision": "cyan and sky blue",
    "Claws & Personal Agents": "deep violet and indigo",
    "AI Architects": "silver white and cool gray",
    "GPUs & LLM Infra": "crimson red and deep orange",
    "GPUs & LLM Infrastructure": "crimson red and deep orange",
    "Google DeepMind/Gemini": "royal blue and green",
    "Generative Media": "lime green and teal",
    "Expo Sessions (Abbey)": "dark gray and silver",
    "Expo Sessions (Shelley)": "dark gray and silver",
    "Expo Sessions (Wesley)": "dark gray and silver",
    "Expo Sessions (Wordsworth)": "dark gray and silver",
    "Leadership Lunch": "warm gold and bronze",
}

TYPE_COLORS = {
    "keynote": "gold and warm white",
    "track_keynote": "gold and warm white",
    "workshop": "navy blue and deep blue",
    "talk": "cool gray and steel blue",
    "lightning": "light violet and purple",
    "expo_session": "dark gray and silver",
}


def make_session_id(s, idx):
    """Generate stable session ID matching the JS code, with index fallback for uniqueness."""
    title = s.get("title", "") or ""
    raw = title + s["day"] + s["time"]
    b = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    b = b.replace("+", "_").replace("/", "_").replace("=", "_")
    sid = b[:16]
    return f"{idx:03d}_{sid}"


def build_prompt(session):
    """Build a FLUX prompt for a session's card background."""
    track = session.get("track", "") or ""
    stype = session.get("type", "") or "talk"
    title = session.get("title", "") or "AI Engineering"

    color_desc = TRACK_COLORS.get(track, TYPE_COLORS.get(stype, "cool blue and dark gray"))

    # Shorten title for prompt (keep first 60 chars)
    title_short = title[:60]

    return (
        f"Abstract digital art background, flowing diagonal light streaks and soft gradients, "
        f"{color_desc} tones against deep black, ethereal luminous glow, "
        f"inspired by the concept: {title_short}. "
        f"Minimal, atmospheric, moody, cinematic lighting. "
        f"No text, no letters, no words, no faces, no people, no objects. "
        f"Pure abstract energy and color."
    )


async def generate_one(client, session, idx, sem, api_key, stats):
    """Generate one card image via FLUX API."""
    sid = make_session_id(session, idx)
    out_path = IMG_DIR / f"{sid}.webp"

    # Resume support: skip if already exists
    if out_path.exists() and out_path.stat().st_size > 1000:
        stats["skipped"] += 1
        return

    prompt = build_prompt(session)

    async with sem:
        try:
            # Step 1: Submit generation request
            resp = await client.post(
                API_URL,
                json={"prompt": prompt, "width": WIDTH, "height": HEIGHT},
                headers={"x-key": api_key, "Content-Type": "application/json"},
                timeout=30,
            )
            if resp.status_code == 429:
                print(f"  [{idx}] Rate limited, waiting 10s...")
                await asyncio.sleep(10)
                resp = await client.post(
                    API_URL,
                    json={"prompt": prompt, "width": WIDTH, "height": HEIGHT},
                    headers={"x-key": api_key, "Content-Type": "application/json"},
                    timeout=30,
                )
            resp.raise_for_status()
            data = resp.json()
            polling_url = data.get("polling_url") or f"https://api.bfl.ai/v1/get_result?id={data['id']}"

            # Step 2: Poll until ready
            start = time.time()
            while time.time() - start < MAX_POLL_TIME:
                await asyncio.sleep(POLL_INTERVAL)
                poll_resp = await client.get(polling_url, headers={"x-key": api_key}, timeout=15)
                poll_data = poll_resp.json()
                status = poll_data.get("status", "")

                if status == "Ready":
                    img_url = poll_data["result"]["sample"]
                    # Step 3: Download image
                    img_resp = await client.get(img_url, timeout=30)
                    img_resp.raise_for_status()

                    # Save as webp (FLUX returns jpg/png, we save as-is with .webp extension)
                    out_path.write_bytes(img_resp.content)
                    stats["done"] += 1
                    title_short = (session.get("title", "") or "?")[:40]
                    print(f"  [{idx}] OK: {title_short}... ({stats['done']}/{stats['total']})")
                    return

                if status in ("Error", "Failed", "Content Moderated"):
                    stats["failed"] += 1
                    print(f"  [{idx}] FAIL ({status}): {(session.get('title','') or '?')[:40]}")
                    return

            stats["failed"] += 1
            print(f"  [{idx}] TIMEOUT: {(session.get('title','') or '?')[:40]}")

        except Exception as e:
            stats["failed"] += 1
            print(f"  [{idx}] ERROR: {e}")


async def main():
    api_key = os.environ.get("BFL_API_KEY")
    if not api_key:
        print("ERROR: Set BFL_API_KEY environment variable")
        sys.exit(1)

    # Load sessions
    with open(SESSIONS_FILE) as f:
        sessions = json.load(f)["sessions"]

    IMG_DIR.mkdir(parents=True, exist_ok=True)

    stats = {"done": 0, "skipped": 0, "failed": 0, "total": len(sessions)}

    print(f"Generating {len(sessions)} card images with FLUX API...")
    print(f"Output: {IMG_DIR}/")
    print(f"Concurrency: {MAX_CONCURRENT}")
    print()

    sem = asyncio.Semaphore(MAX_CONCURRENT)
    async with httpx.AsyncClient() as client:
        tasks = [generate_one(client, s, i, sem, api_key, stats) for i, s in enumerate(sessions)]
        await asyncio.gather(*tasks)

    print()
    print(f"Done! Generated: {stats['done']}, Skipped: {stats['skipped']}, Failed: {stats['failed']}")

    # Write an index mapping session IDs to filenames for the frontend
    index = {}
    for i, s in enumerate(sessions):
        sid = make_session_id(s, i)
        img_path = IMG_DIR / f"{sid}.webp"
        if img_path.exists():
            index[i] = f"{sid}.webp"
    with open(IMG_DIR / "index.json", "w") as f:
        json.dump(index, f)
    print(f"Index written: {len(index)} entries in data/card-images/index.json")


if __name__ == "__main__":
    asyncio.run(main())
