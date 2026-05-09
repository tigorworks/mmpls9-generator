import os
import json
import time
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

API_KEY     = os.environ.get("CHALLONGE_API_KEY", "")
TOURNAMENT  = "mmpls9"
OUTPUT_FILE = "final_bracket.json"
MAX_RETRIES = 4
BACKOFF     = [2, 4, 8, 16]   # seconds between retries

HEADERS = {
    "User-Agent": "MMPL-S9-Sync/1.0 (github-actions)",
    "Accept":     "application/json",
}


def fetch_with_retry():
    url = f"https://api.challonge.com/v1/tournaments/{TOURNAMENT}.json"
    params = {
        "api_key":              API_KEY,
        "include_participants": 1,
        "include_matches":      1,
    }

    last_err = None
    for attempt in range(MAX_RETRIES):
        if attempt > 0:
            wait = BACKOFF[attempt - 1]
            print(f"  Retry {attempt}/{MAX_RETRIES - 1} — waiting {wait}s...")
            time.sleep(wait)
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=20)
            if resp.status_code == 520:
                # Cloudflare transient error — retry
                last_err = f"HTTP 520 (Cloudflare transient)"
                print(f"  Attempt {attempt + 1}: {last_err}")
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            last_err = str(e)
            print(f"  Attempt {attempt + 1} failed: {last_err}")

    raise RuntimeError(f"All {MAX_RETRIES} attempts failed. Last error: {last_err}")


def main():
    if not API_KEY:
        raise SystemExit("CHALLONGE_API_KEY environment variable not set")

    print(f"Fetching tournament '{TOURNAMENT}' from Challonge...")

    try:
        data = fetch_with_retry()
    except RuntimeError as e:
        # Preserve existing file if available; don't fail CI hard
        if os.path.exists(OUTPUT_FILE):
            print(f"WARNING: {e}")
            print(f"Keeping existing {OUTPUT_FILE} unchanged.")
        else:
            print(f"ERROR: {e}")
            print(f"No existing {OUTPUT_FILE} to fall back on.")
        return   # exit 0 — don't break CI on transient API errors

    data["fetched_at"] = datetime.now(ZoneInfo("Asia/Jakarta")).isoformat()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    state = data.get("tournament", {}).get("state", "unknown")
    print(f"Saved {OUTPUT_FILE}  (tournament state: {state})")


if __name__ == "__main__":
    main()
