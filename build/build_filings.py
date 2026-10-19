# Copyright (c) 2026 Internet Archive
#
# Author: Derek Fukumori
# Generated with assistance from Claude Opus 5 (claude-opus-5)
#
"""Build data/filings.json from the saved workbook, for the filings subpage.

Two tabs of the "Wayback Machine in U.S. Courts" workbook (as of 2026-09-18):

- data/sources/workbook/federal-dockets.csv: 3,349 federal dockets with a
  matching record, with the court, circuit, claim type and nature of suit.
- data/sources/workbook/filings.csv: 4,916 matching documents on those
  dockets — briefs, motions, exhibits, declarations and court orders.

The two join on Docket ID, and every filing has a docket, so the output nests
each docket's filings inside it. That is the shape the page reads: a docket
opens to the filings beneath it, the way CourtListener's own RECAP results do.

Document URLs are kept whole rather than rebuilt from the docket's slug.
Thirteen of the first two thousand carry a different slug from their docket's,
so rebuilding them would quietly produce links to the wrong page.

Standard library only, no network.
"""

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKBOOK = ROOT / 'data' / 'sources' / 'workbook'
OUT = ROOT / 'data' / 'filings.json'

# Document URLs look like /docket/<id>/<entry>/<attachment>/<slug>/, or without
# the attachment. The page shows the entry as CourtListener numbers it, "163.3".
ENTRY = re.compile(r'^/docket/\d+/([^/]+)/([^/]+)/')
CL = 'https://www.courtlistener.com'


def path_of(url: str) -> str:
    """ Reduce a CourtListener URL to its path, or '' if it is not one.

        Two filings in the workbook carry a bare domain with no path; those
        become '' so the page can render them without a link.

        Args:
            url: (str) The URL as the workbook records it.

        Returns:
            (str) The path beginning '/docket/', or an empty string.
    """
    url = (url or '').strip()
    if not url.startswith(CL):
        return ''
    path = url[len(CL):]
    return path if path.startswith('/docket/') else ''


def entry_label(path: str) -> str:
    """ Read the entry number, and attachment if there is one, from a path.

        Args:
            path: (str) A document path from path_of().

        Returns:
            (str) '163.3', '163', or '' when the path has neither.
    """
    m = ENTRY.match(path or '')
    if not m:
        return ''
    entry, attachment = m.group(1), m.group(2)
    if entry.isdigit() and attachment.isdigit():
        return f'{entry}.{attachment}'
    return entry if entry.isdigit() else ''


def read(name: str) -> list:
    """ Read one workbook tab.

        Args:
            name: (str) The CSV filename inside the workbook directory.

        Returns:
            (list) One dict per row.
    """
    with open(WORKBOOK / name, newline='', encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    csv.field_size_limit(2**31 - 1)
    dockets = read('federal-dockets.csv')
    filings = read('filings.csv')

    by_docket = defaultdict(list)
    for row in filings:
        by_docket[row['Docket ID']].append(row)

    orphans = sum(1 for row in filings
                  if row['Docket ID'] not in {d['Docket ID'] for d in dockets})
    if orphans:
        print(f'warning: {orphans} filings have no docket row', file=sys.stderr)

    out = []
    for d in dockets:
        rows = by_docket.get(d['Docket ID'])
        if not rows:
            continue
        docs = []
        for r in sorted(rows, key=lambda r: (r['Document date'] or '', r['Document ID'])):
            path = path_of(r['Document URL'])
            filer = (r['Filer'] or '').strip()
            # The workbook reads the filer out of docket text, and 28 rows come
            # back as a stray initial or honorific — 'C', 'Mr', 'St'. Those name
            # nobody, so they are treated the same as an absent filer. An
            # all-capital short value like 'USA' is kept.
            if len(filer) < 4 and not (filer.isupper() and len(filer) >= 3):
                filer = ''
            docs.append({
                'id': r['Document ID'],
                'entry': entry_label(path),
                'date': r['Document date'] or '',
                'type': r['Filing type'] or 'Other filing',
                'by': 'court' if r['Who invoked it'] == 'Court' else 'party',
                'available': r['Document available?'] == 'Yes',
                'filer': '' if filer.startswith('Not identified') else filer,
                'description': re.sub(r'\s+', ' ', r['Docket description'] or '').strip()[:280],
                'url': path,
            })
        out.append({
            'id': d['Docket ID'],
            'case': d['Case name'],
            'docket': d['Docket number'],
            'court': d['Court'],
            'state': d['State'],
            'circuit': d['Circuit'],
            'claim': d['Claim / case type'],
            'nature': d['Nature of suit'] or '',
            'filed': d['Filed'] or '',
            'terminated': d['Terminated'] or '',
            'url': path_of(d['Docket URL']),
            'filings': docs,
        })

    # Newest matching filing first, which is how the page lists them.
    out.sort(key=lambda d: max([f['date'] for f in d['filings']] or ['']), reverse=True)
    with open(OUT, 'w', encoding='utf-8') as handle:
        json.dump(out, handle, separators=(',', ':'))

    total = sum(len(d['filings']) for d in out)
    court = sum(1 for d in out for f in d['filings'] if f['by'] == 'court')
    print(f'{len(out)} dockets, {total} filings ({court} court-authored) -> {OUT.name} '
          f'({OUT.stat().st_size / 1024 / 1024:.2f} MB)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
