"""Run on your own computer to register the feeds in config.FEEDS on your
Bluesky account.

Safe to re-run: each feed's record is overwritten in place (e.g. after changing
a name or description), so subscribers and likes are kept. Run it again after
adding a new feed to the list.
"""
import getpass
import os
from datetime import datetime, timezone
from pathlib import Path

from atproto import Client

import config


def upload_avatar(client: Client, path_str: str) -> dict:
    """Upload a feed avatar image and return the reference to store in the record."""
    path = Path(__file__).parent / path_str
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
        raise SystemExit(f"{path_str}: avatar must be a .png or .jpg file")
    data = path.read_bytes()
    if len(data) > 1_000_000:
        raise SystemExit(f"{path_str}: avatar is {len(data) // 1000} KB, max 1000 KB")
    blob = client.upload_blob(data).blob
    return blob.model_dump(mode="json", by_alias=True, exclude_none=True)


def main() -> None:
    handle = os.environ.get("BSKY_HANDLE") or input("Bluesky handle: ").strip()
    password = os.environ.get("BSKY_APP_PASSWORD") or getpass.getpass("App password: ")

    client = Client()
    client.login(handle, password)
    did = client.me.did
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    for feed in config.FEEDS:
        record = {
            "$type": "app.bsky.feed.generator",
            "did": config.SERVICE_DID,
            "displayName": feed["name"],
            "description": feed["description"],
            "createdAt": now,
        }
        if feed.get("avatar"):
            record["avatar"] = upload_avatar(client, feed["avatar"])
        client.com.atproto.repo.put_record({
            "repo": did,
            "collection": "app.bsky.feed.generator",
            "rkey": feed["rkey"],
            "record": record,
        })
        print(f"Published {feed['name']}: https://bsky.app/profile/{did}/feed/{feed['rkey']}")

    print(f"\nYour DID (put in config.PUBLISHER_DID): {did}")


if __name__ == "__main__":
    main()
