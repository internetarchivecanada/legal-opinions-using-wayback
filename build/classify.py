"""Who filed a RECAP document, and what kind of filing it is.

Read from the docket entry's description. Docket text opens with what the
filing is — "MOTION to Strike…", "DECLARATION of…", "ORDER granting 12
Motion…" — so the rule whose match comes earliest wins, and later mentions of
other filings ("…re 16 MOTION to Dismiss") lose to it. Ties go to the rule
listed first.

The trailing "(Attachments: # 1 Exhibit A, …)" list is ignored: it names the
attachments, not the filing, and reading it labelled every filing an exhibit.
An attachment is read from its own short description first, because its
description is the whole entry's; attachments with nothing else to go on are
exhibits.

It is a heuristic. Every record keeps the description it was classified
from, and anything no rule matches is "other", never dropped.
"""

import re

COURT, PARTY, UNKNOWN = "court", "party", "unknown"


def _rx(*terms):
    return re.compile(r"\b(?:" + "|".join(terms) + r")\b", re.I)


# (filer, kind, pattern). The earliest match in the description wins.
RULES = [
    (COURT, "opinion", _rx(r"(?:memorandum\s+)?opinion", r"memorandum and order", r"memorandum decision",
                           r"findings of fact")),
    (COURT, "recommendation", _rx(r"report and recommendations?", r"recommendation")),
    (COURT, "judgment", _rx(r"judgment", r"verdict")),
    (COURT, "order", _rx(r"order", r"ruling")),
    (PARTY, "argument", _rx(r"memorandum (?:of law )?in (?:support|opposition)", r"brief", r"reply",
                            r"response", r"opposition", r"objections?")),
    (PARTY, "declaration", _rx(r"declarations?", r"affidavits?")),
    (PARTY, "exhibit", _rx(r"exhibits?")),
    (PARTY, "motion", _rx(r"motions?", r"request for judicial notice", r"letter")),
    (PARTY, "pleading", _rx(r"complaint", r"answer", r"petition", r"counterclaim")),
    (UNKNOWN, "transcript", _rx(r"transcripts?")),
]

_ATTACHMENTS = re.compile(r"\(\s*attachments?\s*:.*$", re.I | re.S)


def _earliest(text):
    best = None
    for i, (filer, kind, rx) in enumerate(RULES):
        m = rx.search(text)
        if m and (best is None or (m.start(), i) < best[0]):
            best = ((m.start(), i), filer, kind)
    return best and best[1:]


def classify(description, attachment_number=0, short_description=None):
    """Return (filer, kind) for one RECAP document."""
    if attachment_number:
        return _earliest(short_description or "") or (PARTY, "exhibit")
    text = _ATTACHMENTS.sub("", description or short_description or "")
    # A docket entry like "ORDER granting 12 MOTION" is the court's, and so is
    # anything the court signs; but a party's "MOTION for entry of judgment"
    # is the party's. The earliest match settles both.
    return _earliest(text) or (UNKNOWN, "other")
