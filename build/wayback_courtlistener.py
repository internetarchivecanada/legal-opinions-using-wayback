"""Find Wayback Machine captures of CourtListener pages, the second tier of sources.

METHODOLOGY.md puts Internet Archive copies first: RECAP at Internet Archive
for dockets and filings (data/filings_ia.json), the court's PDF in the Wayback
Machine for opinions (data/opinions_wayback.json). For what neither holds,
a Wayback Machine capture of the CourtListener page is still an Internet
Archive source, and comes before CourtListener live. This finds them:

- Dockets and filings: one CDX prefix query per docket,
  courtlistener.com/docket/<id>/, answers the docket page and every document
  page under it. Addresses are compared in full, query string included:
  CourtListener's ?redirect_or_modal=True pop-up variant is a different page.
- Opinions: one exact-address CDX lookup per CourtListener opinion page.

Each item takes the first capture with HTTP 200 on or after its date. Writes
data/wayback_courtlistener.json. CDX responses are cached in data/cache/cdx/,
and requests are paced, as METHODOLOGY.md requires.

    python3 build/wayback_courtlistener.py
"""

import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from courtlistener import AGENT, CACHE, DATA, SITE

CDX = "https://web.archive.org/cdx/search/cdx"
PAUSE = 5.0
FIELDS = "timestamp,original,mimetype,statuscode"


def cdx(params):
    q = CDX + "?" + urllib.parse.urlencode(params)
    cached = CACHE / "cdx" / (hashlib.sha256(q.encode()).hexdigest() + ".json")
    if cached.exists():
        return json.loads(cached.read_text())
    req = urllib.request.Request(q, headers={"User-Agent": AGENT})
    for attempt in range(1, 12):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                rows = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):  # rate limit or a temporary server error
                raise
        except (OSError, json.JSONDecodeError):  # URLError, timeouts and dropped connections are all OSError
            pass
        time.sleep(min(30 * attempt, 300))
    else:
        raise SystemExit(f"giving up on {q}")
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_text(json.dumps(rows))
    time.sleep(PAUSE)
    return rows


def path(url):
    """A CourtListener address without scheme, host, port or trailing slash. The
    query is kept: ?redirect_or_modal=True is a different page."""
    p, _, query = re.sub(r"^(https?://)?(www\.)?courtlistener\.com(:\d+)?", "", url).partition("?")
    return (p.rstrip("/") + ("?" + query if query else "")).lower()


def first(rows, url, since):
    """The earliest capture of exactly url on or after since (YYYYMMDD)."""
    hits = sorted(r for r in rows if path(r[1]) == path(url) and r[0][:8] >= since)
    return {"timestamp": hits[0][0], "original": hits[0][1]} if hits else None


def since(date):
    return (date or "1996").replace("-", "")


def main():
    dockets = json.loads((DATA / "filings.json").read_text())
    held = json.loads((DATA / "filings_ia.json").read_text())["dockets"]
    court_pdfs = json.loads((DATA / "opinions_wayback.json").read_text())["opinions"]
    opinions = json.loads((DATA / "opinions.json").read_text())
    out = {"dockets": {}, "filings": {}, "opinions": {}}

    for n, d in enumerate(dockets, 1):
        h = held.get(d["id"])
        wanted = [f for f in d["filings"] if f.get("url") and not (h and f["id"] in h["documents"])]
        if h and not wanted:
            continue
        rows = cdx({"url": f"courtlistener.com/docket/{d['id']}/", "matchType": "prefix",
                    "filter": "statuscode:200", "fl": FIELDS, "output": "json"})[1:]
        if not h and d.get("url") and (c := first(rows, SITE + d["url"], since(d.get("filed")))):
            out["dockets"][d["id"]] = c
        for f in wanted:
            if c := first(rows, SITE + f["url"], since(f.get("date"))):
                out["filings"][f["id"]] = c
        if n % 100 == 0:
            print(f"  dockets {n}/{len(dockets)}", file=sys.stderr, flush=True)

    for o in opinions:
        if str(o["id"]) in court_pdfs:
            continue
        rows = cdx({"url": o["url"], "output": "json", "filter": "statuscode:200", "from": since(o["date"]),
                    "limit": "1", "fl": FIELDS})
        if len(rows) > 1:
            out["opinions"][str(o["id"])] = {"timestamp": rows[1][0], "original": rows[1][1]}

    result = {"built": time.strftime("%Y-%m-%d"), **{f"{k}_captured": len(v) for k, v in out.items()}, **out}
    (DATA / "wayback_courtlistener.json").write_text(json.dumps(result, indent=1) + "\n")
    print(f"Wayback captures of CourtListener pages: {len(out['dockets'])} dockets, "
          f"{len(out['filings'])} filings, {len(out['opinions'])} opinions")


if __name__ == "__main__":
    main()
