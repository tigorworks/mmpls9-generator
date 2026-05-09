import os
import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

API_KEY      = os.environ.get("CHALLONGE_API_KEY", "")
TOURNAMENT   = "mmpls9"
OUTPUT_FILE  = "final_bracket.json"

def main():
    if not API_KEY:
        raise SystemExit("CHALLONGE_API_KEY environment variable not set")

    url = f"https://api.challonge.com/v1/tournaments/{TOURNAMENT}.json"
    resp = requests.get(
        url,
        params={"api_key": API_KEY, "include_participants": 1, "include_matches": 1},
        timeout=15,
    )
    resp.raise_for_status()

    data = resp.json()
    data["fetched_at"] = datetime.now(ZoneInfo("Asia/Jakarta")).isoformat()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    state = data.get("tournament", {}).get("state", "unknown")
    print(f"Saved {OUTPUT_FILE}  (tournament state: {state})")

if __name__ == "__main__":
    main()
