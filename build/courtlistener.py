"""The one place that talks to CourtListener.

Every GET is cached in data/cache/ (ignored by git), so a run that stops —
usually on a rate limit — resumes where it left off. Delete the cache for a
fresh harvest.

Set COURTLISTENER_TOKEN to send a token. Search works without one, but
anonymous requests are cut off after a few dozen; the opinion, cluster and
RECAP document endpoints refuse them outright.
"""

import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SEARCH = "https://www.courtlistener.com/api/rest/v4/search/"
SITE = "https://www.courtlistener.com"
DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
CACHE = DATA / "cache"
PAUSE = 3.0
AGENT = "legal-opinions-using-wayback (Internet Archive)"


def get(url, params=None):
    """GET a JSON page, from the cache when it has been fetched before."""
    if params:
        url += "?" + urllib.parse.urlencode(params)
    cached = CACHE / (hashlib.sha256(url.encode()).hexdigest() + ".json")
    if cached.exists():
        return json.loads(cached.read_text())
    req = urllib.request.Request(url, headers={"User-Agent": AGENT})
    token = os.environ.get("COURTLISTENER_TOKEN")
    if token:
        req.add_header("Authorization", f"Token {token}")
    for attempt in range(1, 9):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                page = json.load(r)
            CACHE.mkdir(parents=True, exist_ok=True)
            cached.write_text(json.dumps(page))
            time.sleep(PAUSE)
            return page
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise
            wait = int(e.headers.get("Retry-After") or 60 * attempt)
            print(f"  {e.code}, waiting {wait}s", file=sys.stderr, flush=True)
            time.sleep(wait)
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"  {e}, waiting {30 * attempt}s", file=sys.stderr, flush=True)
            time.sleep(30 * attempt)
    raise SystemExit(f"giving up on {url}")


def search(query, kind, limit=None, **params):
    """Results for a search, and the count the API reported for it.

    With limit, stops after that many results: for testing, never for a
    harvest that is going to be published.
    """
    page = get(SEARCH, {"q": query, "type": kind, "highlight": "on", **params})
    count, results = page["count"], list(page["results"])
    while page.get("next") and not (limit and len(results) >= limit):
        page = get(page["next"])
        results += page["results"]
        print(f"  {len(results)}/{count}", file=sys.stderr, flush=True)
    return count, results[:limit] if limit else results
