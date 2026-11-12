"""Run once on your own computer to register the feed on your Bluesky account.

Safe to re-run: it overwrites the same record (e.g. after changing the name).
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

    client.com.atproto.repo.put_record({
        "repo": did,
        "collection": "app.bsky.feed.generator",
        "rkey": config.FEED_RKEY,
        "record": {
            "$type": "app.bsky.feed.generator",
            "did": config.SERVICE_DID,
            "displayName": config.FEED_DISPLAY_NAME,
            "description": config.FEED_DESCRIPTION,
            "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        },
    })

    print("Feed published.")
    print(f"  Your DID (put in config.PUBLISHER_DID): {did}")
    print(f"  Feed URI: at://{did}/app.bsky.feed.generator/{config.FEED_RKEY}")
    print(f"  Open it: https://bsky.app/profile/{did}/feed/{config.FEED_RKEY}")


if __name__ == "__main__":
    main()
