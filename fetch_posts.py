"""Search Bluesky for new posts with the hashtag and merge them into data/posts.json.

Needs env vars BSKY_HANDLE and BSKY_APP_PASSWORD (an app password, not your
main password: Settings > Privacy and security > App passwords).
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from atproto import Client

import config

DATA_FILE = Path(__file__).parent / "data" / "posts.json"


def normalize_time(ts: str) -> str:
    """Fixed-width UTC timestamps so they sort correctly as strings."""
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def load_posts() -> list[dict]:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return []


def save_posts(posts: list[dict]) -> None:
    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(posts, indent=0) + "\n")


def search_new_posts(client: Client, known: set[str]) -> list[dict]:
    found, cursor = [], None
    for _ in range(config.MAX_PAGES_PER_RUN):
        params = {
            "q": f"#{config.HASHTAG}",
            "tag": [config.HASHTAG],
            "sort": "latest",
            "limit": 100,
        }
        if cursor:
            params["cursor"] = cursor
        resp = client.app.bsky.feed.search_posts(params=params)
        hit_known = False
        for p in resp.posts:
            if p.uri in known:
                hit_known = True
                continue
            found.append({
                "uri": p.uri,
                "t": normalize_time(p.indexed_at),
                "author": p.author.did,
                "handle": p.author.handle,
            })
        cursor = resp.cursor
        if hit_known or not cursor or not resp.posts:
            break
    return found


def main() -> None:
    client = Client()
    client.login(os.environ["BSKY_HANDLE"], os.environ["BSKY_APP_PASSWORD"])

    posts = load_posts()
    new = search_new_posts(client, {p["uri"] for p in posts})

    merged = {p["uri"]: p for p in posts + new}
    ordered = sorted(merged.values(), key=lambda p: (p["t"], p["uri"]), reverse=True)
    ordered = ordered[: config.MAX_STORED_POSTS]

    changed = bool(new)
    if changed:
        save_posts(ordered)
    print(f"{len(new)} new posts, {len(ordered)} stored")

    # Tell the GitHub workflow whether anything changed.
    if out := os.environ.get("GITHUB_OUTPUT"):
        with open(out, "a") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")


if __name__ == "__main__":
    sys.exit(main())
