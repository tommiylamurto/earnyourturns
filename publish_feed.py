"""Run on your own computer to register the feeds in config.FEEDS on your
Bluesky account.

Safe to re-run: each feed's record is overwritten in place (e.g. after changing
a name or description), so subscribers and likes are kept. Run it again after
adding a new feed to the list.
"""
import getpass
import os
from datetime import datetime, timezone

from atproto import Client

import config


def main() -> None:
    handle = os.environ.get("BSKY_HANDLE") or input("Bluesky handle: ").strip()
    password = os.environ.get("BSKY_APP_PASSWORD") or getpass.getpass("App password: ")

    client = Client()
    client.login(handle, password)
    did = client.me.did
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    for feed in config.FEEDS:
        client.com.atproto.repo.put_record({
            "repo": did,
            "collection": "app.bsky.feed.generator",
            "rkey": feed["rkey"],
            "record": {
                "$type": "app.bsky.feed.generator",
                "did": config.SERVICE_DID,
                "displayName": feed["name"],
                "description": feed["description"],
                "createdAt": now,
            },
        })
        print(f"Published {feed['name']}: https://bsky.app/profile/{did}/feed/{feed['rkey']}")

    print(f"\nYour DID (put in config.PUBLISHER_DID): {did}")


if __name__ == "__main__":
    main()
