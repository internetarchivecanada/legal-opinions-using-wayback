"""Find which filings dockets and documents archive.org's RECAP collection holds.

archive.org's `usfederalcourts` collection ("RECAP US Federal Court Documents")
holds RECAP dockets as items named gov.uscourts.<court>.<pacer case id>, each
document inside as <item>.<document number>.<attachment number>.pdf. The
collection sits in USGovernmentDocuments, so it is part of Democracy's Library
through that collection's scope expression.

data/filings.json has no PACER case id to build those names from, but every
item records the CourtListener docket it came from in `source_url`, and that
is the docket id filings.json uses. So dockets are matched by searching
`source_url:(<id> OR ...)` a hundred at a time, keeping a hit only when its
source_url really contains /docket/<id>/. Then each matched item's file list
is read, and a filing counts as held only when the exact
<item>.<doc>.<att>.pdf is there. Variant names (<item>.<doc>.<att>_1.pdf) are
not used: which version they hold is not recorded.

Writes data/filings_ia.json, which filings.js reads to link a held document
to its archive.org PDF and a matched docket to its item. Public search only,
so the counts are a floor: an item can exist and be missing from the index.

    python3 build/ia_recap.py
"""

import datetime
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from courtlistener import AGENT

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEARCH = "https://archive.org/advancedsearch.php"
BATCH = 100


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": AGENT})
    for attempt in range(1, 7):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            time.sleep(5 * attempt)
    raise SystemExit(f"giving up on {url}")


def document(url):
    """(document number, attachment number) from a CourtListener document URL,
    /docket/<id>/<doc>/<slug>/ or /docket/<id>/<doc>/<att>/<slug>/."""
    m = re.match(r"/docket/\d+/(\d+)/(?:(\d+)/)?[^/]+/?$", url or "")
    return (m.group(1), m.group(2) or "0") if m else None


def docket_id(source_url):
    m = re.search(r"/docket/(\d+)/", source_url or "")
    return m.group(1) if m else None


def items(ids):
    """{docket id: archive.org item} for the dockets the collection holds."""
    found = {}
    for i in range(0, len(ids), BATCH):
        batch = ids[i:i + BATCH]
        q = "collection:usfederalcourts AND source_url:(" + " OR ".join(batch) + ")"
        r = get(SEARCH + "?" + urllib.parse.urlencode(
            [("q", q), ("fl[]", "identifier"), ("fl[]", "source_url"), ("rows", "500"), ("output", "json")]))["response"]
        if r["numFound"] > 500:
            raise SystemExit(f"batch at {i} matched {r['numFound']} items; lower BATCH")
        for doc in r["docs"]:
            urls = doc.get("source_url")
            for u in urls if isinstance(urls, list) else [urls]:
                d = docket_id(u)
                if d in batch:
                    if found.get(d, doc["identifier"]) != doc["identifier"]:
                        raise SystemExit(f"docket {d} is in two items: {found[d]}, {doc['identifier']}")
                    found[d] = doc["identifier"]
        print(f"  searched {min(i + BATCH, len(ids))}/{len(ids)}, {len(found)} held", file=sys.stderr, flush=True)
    return found


def files(item):
    return item, {f["name"] for f in get(f"https://archive.org/metadata/{item}/files").get("result", [])}


def main():
    dockets = json.loads((ROOT / "data/filings.json").read_text())
    held = items([d["id"] for d in dockets])
    with ThreadPoolExecutor(6) as ex:
        names = dict(ex.map(files, sorted(set(held.values()))))
    out, n_filings, n_held = {}, 0, 0
    for d in dockets:
        item = held.get(d["id"])
        n_filings += len(d["filings"])
        if not item:
            continue
        docs = {}
        for f in d["filings"]:
            doc = document(f.get("url"))
            if doc and f"{item}.{doc[0]}.{doc[1]}.pdf" in names[item]:
                docs[f["id"]] = f"{doc[0]}.{doc[1]}"
        n_held += len(docs)
        out[d["id"]] = {"item": item, "documents": docs}
    result = {
        "built": datetime.date.today().isoformat(),
        "source": "archive.org collection usfederalcourts, public search",
        "dockets_checked": len(dockets),
        "dockets_held": len(out),
        "filings_checked": n_filings,
        "filings_held": n_held,
        "dockets": out,
    }
    (ROOT / "data/filings_ia.json").write_text(json.dumps(result, separators=(",", ":")) + "\n")
    print(f"{len(out)} of {len(dockets)} dockets and {n_held} of {n_filings} filings held on archive.org")


if __name__ == "__main__":
    main()
