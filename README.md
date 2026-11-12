# Bluesky hashtag feed (GitHub Actions + Cloudflare Pages)

A custom Bluesky feed for one hashtag, with no server to run and no post cap.

**How it works**

1. Every 15 minutes a GitHub Action searches Bluesky for new posts with your
   hashtag and appends them to `data/posts.json` (your permanent history).
2. It builds a tiny static site and deploys it to Cloudflare Pages on your
   subdomain (e.g. `feed.example.com`).
3. When someone opens the feed, Bluesky calls
   `https://feed.example.com/xrpc/app.bsky.feed.getFeedSkeleton`. A small
   Cloudflare Pages Function (`functions/xrpc/[method].js`) returns a page of
   post IDs; Bluesky fills in the post contents itself.

Cost: free on GitHub (public repo) and Cloudflare's free tier.

## Setup

### 1. Edit `config.py`
Set `HASHTAG`, `SERVICE_HOSTNAME`, `FEED_RKEY`, display name and description.
Leave `PUBLISHER_DID` for now (step 6 gives it to you).

### 2. Make a Bluesky app password
Bluesky → Settings → Privacy and security → App passwords → Add. Don't use
your main password anywhere in this repo.

### 3. Push to GitHub
Create a **public** repo (Actions minutes are unlimited for public repos; a
private repo's 2,000 free minutes/month run out at this schedule) and push
these files.

### 4. Cloudflare
- Create a free account at dash.cloudflare.com.
- Copy your **Account ID** (Workers & Pages overview, right sidebar).
- My Profile → API Tokens → Create Token → "Edit Cloudflare Workers"
  template (includes Pages edit permission). Copy the token.

### 5. Add secrets to the GitHub repo
Settings → Secrets and variables → Actions:

| Kind | Name | Value |
|---|---|---|
| Secret | `BSKY_HANDLE` | e.g. `you.bsky.social` or your domain handle |
| Secret | `BSKY_APP_PASSWORD` | the app password from step 2 |
| Secret | `CLOUDFLARE_API_TOKEN` | token from step 4 |
| Secret | `CLOUDFLARE_ACCOUNT_ID` | account ID from step 4 |
| Variable | `CF_PAGES_PROJECT` | a project name, e.g. `yourtag-feed` |

Then Actions tab → "Update feed" → **Run workflow**. The first run backfills
recent posts, creates the Pages project and deploys it to
`<project>.pages.dev`.

### 6. Point your subdomain at it
Cloudflare → Workers & Pages → your project → Custom domains → add
`feed.example.com`. Cloudflare shows a **CNAME** record to create at your
domain registrar (name `feed`, target `<project>.pages.dev`). HTTPS is set up
automatically once DNS resolves (minutes to an hour).

Check that `https://feed.example.com/.well-known/did.json` loads.

### 7. Publish the feed (once, on your own computer)
```
pip install -r requirements.txt
python publish_feed.py
```
It prints your DID and a link to the feed. Put the DID into
`config.PUBLISHER_DID`, commit, and run the workflow once more.
Open the link, pin or like the feed, and share it.

## Day to day
- **Block a spammer:** add their handle or DID to `BLOCKED_AUTHORS`, commit.
  Their old posts disappear on the next deploy.
- **Rename the feed:** edit config, re-run `publish_feed.py`.
- **Faster updates:** change the cron to `*/10`. Don't go below that; each run
  logs in to Bluesky and logins are rate-limited (300/day).
- GitHub pauses scheduled workflows in repos with no activity for 60 days;
  the bot's own commits normally keep it alive, but if a quiet hashtag gets no
  new posts for two months, re-enable it in the Actions tab.

## Files
| File | Purpose |
|---|---|
| `config.py` | all settings |
| `fetch_posts.py` | search Bluesky, update `data/posts.json` |
| `build_site.py` | write `site/` (did.json, posts.json, describe.json) |
| `functions/xrpc/[method].js` | answers Bluesky's feed requests with paging |
| `publish_feed.py` | registers the feed on your account (run once) |
| `.github/workflows/update-feed.yml` | the schedule |
