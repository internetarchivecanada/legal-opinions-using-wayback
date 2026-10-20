# Data source methodology

How the explorer decides where each opinion, docket and filing links, how
every link is found and checked, and the traps found so far. The README says
what the explorer shows; this file says how its links are chosen, so that
anyone (or any agent) extending them gets the same answer.

## The rule: Internet Archive first, CourtListener second

**Our data source is the Wayback Machine or an Internet Archive collection
whenever one holds the item. CourtListener is a secondary source**, used only
for what the Internet Archive does not hold, and alongside it where
CourtListener carries something the archive copy lacks.

## Sources, in order of preference

A card links to the first of these that holds the item, and says which with
its "via" line.

| Item | 1st | 2nd | Last |
|---|---|---|---|
| Opinion | The court's own PDF in the **Wayback Machine** (`data/opinions_wayback.json`) | The CourtListener opinion page as the **Wayback Machine** captured it | **CourtListener** case law, live |
| Filing (document) | Its PDF in **RECAP at Internet Archive** (`data/filings_ia.json`) | The CourtListener document page as the **Wayback Machine** captured it | **CourtListener** RECAP, live |
| Docket | Its item in **RECAP at Internet Archive** | The CourtListener docket page as the **Wayback Machine** captured it | **CourtListener** RECAP, live |
| Press about a case | A **Wayback Machine** capture of the article (`url`, with the live address in `original_url`) | — | — |

The second tier is a Wayback Machine capture of a CourtListener page: an
Internet Archive source for what no Internet Archive collection holds
directly. Lookups for it compare the full address (see the pop-up trap
below). The second tier is being collected as of 2026-10-20 and is not yet on
the site.

CourtListener stays beside an Internet Archive link wherever it carries
something the archive copy does not: the opinion's text and citations, or a
docket's full entry list (archive.org's RECAP items hold documents but no
docket sheet, none of the 2,642 matched on 2026-10-19).

RECAP at Internet Archive is archive.org's
[`usfederalcourts`](https://archive.org/details/usfederalcourts) collection. It
sits inside `USGovernmentDocuments`, so it is part of Democracy's Library
through that collection's scope expression, not through the
`democracys-library` tag. Say so whenever a count depends on it.

## Matching rules

**RECAP at Internet Archive** (`build/ia_recap.py`)

- Items are `gov.uscourts.<court>.<pacer case id>`; documents inside are
  `<item>.<document>.<attachment>.pdf`, attachment 0 being the main document.
- `data/filings.json` has no PACER case id. Match on the CourtListener docket
  id instead, which every item records in `source_url`: search
  `source_url:(<id> OR …)`, then keep a hit only when the URL really contains
  `/docket/<id>/`.
- A filing is held only when its exact `<item>.<doc>.<att>.pdf` is in the
  item's file list. Variant names (`…_1.pdf`) are not used: which version
  they hold is not recorded.

**Wayback Machine** (`build/wayback_opinions.py`, and any new lookup)

- Use the CDX index. Take the **first capture with HTTP 200 on or after the
  decision or filing date**; an earlier capture cannot be of this decision.
- Keep a capture of a PDF address only when its mimetype is
  `application/pdf`. An HTML capture there is an error or landing page.
- **Compare the full address, query string included.** CourtListener serves
  a pop-up variant of every document page at
  `…/?redirect_or_modal=True`, and the Wayback Machine captures it separately,
  often earlier. Dropping the query matches the pop-up instead of the page:
  on 2026-10-20 it gave *Authors Guild v. OpenAI* document 1072 a capture a
  day early. Scheme, `www.` and port may be ignored; the query may not.
- A prefix query (`url=courtlistener.com/docket/<id>/&matchType=prefix`)
  answers a docket page and all its document pages at once. Before trusting a
  prefix result, check it reproduces captures already found by exact-address
  lookups.
- Where the gap between decision and capture is long, open the PDF and
  confirm it carries the opinion's docket number: a court can reuse an
  address.

**Press and commentary** (`data/coverage.json`, curated by hand)

- Link only pages about that exact decision: same parties, court and ruling,
  not an earlier or later one in the same dispute. Check date, docket and
  citation against `data/opinions.json`. Read every page before linking it;
  never link from a search snippet.
- Exclude case-law databases, the opinion itself, filings and briefs, AI
  summary sites and pages that cannot be loaded.
- No limit on links per opinion, but each must be a different article, never
  the same address twice, live or archived.
- Link the Wayback capture dated on or after publication, loaded and
  confirmed to name the case. With no capture, list the article as unverified
  rather than linking it live. Do not use Save Page Now without asking.
- Wikipedia is not press: it gets its own section, and only for an article
  about the exact case, filing or opinion. An article about a later appeal or
  Supreme Court decision in the same dispute is not linked, for dockets as
  for opinions.
- Copies of one decision under several CourtListener ids (same normalized
  case name, court and date) share their links.

## Counting

- Every count is a floor: search finds what its index holds, and these use
  public search.
- Date every count, and say which mechanism produced it.
- Report what could not be checked, not only what could.

## Working with the services

- **`web.archive.org` throttles.** It answered 429 and then refused
  connections outright when queried by two processes at once, and refused
  intermittently even at one request a minute. Run one Wayback lookup at a
  time, pause at least 4 seconds between requests, cache every response, and
  make every run resumable.
- **Never record an error as "not captured".** Catch `OSError` (refused,
  reset and timed-out connections all are), retry with backoff, and keep
  failures marked as errors so a rerun retries them.
- **CourtListener's anonymous search** is rate-limited after a few dozen
  requests; honour `Retry-After`. Its search returns an opinion's
  `download_url` without a token; the opinion, cluster and RECAP document
  endpoints need one.
- **archive.org search**: the quoted form `source_url:"…"` returns nothing;
  use the token form `source_url:(…)`.
- **GitHub Pages** lets browsers cache files for 10 minutes, so a check right
  after a rebuild can show the old script with the new page. Bypass the cache
  before concluding a deploy failed.
- Read input data from `origin/main` (`git show origin/main:data/…`), not
  from a working tree that may be on an old branch: a lookup that read a
  missing file once queued every filing instead of the 2,211 that needed it.
