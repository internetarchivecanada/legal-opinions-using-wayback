"""Harvest RECAP filings that cite the Wayback Machine, and classify them.

Searches CourtListener's RECAP archive (type=r, one result per docket with its
matching documents nested) for each exact phrase, then records one row per
document: the case, the docket entry's description, who filed it and what
kind of filing it is (see classify.py), and where its text is on archive.org.

Writes data/recap_filings.json and data/recap_harvest.json. Run
recap_text.py afterwards to read each filing's text from archive.org and pull
out the Wayback URLs it cites.

    python3 build/recap_harvest.py --inspect      # print the fields the API returns
    python3 build/recap_harvest.py --limit 40     # a test run; not for publishing
    python3 build/recap_harvest.py                # the whole harvest

The whole harvest needs COURTLISTENER_TOKEN: anonymous requests are cut off
after a few dozen, and this is hundreds of pages.
"""

import argparse
import datetime
import json
import sys

from classify import classify
from courtlistener import DATA, SITE, SEARCH, get, search

PHRASES = ["web.archive.org", "wayback machine", "archive.org/web"]
IA = "https://archive.org/download"


def ia_name(court, pacer_case_id, doc, att):
    """archive.org's name for a RECAP document, without extension.

    Items are gov.uscourts.<court>.<pacer case id>, and each document inside is
    <item>.<document number>.<attachment number>, attachment 0 being the main
    document. Checked against gov.uscourts.nysd.590045 on 2026-10-19.
    """
    if not (court and pacer_case_id and doc not in (None, "")):
        return None, None
    item = f"gov.uscourts.{court}.{pacer_case_id}"
    return item, f"{item}.{doc}.{att or 0}"


def rows(docket, phrase):
    for d in docket.get("recap_documents") or []:
        att = d.get("attachment_number") or 0
        filer, kind = classify(d.get("description"), att, d.get("short_description"))
        item, name = ia_name(docket.get("court_id"), docket.get("pacer_case_id"), d.get("document_number"), att)
        yield {
            "id": d.get("id"),
            "docket_id": docket.get("docket_id"),
            "case": docket.get("caseName"),
            "court": docket.get("court"),
            "court_id": docket.get("court_id"),
            "docket": docket.get("docketNumber"),
            "case_filed": docket.get("dateFiled"),
            "date": d.get("entry_date_filed"),
            "document_number": d.get("document_number"),
            "attachment_number": att,
            "description": d.get("description"),
            "short_description": d.get("short_description"),
            "filer": filer,
            "kind": kind,
            "url": SITE + d["absolute_url"] if d.get("absolute_url") else None,
            "ia_item": item,
            "ia_pdf": f"{IA}/{item}/{name}.pdf" if name else None,
            "ia_text": f"{IA}/{item}/{name}_djvu.txt" if name else None,
            "snippet": d.get("snippet"),
            "phrases": [phrase],
        }


def inspect():
    page = get(SEARCH, {"q": f'"{PHRASES[0]}"', "type": "r", "highlight": "on"})
    print("count", page.get("count"), "document_count", page.get("document_count"))
    docket = page["results"][0]
    print("docket fields:", sorted(k for k in docket if k != "recap_documents"))
    print("document fields:", sorted(docket["recap_documents"][0]))
    print("more_docs on first page:", sum(bool(r.get("more_docs")) for r in page["results"]), "of", len(page["results"]))
    for r in page["results"][:5]:
        for d in r["recap_documents"][:2]:
            print("-", r.get("court_id"), r.get("pacer_case_id"), d.get("document_number"), d.get("attachment_number"),
                  "|", (d.get("description") or "")[:70], "|", d.get("short_description"), "|", classify(d.get("description"), d.get("attachment_number"), d.get("short_description")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="stop after this many dockets per phrase (testing only)")
    ap.add_argument("--inspect", action="store_true", help="print the fields of one page and stop")
    args = ap.parse_args()
    if args.inspect:
        return inspect()

    started = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    filings, searches, truncated = {}, [], 0
    for phrase in PHRASES:
        query = f'"{phrase}"'
        print(query, file=sys.stderr, flush=True)
        count, dockets = search(query, "r", limit=args.limit)
        truncated += sum(bool(d.get("more_docs")) for d in dockets)
        searches.append({"query": query, "count": count, "received": len(dockets)})
        for docket in dockets:
            for row in rows(docket, phrase):
                key = row["id"] or (row["docket_id"], row["document_number"], row["attachment_number"])
                if key in filings:
                    if phrase not in filings[key]["phrases"]:
                        filings[key]["phrases"].append(phrase)
                else:
                    filings[key] = row

    out = sorted(filings.values(), key=lambda r: (r["date"] or "", r["case"] or ""))
    stem = "recap_test" if args.limit else "recap"
    (DATA / f"{stem}_filings.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    (DATA / f"{stem}_harvest.json").write_text(json.dumps({
        "started": started,
        "source": "CourtListener RECAP archive (search API, type=r)",
        "limit": args.limit,
        "searches": searches,
        "dockets_with_more_documents_than_returned": truncated,
    }, indent=1) + "\n")

    kinds = {}
    for r in out:
        kinds[(r["filer"], r["kind"])] = kinds.get((r["filer"], r["kind"]), 0) + 1
    for s in searches:
        print(f"{s['query']}: count {s['count']}, received {s['received']}", file=sys.stderr)
    print(f"{len(out)} filings; {truncated} dockets had more matching documents than the search returned", file=sys.stderr)
    for (filer, kind), n in sorted(kinds.items(), key=lambda kv: -kv[1]):
        print(f"  {filer:8} {kind:15} {n}", file=sys.stderr)
    if not args.limit:
        short = [s for s in searches if s["received"] != s["count"]]
        if short:
            raise SystemExit(f"enumeration incomplete: {short}")


if __name__ == "__main__":
    main()
