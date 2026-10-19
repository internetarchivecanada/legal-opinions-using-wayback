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
import sys
import time

from courtlistener import DATA as OUT, SITE, SEARCH, PAUSE, get, search

PHRASES = ["web.archive.org", "wayback machine", "archive.org/web"]


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
        print(query, file=sys.stderr, flush=True)
        count, results = search(query, "o", order_by="dateFiled asc")
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
