"""Remove feed entries from your Bluesky account. Run on your own computer.

    python delete_feed.py earnyourturns senditsun

Takes the feed ids (the last part of a feed's bsky.app link). Their subscribers
and likes are lost, so only use it for feeds you no longer want. Refuses ids
that are still listed in config.FEEDS.
"""
import getpass
import os
import sys

from atproto import Client

import config


def main(rkeys: list[str]) -> None:
    if not rkeys:
        raise SystemExit(__doc__)
    active = {f["rkey"] for f in config.FEEDS}
    for rkey in rkeys:
        if rkey in active:
            raise SystemExit(f"{rkey!r} is still in config.FEEDS; remove it there first.")

    handle = os.environ.get("BSKY_HANDLE") or input("Bluesky handle: ").strip()
    password = os.environ.get("BSKY_APP_PASSWORD") or getpass.getpass("App password: ")
    client = Client()
    client.login(handle, password)

    for rkey in rkeys:
        print(f"Delete feed {rkey!r} from {handle}? [y/N] ", end="")
        if input().strip().lower() != "y":
            print("  skipped")
            continue
        client.com.atproto.repo.delete_record({
            "repo": client.me.did,
            "collection": "app.bsky.feed.generator",
            "rkey": rkey,
        })
        print("  deleted")


if __name__ == "__main__":
    main(sys.argv[1:])
