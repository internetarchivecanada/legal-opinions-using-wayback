# legal-opinions-using-wayback

Court opinions that cite the Wayback Machine, on a timeline.

### → **[Explorer](https://internetarchivecanada.github.io/legal-opinions-using-wayback/)**

The explorer is not built yet; until it is, that address serves this README.

Data comes from [CourtListener](https://www.courtlistener.com/): its case-law
opinions and its RECAP archive of federal court filings.

## What is counted

`build/harvest.py` includes an opinion when CourtListener's full-text search
finds one of these exact phrases in it: `"web.archive.org"`,
`"wayback machine"`, `"archive.org/web"`. Each record says which phrases
matched. The data committed in `data/` is a wider, merged set that also
counts "Internet Archive" on its own; see [The data in this
repo](#the-data-in-this-repo).

Every count is a floor. An opinion that cites an archived page some other way
— a shortened link, a perma.cc link to a Wayback capture, "Internet Archive"
alone — is not found. Unquoted searches are not used: CourtListener matches
the words separately, and the extra hits were mostly unrelated.

This first version covers **case-law opinions only**, read from the search
API, which needs no token. Two things wait on a CourtListener API token:

- **RECAP.** Federal trial-court filings. At least 19,780 RECAP documents
  matched the same three phrases on 2026-10-19, but that includes briefs,
  exhibits and motions; separating the opinions and orders needs
  authenticated queries.
- **The cited URLs.** Search returns only a highlighted snippet. Extracting
  every Wayback URL an opinion cites needs its full text, from the opinion
  endpoint, which refuses requests without a token.

## Running it

```bash
python3 build/harvest.py
python3 -m http.server 8000
```

The harvest uses the standard library only, and checks that it received every
result each search reported. It writes `data/opinions.json`, one record per
opinion cluster, and `data/harvest.json`, recording when it ran and what each
search returned. Set `COURTLISTENER_TOKEN` to send a token.

Every view of the explorer is a link: `?year=2021`, `?court=cafc`,
`?phrase=wayback%20machine`, `?q=trademark`.

## Federal court filings (RECAP) — in progress

How parties use the Wayback Machine, not only how courts do. RECAP holds
federal trial-court filings bought from PACER; CourtListener searches them,
and archive.org holds each one's PDF and OCR text.

1. `build/recap_harvest.py` finds filings that contain one of the three
   phrases and labels each by **who filed it** (court or party) and **what
   kind of filing** it is: opinion, order, recommendation, judgment, motion,
   argument, declaration, exhibit, pleading, or other. The labels come from
   the docket entry's description (`build/classify.py`); attachments default
   to exhibits. It is a heuristic, so every row keeps the description it was
   labelled from, and nothing unmatched is dropped.
2. `build/recap_text.py` reads each filing's OCR text from archive.org and
   pulls out the Wayback URLs it cites (`build/wayback_urls.py`), with the
   capture timestamp. Timestamps survive OCR well; target addresses often
   don't, because a URL that wrapped on the printed page is cut short. Each
   URL keeps the raw text it was read from.

RECAP holds only what someone bought from PACER, so coverage leans heavily
toward high-profile cases. The full harvest needs `COURTLISTENER_TOKEN`.

```bash
python3 -m unittest discover -s tests
```

## The data in this repo

`data/opinions.json` has 687 opinions. It's built from two saved sources by
`python3 build/merge_sources.py`, which needs no network:

- `data/sources/workbook/`: every tab of the *Wayback Machine in U.S. Courts*
  workbook (as of 2026-09-18), as CSV. Its Decisions tab has 556 opinions
  matching `"Wayback Machine"` or `web.archive.org`, with Internet Archive
  party cases left out. The other tabs cover RECAP: 3,349 federal dockets and
  4,916 filings.
- `data/sources/courtlistener-search-2026-10-20.json`: 428 opinions from an
  authenticated search for `"Wayback Machine" OR "Internet Archive" OR
  "archive.org"`, and which 159 of them match `"Internet Archive"`.

297 opinions are in both. The search adds opinions that name the Internet
Archive without citing a capture (tagged `internet archive`), and 61 that are
in neither the workbook nor the "Internet Archive" results (tagged
`archive.org`). That tag is inferred, not a recorded match: those opinions
matched the combined search, and the workbook already covers
`"Wayback Machine"` through 2026-09-18, with no new matches since. Four are cases the Internet
Archive is a party to, marked `internet_archive_party`. Opinions from the
workbook also carry `court_level`, `state`, `circuit`, `claim` and
`judicial_notice`.

Running `build/harvest.py` overwrites `data/opinions.json`. Run
`build/merge_sources.py` again to get the merged set back.
