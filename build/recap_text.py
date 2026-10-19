"""Read each RECAP filing's text from archive.org and find the Wayback URLs.

Reads the filings file written by recap_harvest.py and adds, to each filing,
the Wayback URLs found in its OCR text (see wayback_urls.py) and whether the
text could be read at all. archive.org has no rate limit like CourtListener's,
but texts are cached in data/cache/ia/ all the same, so a rerun is cheap.

    python3 build/recap_text.py data/recap_test_filings.json
"""

import hashlib
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

from courtlistener import AGENT, CACHE
from wayback_urls import find

TEXTS = CACHE / "ia"


def text(url):
    """The text at url, or None if archive.org has none for this filing."""
    cached = TEXTS / (hashlib.sha256(url.encode()).hexdigest() + ".txt")
    if cached.exists():
        return cached.read_text()
    req = urllib.request.Request(url, headers={"User-Agent": AGENT})
    for attempt in range(1, 6):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read().decode("utf-8", "replace")
            break
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None
            time.sleep(10 * attempt)
        except (urllib.error.URLError, TimeoutError):
            time.sleep(10 * attempt)
    else:
        raise SystemExit(f"giving up on {url}")
    TEXTS.mkdir(parents=True, exist_ok=True)
    cached.write_text(body)
    return body


def main(path):
    path = pathlib.Path(path)
    filings = json.loads(path.read_text())
    read = found = 0
    for i, f in enumerate(filings, 1):
        body = text(f["ia_text"]) if f.get("ia_text") else None
        f["text_read"] = body is not None
        f["wayback"] = find(body) if body else []
        read += f["text_read"]
        found += bool(f["wayback"])
        if i % 50 == 0:
            print(f"  {i}/{len(filings)}", file=sys.stderr, flush=True)
    path.write_text(json.dumps(filings, indent=1, ensure_ascii=False) + "\n")
    print(f"{len(filings)} filings: text read for {read}, Wayback URLs found in {found}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1])
