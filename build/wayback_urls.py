"""Find Wayback Machine URLs in text, including text damaged by OCR.

RECAP text from archive.org is OCR, and it breaks addresses in predictable
ways — seen in real hits: "web. archive. org", "web archive .org",
"httos://", and a timestamp split as "20220730 14343 1". The pattern allows
whitespace and stray dots between the parts, then cleans what it captured.
The scheme in front of the host is not matched: OCR mangles it too often
("httos") to be worth repairing, and the cleaned URL supplies its own.
Every match keeps the raw text beside the cleaned URL, so a bad repair can be
seen and fixed.

The timestamp survives OCR well. The target often does not: a URL that
wrapped onto the next line on the printed page is cut short ("https://",
"http://s-") or misread ("abcnews.go.convUS").
"""

import re

_SEP = r"[\s.]*"
_HOST = _SEP.join("web") + _SEP + _SEP.join("archive") + r"\s*\.\s*" + _SEP.join("org")
_STAMP = r"(?P<stamp>\d[\d\s]{3,20}?)(?P<flag>[a-z]{2}_)?"
WAYBACK = re.compile(
    rf"{_HOST}\s*/\s*web\s*/\s*{_STAMP}\s*\*?\s*/\s*(?P<target>\S+)",
    re.I,
)
_TRAIL = ".,;:)]}>\"'"


def find(text):
    """Each distinct Wayback URL in text: url, timestamp, target, raw, count.

    A printed capture repeats its header on every page, so the same URL can
    appear dozens of times in one filing. It is listed once, with count.
    """
    out = {}
    for m in WAYBACK.finditer(text or ""):
        stamp = re.sub(r"\s", "", m["stamp"])
        target = m["target"].rstrip(_TRAIL)
        target = re.sub(r"^(https?):/(?!/)", r"\1://", target, flags=re.I)
        if not 4 <= len(stamp) <= 14:
            continue
        url = f"https://web.archive.org/web/{stamp}/{target}"
        if url in out:
            out[url]["count"] += 1
        else:
            out[url] = {"url": url, "timestamp": stamp, "target": target, "raw": m.group(0), "count": 1}
    return list(out.values())
