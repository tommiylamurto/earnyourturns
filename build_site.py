"""Write the static files Cloudflare Pages serves into site/."""
import json
import shutil
from pathlib import Path

import config

ROOT = Path(__file__).parent
SITE = ROOT / "site"
DATA_FILE = ROOT / "data" / "posts.json"


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, separators=(",", ":")))


def main() -> None:
    shutil.rmtree(SITE, ignore_errors=True)
    SITE.mkdir()

    # Proves to Bluesky that this domain runs a feed generator.
    write_json(SITE / ".well-known" / "did.json", {
        "@context": ["https://www.w3.org/ns/did/v1"],
        "id": config.SERVICE_DID,
        "service": [{
            "id": "#bsky_fg",
            "type": "BskyFeedGenerator",
            "serviceEndpoint": f"https://{config.SERVICE_HOSTNAME}",
        }],
    })

    write_json(SITE / "describe.json", {
        "did": config.SERVICE_DID,
        "feeds": [{"uri": config.FEED_URI}],
    })

    posts = json.loads(DATA_FILE.read_text()) if DATA_FILE.exists() else []
    blocked = {b.lower() for b in config.BLOCKED_AUTHORS}
    served = [
        {"uri": p["uri"], "t": p["t"]}
        for p in posts
        if p["author"].lower() not in blocked and p.get("handle", "").lower() not in blocked
    ]
    write_json(SITE / "posts.json", served)

    tag_list = " ".join("#" + t for t in config.HASHTAGS)
    (SITE / "index.html").write_text(
        f"<!doctype html><title>{config.FEED_DISPLAY_NAME}</title>"
        f"<p>Bluesky feed generator for {tag_list}. {len(served)} posts indexed.</p>"
    )
    print(f"site built: {len(served)} posts")


if __name__ == "__main__":
    main()
