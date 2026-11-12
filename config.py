
# The hashtag to collect, without the leading '#'. Case-insensitive on Bluesky.
HASHTAGS = ["earnyourturnsday", "nolifts", "splitboarding","backcountryskiing", "skitouring","mtb", "mountainbiking"]

# The subdomain that will serve the feed.
SERVICE_HOSTNAME = "feed.evo-review.com"

# Short id for the feed: lowercase letters, digits and dashes, max 15 characters.
FEED_RKEY = "earnyourturnsday"

# What people see in the Bluesky app.
FEED_DISPLAY_NAME = "#earnyourTurnsday"
FEED_DESCRIPTION = "Post your backcountry skiing and enduro biking adventures every Thursday. You earned it! No lifts, shuttles or ebikes."

# Your Bluesky account's DID (starts with did:plc:). publish_feed.py prints it.
PUBLISHER_DID = "did:plc:REPLACE_ME"

# Accounts whose posts should never appear (DIDs or handles).
BLOCKED_AUTHORS: set[str] = set()

# How many posts to keep in history, and how many search pages to read per run.
MAX_STORED_POSTS = 20000
MAX_PAGES_PER_RUN = 10

# ---- derived values, no need to edit ----
SERVICE_DID = f"did:web:{SERVICE_HOSTNAME}"
FEED_URI = f"at://{PUBLISHER_DID}/app.bsky.feed.generator/{FEED_RKEY}"
