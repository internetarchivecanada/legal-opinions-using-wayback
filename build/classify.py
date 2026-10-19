"""Who filed a RECAP document, and what kind of filing it is.

Read from the docket entry's description and whether the document is an
attachment. This is a heuristic: every record keeps the description it was
classified from, and anything no rule matches is "other", never dropped.

Rules are tried in order and the first match wins, so the order matters:
"MEMORANDUM OPINION AND ORDER" is the court's, but "MEMORANDUM in Opposition
to Motion" is a party's.
"""

import re

COURT, PARTY, UNKNOWN = "court", "party", "unknown"


def _rx(*terms):
    return re.compile(r"\b(?:" + "|".join(terms) + r")\b", re.I)


# (filer, kind, pattern), first match wins.
RULES = [
    (PARTY, "exhibit", _rx(r"exhibits?")),
    (PARTY, "declaration", _rx(r"declarations?", r"affidavits?")),
    (PARTY, "argument", _rx(r"memorandum (?:of law )?in (?:support|opposition)",
                            r"brief", r"reply", r"response", r"opposition", r"objections?")),
    (COURT, "opinion", _rx(r"opinion", r"memorandum and order", r"memorandum decision",
                           r"findings of fact")),
    (COURT, "recommendation", _rx(r"report and recommendations?", r"recommendation")),
    (COURT, "judgment", _rx(r"judgment", r"verdict")),
    (COURT, "order", _rx(r"order", r"ruling")),
    (PARTY, "motion", _rx(r"motions?", r"letter motion", r"letter")),
    (PARTY, "pleading", _rx(r"complaint", r"answer", r"petition", r"counterclaim")),
    (UNKNOWN, "transcript", _rx(r"transcripts?")),
]


def classify(description, attachment_number=0):
    """Return (filer, kind) for one RECAP document."""
    text = description or ""
    # A bare "ORDER" granting a motion mentions the motion: check the court's
    # own words at the start first.
    if re.match(r"\s*(?:memorandum\s+)?(?:opinion|order|judgment)\b", text, re.I):
        for filer, kind, rx in RULES:
            if filer == COURT and rx.search(text):
                return filer, kind
    if attachment_number:
        # Attachments are overwhelmingly exhibits, and their descriptions are
        # often just "Exhibit A" or a party's own label.
        for filer, kind, rx in RULES[:2]:
            if rx.search(text):
                return filer, kind
        return PARTY, "exhibit"
    for filer, kind, rx in RULES:
        if rx.search(text):
            return filer, kind
    return UNKNOWN, "other"
