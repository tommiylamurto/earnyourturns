"""Search Bluesky for new posts with the hashtag and merge them into data/posts.json.

Needs env vars BSKY_HANDLE and BSKY_APP_PASSWORD (an app password, not your
main password: Settings > Privacy and security > App passwords).
"""
import json
import os
import re
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


def _get(obj, name):
    """Read a field from either an SDK model or a plain dict."""
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def post_hashtags(record) -> list[str]:
    """Every hashtag on a post: #tags in the text plus any hidden extra tags."""
    tags = [config.clean_tag(t) for t in (_get(record, "tags") or [])]
    for facet in _get(record, "facets") or []:
        for feature in _get(facet, "features") or []:
            tag = _get(feature, "tag")
            if tag:
                tags.append(config.clean_tag(tag))
    return list(dict.fromkeys(tags))


LINK_IN_TEXT = re.compile(r"https?://|www\.\S+\.\w", re.IGNORECASE)


def _type(obj) -> str:
    return _get(obj, "py_type") or _get(obj, "$type") or ""


def post_has_link(record) -> bool:
    """True if the post has a link preview card or a web link in its text.
    Images, videos and quote posts don't count as links."""
    embed = _get(record, "embed")
    if embed is not None:
        if _type(embed).startswith("app.bsky.embed.external"):
            return True
        media = _get(embed, "media")  # quote post + attached media
        if media is not None and _type(media).startswith("app.bsky.embed.external"):
            return True
    for facet in _get(record, "facets") or []:
        for feature in _get(facet, "features") or []:
            if _get(feature, "uri"):
                return True
    return bool(LINK_IN_TEXT.search(_get(record, "text") or ""))


def visible_hashtags(record) -> list[str]:
    """Only the #tags written in the post text (not hidden extra tags)."""
    tags = []
    for facet in _get(record, "facets") or []:
        for feature in _get(facet, "features") or []:
            tag = _get(feature, "tag")
            if tag:
                tags.append(config.clean_tag(tag))
    return list(dict.fromkeys(tags))


def describe(record) -> dict:
    return {
        "all_tags": post_hashtags(record),
        "visible_tags": visible_hashtags(record),
        "has_link": post_has_link(record),
    }


def fill_missing_details(client: Client, posts: list[dict]) -> int:
    """Look up tags/link info for posts collected before these were recorded."""
    missing = [p for p in posts if "has_link" not in p or "visible_tags" not in p]
    for i in range(0, len(missing), 25):
        batch = missing[i:i + 25]
        resp = client.app.bsky.feed.get_posts(params={"uris": [p["uri"] for p in batch]})
        found = {pv.uri: pv for pv in resp.posts}
        for p in batch:
            if p["uri"] in found:
                p.update(describe(found[p["uri"]].record))
            else:
                # deleted post; Bluesky stops showing it anyway
                p.setdefault("has_link", False)
                p.setdefault("visible_tags", [])
    return len(missing)


def search_tag(client: Client, tag: str, known: set[str]) -> list[dict]:
    """Newest-first search for one tag; stops at the first post already
    collected under this same tag."""
    found, cursor = [], None
    for _ in range(config.MAX_PAGES_PER_RUN):
        params = {"q": f"#{tag}", "tag": [tag], "sort": "latest", "limit": 100}
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
                "tags": [tag],
                **describe(p.record),
            })
        cursor = resp.cursor
        if hit_known or not cursor or not resp.posts:
            break
    return found


def merge(posts: list[dict], new: list[dict]) -> dict[str, dict]:
    """Combine by post URI, unioning the tags each post was found under."""
    merged: dict[str, dict] = {}
    for p in posts + new:
        if p["uri"] in merged:
            tags = merged[p["uri"]].setdefault("tags", [])
            tags.extend(t for t in p.get("tags", []) if t not in tags)
        else:
            merged[p["uri"]] = {**p, "tags": list(p.get("tags", []))}
    return merged


def main() -> None:
    client = Client()
    client.login(os.environ["BSKY_HANDLE"], os.environ["BSKY_APP_PASSWORD"])

    posts = load_posts()
    new: list[dict] = []
    for tag in config.all_hashtags():
        known = {p["uri"] for p in posts if tag in p.get("tags", [])}
        hits = search_tag(client, tag, known)
        print(f"#{tag}: {len(hits)} new")
        new.extend(hits)

    merged = merge(posts, new)
    ordered = sorted(merged.values(), key=lambda p: (p["t"], p["uri"]), reverse=True)
    ordered = ordered[: config.MAX_STORED_POSTS]

    filled = fill_missing_details(client, ordered)
    if filled:
        print(f"looked up link/tag details for {filled} older posts")

    changed = bool(new) or filled > 0
    if changed:
        save_posts(ordered)
    print(f"{len(merged) - len(posts)} new posts, {len(ordered)} stored")

    # Tell the GitHub workflow whether anything changed.
    if out := os.environ.get("GITHUB_OUTPUT"):
        with open(out, "a") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")


if __name__ == "__main__":
    sys.exit(main())
