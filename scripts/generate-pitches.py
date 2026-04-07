#!/usr/bin/env python3
"""Generate one-line talk pitches for AIE Europe '26 sessions using Claude API.

Usage:
    # Set ANTHROPIC_KEY in .env, then:
    python3 scripts/generate-pitches.py

Generates a JSON file at data/pitches.json mapping session index to pitch text.
Falls back to first sentence of description if API call fails.
"""

import json
import os
import sys
import time
from pathlib import Path

SESSIONS_FILE = Path("data/sessions.json")
OUTPUT_FILE = Path("data/pitches.json")

def load_dotenv():
    for p in [Path(".env"), Path(__file__).resolve().parent.parent / ".env", Path("/Users/usuario/Code/aie-twin/.env")]:
        if p.exists():
            for line in p.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
            return

load_dotenv()

def first_sentence(desc):
    """Extract first sentence as fallback pitch."""
    if not desc:
        return ""
    # Split on period followed by space or end
    for i, c in enumerate(desc):
        if c == '.' and (i + 1 >= len(desc) or desc[i+1] == ' '):
            s = desc[:i+1].strip()
            if len(s) > 15:  # Skip very short fragments
                return s[:120]
    return desc[:120].strip()

def generate_pitch_claude(title, description, api_key):
    """Call Claude API to generate a one-line pitch."""
    import httpx

    prompt = f"""You are a conference attendee advisor. Given this talk title and description, write ONE compelling sentence (max 15 words) explaining why an AI engineer should attend this talk. Be specific and concrete, not generic. No quotes around the sentence.

Title: {title}
Description: {description[:500]}"""

    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 60,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["content"][0]["text"].strip().strip('"').strip("'")

def main():
    with open(SESSIONS_FILE) as f:
        sessions = json.load(f)["sessions"]

    api_key = os.environ.get("ANTHROPIC_KEY", "")
    use_api = api_key and not api_key.startswith("sk-ant-...")

    if use_api:
        print(f"Using Claude API (claude-haiku-4-5) for {len(sessions)} sessions...")
        import httpx  # Verify available
    else:
        print("No valid ANTHROPIC_KEY found. Using first-sentence fallback.")

    # Load existing pitches for resume
    pitches = {}
    if OUTPUT_FILE.exists():
        pitches = json.load(open(OUTPUT_FILE))
        print(f"Loaded {len(pitches)} existing pitches (resume mode)")

    generated = 0
    failed = 0

    for i, s in enumerate(sessions):
        idx = str(i)
        if idx in pitches:
            continue

        title = s.get("title", "") or "TBA"
        desc = s.get("description", "") or ""

        if use_api and desc:
            try:
                pitch = generate_pitch_claude(title, desc, api_key)
                pitches[idx] = pitch
                generated += 1
                print(f"  [{i}] {pitch}")
                # Rate limit: ~50 req/min for haiku
                if generated % 10 == 0:
                    time.sleep(1)
            except Exception as e:
                pitches[idx] = first_sentence(desc)
                failed += 1
                print(f"  [{i}] FALLBACK: {e}")
        else:
            pitches[idx] = first_sentence(desc)
            generated += 1

        # Save incrementally every 20
        if generated % 20 == 0:
            with open(OUTPUT_FILE, "w") as f:
                json.dump(pitches, f, indent=2)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(pitches, f, indent=2)

    print(f"\nDone! Generated: {generated}, Failed: {failed}, Total: {len(pitches)}")
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
