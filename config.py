"""Everything you need to edit lives in this file."""

# The subdomain that serves all your feeds (points at Cloudflare Pages).
SERVICE_HOSTNAME = "feed.evo-review.com"

# One entry per feed. Each feed shows posts with ANY of its hashtags.
#   rkey:        the feed's short id in its link. Lowercase letters, digits and
#                dashes, max 15 characters. Must differ from any feed you already
#                have (e.g. your BlueskyFeedCreator one) unless you mean to take it over.
#   hashtags:    without '#'. Case doesn't matter (#SendItSunday = #senditsunday),
#                but different spellings (#sendit_sunday) are different tags.
#   name / description: what people see in the Bluesky app.
FEEDS = [
    {
        "rkey": "earnyourturns",
        "hashtags": ["earnyourturnsday","nolifts", "splitboarding","backcountryskiing", "skitouring","mtb", "mountainbiking"],
        "name": "#EarnYourTurnsDay",
        "description": "Post your backcountry skiing and enduro biking adventures every Thursday. You earned it! No lifts, shuttles or ebikes.",
    },
    {
        "rkey": "senditsun",
        "hashtags": ["senditsunday"],
        "name": "#SendItSunday",
        "description": "Post your skiing and mountain biking photos and videos every Sunday. Doesn't really have to be sendy at all. We are not sponsored by Redbull. If it was sendy to you, then it's good enough for this feed.",
    },
]

# Your Bluesky account's DID (starts with did:plc:). publish_feed.py prints it.
PUBLISHER_DID = "did:plc:REPLACE_ME"

# Accounts whose posts should never appear in any feed (DIDs or handles).
# These are mostly ads or non-original content or flooding the channel.
BLOCKED_AUTHORS: set[str] = set('kagank.bsky.social','mathieuvanderpoel.bsky.social','indeleiderstrui.bsky.social','pink-wire.bsky.social',
                                'coloradotrail.pages.dev','acht.eurosky.social')

# How many posts to keep in history, and how many search pages to read per tag per run.
MAX_STORED_POSTS = 50000
MAX_PAGES_PER_RUN = 10

# ---- derived values, no need to edit ----
SERVICE_DID = f"did:web:{SERVICE_HOSTNAME}"


def clean_tag(tag: str) -> str:
    return tag.lower().lstrip("#")


def all_hashtags() -> list[str]:
    """Every hashtag across all feeds, each once."""
    return list(dict.fromkeys(clean_tag(t) for f in FEEDS for t in f["hashtags"]))


def feed_uri(rkey: str) -> str:
    return f"at://{PUBLISHER_DID}/app.bsky.feed.generator/{rkey}"


import re as _re

for _f in FEEDS:
    if not _re.fullmatch(r"[a-z0-9-]{1,15}", _f["rkey"]):
        raise ValueError(f"rkey {_f['rkey']!r}: use lowercase letters, digits, dashes; max 15 chars")
if len({_f["rkey"] for _f in FEEDS}) != len(FEEDS):
    raise ValueError("Two feeds in FEEDS share the same rkey")
