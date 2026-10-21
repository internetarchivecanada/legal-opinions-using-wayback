"""Find each opinion's own court PDF in the Wayback Machine.

CourtListener's search results give an opinion's download_url: the PDF as the
court published it (cdn.ca9.uscourts.gov, iowacourts.gov, courts.ms.gov ...).
Search works without a token, so this needs none. Each download_url is then
looked up in the Wayback Machine's CDX index for the first capture with HTTP
200 on or after the decision date, and kept only when that capture is a PDF:
an HTML capture at a PDF address is an error or landing page.

Writes data/opinions_wayback.json, which app.js reads to link an opinion to
the court's PDF as archived, "via Wayback Machine". Opinions with no
download_url, or none captured, keep their CourtListener link. Lookups are
cached in data/cache/ like every other request, so a rerun is cheap.

    python3 build/wayback_opinions.py
"""

import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from courtlistener import AGENT, CACHE, DATA, SEARCH, get

CDX = "https://web.archive.org/cdx/search/cdx"
PAUSE = 4.0  # the Wayback Machine refuses connections from clients that go faster
BATCH = 20


def download_urls(ids):
    """{cluster id: the court's own PDF address}, from CourtListener search."""
    found = {}
    for i in range(0, len(ids), BATCH):
        batch = ids[i:i + BATCH]
        page = get(SEARCH, {"type": "o", "q": "cluster_id:(" + " OR ".join(batch) + ")", "page_size": str(BATCH)})
        for r in page["results"]:
            url = next((op["download_url"] for op in r.get("opinions", []) if op.get("download_url")), None)
            if url:
                found[str(r["cluster_id"])] = url
    return found


def first_capture(url, since):
    """[timestamp, original, mimetype, status] of the first 200 capture of url on
    or after since (YYYYMMDD), or None."""
    q = CDX + "?" + urllib.parse.urlencode({"url": url, "output": "json", "filter": "statuscode:200",
                                             "from": since, "limit": "1", "fl": "timestamp,original,mimetype,statuscode"})
    cached = CACHE / "cdx" / (hashlib.sha256(q.encode()).hexdigest() + ".json")
    if cached.exists():
        rows = json.loads(cached.read_text())
    else:
        req = urllib.request.Request(q, headers={"User-Agent": AGENT})
        for attempt in range(1, 9):
            try:
                with urllib.request.urlopen(req, timeout=90) as r:
                    rows = json.load(r)
                break
            except urllib.error.HTTPError as e:
                if e.code not in (429, 503):
                    raise
                time.sleep(30 * attempt)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
                time.sleep(10 * attempt)
        else:
            raise SystemExit(f"giving up on {q}")
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(rows))
        time.sleep(PAUSE)
    return rows[1] if len(rows) > 1 else None


def main():
    opinions = json.loads((DATA / "opinions.json").read_text())
    urls = download_urls([str(o["id"]) for o in opinions])
    out = {}
    for n, o in enumerate(opinions, 1):
        url = urls.get(str(o["id"]))
        row = url and first_capture(url, o["date"].replace("-", ""))
        if row and row[2] == "application/pdf":
            out[str(o["id"])] = {"court_url": url, "timestamp": row[0], "original": row[1]}
        if n % 25 == 0:
            print(f"  {n}/{len(opinions)}", file=sys.stderr, flush=True)
    result = {
        "built": time.strftime("%Y-%m-%d"),
        "opinions_checked": len(opinions),
        "with_court_url": len(urls),
        "captured": len(out),
        "opinions": out,
    }
    (DATA / "opinions_wayback.json").write_text(json.dumps(result, indent=1) + "\n")
    print(f"{len(urls)} of {len(opinions)} opinions have a court PDF address; "
          f"{len(out)} were captured as PDFs on or after the decision")


if __name__ == "__main__":
    main()
