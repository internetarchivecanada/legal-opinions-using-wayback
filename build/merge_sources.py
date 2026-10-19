"""Build data/opinions.json and data/harvest.json from the saved sources.

Two sources, both from CourtListener's case-law opinions:

- data/sources/workbook/decisions.csv: the Decisions tab of the "Wayback
  Machine in U.S. Courts" workbook (as of 2026-09-18). Exact-phrase searches
  for "Wayback Machine" and web.archive.org, with matters where the Internet
  Archive is a party left out.
- data/sources/courtlistener-search-2026-10-20.json: an authenticated search
  for "Wayback Machine" OR "Internet Archive" OR "archive.org", plus which of
  those opinions match "Internet Archive" on its own.

Only opinions with a recorded "Wayback Machine" or web.archive.org match go
into data/opinions.json. The search's other results — "Internet Archive"
mentions, and "archive.org" matches that CourtListener finds as the separate
words "archive" and "org" — go to data/excluded.json, each with its reason.

Records are joined on the CourtListener cluster id. The workbook supplies the
richer fields where it has the opinion; the search fills in the rest.

Writes the same record shape as build/harvest.py, plus a few extra fields the
workbook carries. Standard library only, no network.
"""

import csv
import datetime
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "sources"
OUT = ROOT / "data"
SNIPPET = 400

WORKBOOK_PHRASES = {'"Wayback Machine"': "wayback machine", "web.archive.org": "web.archive.org"}

# The phrases that show a Wayback citation. An opinion is published only with
# one of these recorded; anything else goes to data/excluded.json with the
# reason, so it can be checked and brought back rather than lost.
WAYBACK = {"wayback machine", "web.archive.org"}
REASONS = {
    "archive.org": 'Matched only CourtListener\'s search for "archive.org", which matches the words '
                   '"archive" and "org" side by side, in any form ("Archives" counts), not the literal '
                   "address. The saved data has no text to confirm a literal archive.org.",
    "internet archive": "Names the Internet Archive; no Wayback citation is recorded.",
}


def court_id(name, courts):
    if name in courts:
        return courts[name]
    if name.rstrip(".") + "." in courts:
        return courts[name.rstrip(".") + "."]
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def cluster(url, fallback):
    m = re.search(r"/opinion/(\d+)/", url or "")
    return int(m.group(1)) if m else int(fallback)


def main():
    courts = json.loads((SRC / "courtlistener-courts.json").read_text())
    search = json.loads((SRC / "courtlistener-search-2026-10-20.json").read_text())
    with open(SRC / "workbook" / "decisions.csv", newline="") as f:
        decisions = list(csv.DictReader(f))
    with open(SRC / "workbook" / "excluded.csv", newline="") as f:
        party = {cluster(r["URL"], 0) for r in csv.DictReader(f) if r["Record type"] == "Decision"}

    opinions = {}
    for d in decisions:
        cid = cluster(d["Decision URL"], d["Record ID"])
        snippet = (d["Context snippet"] or "").strip()
        opinions[cid] = {
            "id": cid,
            "case": d["Case name"],
            "court": d["Court"],
            "court_id": court_id(d["Court"], courts),
            "date": d["Date filed"][:10],
            "docket": d["Docket"],
            "citations": [c.strip() for c in d["Citation"].split(";") if c.strip()],
            "url": d["Decision URL"],
            "pdfs": [],
            "snippets": [snippet[:SNIPPET] + ("…" if len(snippet) > SNIPPET else "")] if snippet else [],
            "phrases": [WORKBOOK_PHRASES[p.strip()] for p in d["Matched searches"].split(";") if p.strip()],
            "court_level": d["Court level"],
            "state": d["State"],
            "circuit": d["Circuit"],
            "claim": d["Claim / case type"],
            "judicial_notice": d["Judicial notice"] == "Confirmed phrase match",
            "internet_archive_party": False,
            "sources": ["workbook"],
        }

    for r in search["opinions"]:
        cid = r["cluster_id"]
        rec = opinions.get(cid)
        if rec is None:
            rec = opinions[cid] = {
                "id": cid,
                "case": r["case_name"],
                "court": r["court"],
                "court_id": court_id(r["court"], courts),
                "date": r["date"],
                "docket": "",
                "citations": [],
                "url": f"https://www.courtlistener.com/opinion/{cid}/",
                "pdfs": [],
                "snippets": [],
                "phrases": [],
                "court_level": "",
                "state": "",
                "circuit": "",
                "claim": "",
                "judicial_notice": False,
                "internet_archive_party": cid in party or "internet archive" in r["case_name"].lower(),
                "sources": [],
            }
        if r["matches_internet_archive"] and "internet archive" not in rec["phrases"]:
            rec["phrases"].append("internet archive")
        if not rec["phrases"]:
            # Matched the combined search, but isn't in the workbook's
            # "Wayback Machine" / web.archive.org results or the "Internet
            # Archive" search. An inferred tag, not a recorded match: a
            # party case the workbook left out could still be a
            # "Wayback Machine" hit.
            rec["phrases"].append("archive.org")
        rec["cites"] = r["cite_count"]
        rec["sources"].append("courtlistener-2026-10-20")

    everything = sorted(opinions.values(), key=lambda o: (o["date"] or "", o["case"]))
    rows = [o for o in everything if WAYBACK & set(o["phrases"])]
    excluded = [{**o, "reason": " ".join(REASONS[p] for p in o["phrases"] if p in REASONS)}
                for o in everything if not WAYBACK & set(o["phrases"])]
    count = lambda p: sum(p in o["phrases"] for o in rows)
    in_both = sum(len(o["sources"]) == 2 for o in rows)
    harvest = {
        "started": search["retrieved"],
        "source": "CourtListener case-law opinions, from the Wayback Machine in U.S. Courts workbook "
                  "(as of 2026-09-18) and an authenticated CourtListener search (2026-10-20)",
        "searches": [
            {"query": '"wayback machine"', "count": None, "received": count("wayback machine"), "clusters": count("wayback machine")},
            {"query": '"web.archive.org"', "count": None, "received": count("web.archive.org"), "clusters": count("web.archive.org")},
        ],
        "totals": {
            "opinions": len(rows),
            "excluded": len(excluded),
            "excluded_archive_org_only": sum(o["phrases"] == ["archive.org"] for o in excluded),
            "excluded_internet_archive_only": sum(o["phrases"] == ["internet archive"] for o in excluded),
            "workbook_decisions": len(decisions),
            "search_results": len(search["opinions"]),
            "in_both": in_both,
            "internet_archive_party": sum(o["internet_archive_party"] for o in rows),
        },
        "built": datetime.date.today().isoformat(),
    }
    (OUT / "opinions.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    (OUT / "harvest.json").write_text(json.dumps(harvest, indent=1) + "\n")
    (OUT / "excluded.json").write_text(json.dumps(excluded, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(harvest["totals"]))
    for s in harvest["searches"]:
        print(f"{s['query']}: {s['clusters']}")


if __name__ == "__main__":
    main()
