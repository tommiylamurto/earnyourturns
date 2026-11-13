// Cloudflare Pages Function: answers Bluesky's requests at /xrpc/<method>.
// Static files can't read ?limit=&cursor=, so this tiny function pages
// through the prebuilt feeds/<rkey>.json. Free tier: 100k requests/day.

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json",
      "access-control-allow-origin": "*",
      "cache-control": "public, max-age=60",
    },
  });

async function loadAsset(env, request, path) {
  const res = await env.ASSETS.fetch(new URL(path, request.url));
  if (!res.ok) return null;
  return res.json();
}

// ?feed=at://did:plc:.../app.bsky.feed.generator/<rkey>  ->  "<rkey>"
function feedRkey(feedParam) {
  const m = /\/app\.bsky\.feed\.generator\/([a-zA-Z0-9-]{1,64})$/.exec(feedParam || "");
  return m ? m[1] : null;
}

export async function onRequest({ request, env, params }) {
  const url = new URL(request.url);

  if (params.method === "app.bsky.feed.describeFeedGenerator") {
    return json(await loadAsset(env, request, "/describe.json"));
  }

  if (params.method === "app.bsky.feed.getFeedSkeleton") {
    const rkey = feedRkey(url.searchParams.get("feed"));
    const posts = rkey && (await loadAsset(env, request, `/feeds/${rkey}.json`)); // newest first
    if (!posts) return json({ error: "UnknownFeed", message: "No such feed here" }, 400);
    let limit = parseInt(url.searchParams.get("limit") || "50", 10);
    if (!Number.isFinite(limit)) limit = 50;
    limit = Math.min(Math.max(limit, 1), 100);

    // Cursor = "<timestamp>::<uri>" of the last post on the previous page.
    let start = 0;
    const cursor = url.searchParams.get("cursor");
    if (cursor) {
      const sep = cursor.indexOf("::");
      if (sep < 0) return json({ error: "BadCursor", message: "Malformed cursor" }, 400);
      const ct = cursor.slice(0, sep);
      const cu = cursor.slice(sep + 2);
      start = posts.findIndex((p) => p.t < ct || (p.t === ct && p.uri < cu));
      if (start < 0) return json({ feed: [] });
    }

    const page = posts.slice(start, start + limit);
    const body = { feed: page.map((p) => ({ post: p.uri })) };
    if (start + limit < posts.length && page.length) {
      const last = page[page.length - 1];
      body.cursor = `${last.t}::${last.uri}`;
    }
    return json(body);
  }

  return json({ error: "MethodNotImplemented", message: params.method }, 501);
}
