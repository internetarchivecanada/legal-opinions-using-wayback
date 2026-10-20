"""Harvest CourtListener case-law opinions that cite the Wayback Machine.

Runs one exact-phrase search per phrase, so every opinion records which
phrases matched it. Unquoted searches are not used: CourtListener matches the
words separately, and in a sample the extra hits were mostly noise.

Writes data/opinions.json (one record per opinion cluster) and
data/harvest.json (when it ran, and what each search returned).

Uses the search API only, which needs no token. Set COURTLISTENER_TOKEN to
send one anyway; the opinion and cluster endpoints, needed for full text,
refuse requests without it.
"""

import datetime
import json
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request

SEARCH = "https://www.courtlistener.com/api/rest/v4/search/"
SITE = "https://www.courtlistener.com"
PHRASES = ["web.archive.org", "wayback machine", "archive.org/web"]
OUT = pathlib.Path(__file__).resolve().parent.parent / "data"
PAUSE = 1.0


def get(url, params=None):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "legal-opinions-using-wayback (Internet Archive)"})
    token = os.environ.get("COURTLISTENER_TOKEN")
    if token:
        req.add_header("Authorization", f"Token {token}")
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:
            wait = 10 * (attempt + 1)
            print(f"  retry in {wait}s: {e}", file=sys.stderr)
            time.sleep(wait)
    raise SystemExit(f"giving up on {url}")


def search(query):
    """Every result for a query, plus the count the API reported for it."""
    page = get(SEARCH, {"q": query, "type": "o", "highlight": "on", "order_by": "dateFiled asc"})
    count, results = page["count"], list(page["results"])
    while page.get("next"):
        time.sleep(PAUSE)
        page = get(page["next"])
        results += page["results"]
        print(f"  {len(results)}/{count}", file=sys.stderr)
    return count, results


def record(r):
    return {
        "id": r["cluster_id"],
        "case": r["caseName"],
        "court": r["court"],
        "court_id": r["court_id"],
        "date": r["dateFiled"],
        "docket": r["docketNumber"],
        "citations": r["citation"],
        "url": SITE + r["absolute_url"],
        "pdfs": sorted({o["download_url"] for o in r["opinions"] if o.get("download_url")}),
        "snippets": [o["snippet"] for o in r["opinions"] if o.get("snippet", "").strip()],
        "phrases": [],
    }


def main():
    started = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    opinions, searches = {}, []
    for phrase in PHRASES:
        query = f'"{phrase}"'
        print(query, file=sys.stderr)
        count, results = search(query)
        ids = {r["cluster_id"] for r in results}
        searches.append({"query": query, "count": count, "received": len(results), "clusters": len(ids)})
        for r in results:
            rec = opinions.setdefault(r["cluster_id"], record(r))
            if phrase not in rec["phrases"]:
                rec["phrases"].append(phrase)
            for s in record(r)["snippets"]:
                if s not in rec["snippets"]:
                    rec["snippets"].append(s)
        time.sleep(PAUSE)

    union = " OR ".join(f'"{p}"' for p in PHRASES)
    union_count = get(SEARCH, {"q": union, "type": "o"})["count"]
    searches.append({"query": union, "count": union_count, "received": None, "clusters": len(opinions)})

    rows = sorted(opinions.values(), key=lambda o: (o["date"] or "", o["case"]))
    OUT.mkdir(exist_ok=True)
    (OUT / "opinions.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    (OUT / "harvest.json").write_text(json.dumps(
        {"started": started, "source": "CourtListener case-law opinions (search API, type=o)", "searches": searches},
        indent=1) + "\n")

    for s in searches:
        print(f"{s['query']}: count {s['count']}, received {s['received']}, clusters {s['clusters']}", file=sys.stderr)
    short = [s for s in searches if s["received"] is not None and s["received"] != s["count"]]
    if short or len(opinions) != union_count:
        raise SystemExit(f"enumeration incomplete: {short or ''} union {len(opinions)} vs count {union_count}")


if __name__ == "__main__":
    main()
