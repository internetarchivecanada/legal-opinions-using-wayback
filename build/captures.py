"""How old the archived page was when the court cited it.

Reads every Wayback URL printed in an opinion's snippets (data/opinions.json)
and saved passages (data/sources/passages), and compares the capture's
timestamp with the date the opinion was filed. Writes data/captures.json.

Only URLs with a full timestamp and a host shaped like a domain are kept.
OCR damage leaves some with an impossible date ("20013208") or a host that
is just a word ("and"); those are dropped rather than guessed at. Misreads
that still look like a domain ("phiUy.com", "utcourts.gow") stay, with the
full URL beside them so they can be checked.
"""

import datetime as dt
import json
import pathlib
import re
from urllib.parse import urlparse

import wayback_urls

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def texts(o):
    yield from o.get("snippets", [])
    p = DATA / "sources" / "passages" / f"{o['id']}.json"
    if p.exists():
        d = json.loads(p.read_text())
        for q in ("archive", "wayback"):
            for s in d[q]["snippets"]:
                yield s["text"]


def host(target):
    h = urlparse(target if "://" in target else "http://" + target).netloc.lower()
    h = h.removeprefix("www.")
    return h if re.fullmatch(r"[a-z0-9-]+(\.[a-z0-9-]+)+", h) else None


def main():
    rows = []
    for o in json.loads((DATA / "opinions.json").read_text()):
        if not o["date"]:
            continue
        filed = dt.date.fromisoformat(o["date"])
        seen = {}
        for t in texts(o):
            for u in wayback_urls.find(t):
                seen[u["url"]] = u
        for u in seen.values():
            ts, h = u["timestamp"], host(u["target"])
            try:
                captured = dt.date(int(ts[:4]), int(ts[4:6]), int(ts[6:8]))
            except ValueError:
                continue
            if not h or captured > filed:
                continue
            rows.append({"id": o["id"], "url": u["url"], "host": h, "captured": captured.isoformat(),
                         "filed": o["date"], "years": round((filed - captured).days / 365.25, 1)})
    rows.sort(key=lambda r: r["years"])
    out = {"about": "Wayback URLs printed in the opinions, with the capture date and how long before the "
                    "opinion it was taken. Only opinions that print the full URL count.",
           "captures": rows}
    (DATA / "captures.json").write_text(json.dumps(out, indent=1) + "\n")
    print(len(rows), "captures from", len({r["id"] for r in rows}), "opinions")


if __name__ == "__main__":
    main()
