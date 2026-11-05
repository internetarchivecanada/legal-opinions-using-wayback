# Security and accessibility checks

**Status: passing.** All three checks passed on 2026-11-05 at commit `6de6f8c144`. Nothing is open. Advisory items below are optional.

| | |
|---|---|
| Explorer | https://github.com/internetarchivecanada/legal-opinions-using-wayback |
| Commit | `6de6f8c144` on `explorer-checks` |
| Date | 2026-11-05 |
| Pages checked | `./`, `./?year=2021`, `filings.html`, `filings.html?year=2020` |
| Served from | repository root, served locally |
| Live site (headers) | https://internetarchivecanada.github.io/legal-opinions-using-wayback/ |
| Standard | WCAG 2.2 Level AA |
| Security references | OWASP Top 10:2025 and ASVS 5.0.0 |
| Tools | axe-core 4.14.0, html5lib, ruff, bandit, pip-audit, headless Chromium |
| Reviewed by | Claude (claude-opus-5-5) via the explorer-checks skill |
| Skill version | 2026.11.05.8 |

## Summary

| Check | Result | Must fix | Needs review | Advisory |
|---|---|---:|---:|---:|
| Code validity | Pass | 0 | 0 | 1 |
| Code security | Pass | 0 | 0 | 2 |
| Accessibility (WCAG 2.2 AA) | Pass | 0 | 0 | 0 |

## Standards met

Checked 5 November 2026 at commit `6de6f8c144`, on the pages listed above:

- **WCAG 2.2 Level AA**: every Level A and AA success criterion, by automated tests and a manual review of each criterion (checklists under each check below).
- **WCAG 2.1 Level AA** and **WCAG 2.0 Level AA**, which WCAG 2.2 includes. 4.1.1 Parsing, dropped from 2.2 but still in 2.0 and 2.1, is covered by the code validity check (no HTML parse errors, no duplicate ids).
- These are the web content requirements of **Section 508** (US federal; WCAG 2.0 AA) and **EN 301 549** clause 9 (WCAG 2.1 AA).
- Security was checked against the OWASP Top 10:2025 risks and ASVS 5.0.0 chapters that apply to an explorer; each finding and checklist item names its category. That is not an ASVS verification at any level.

## What a pass means

Each check combines automated tools with a review of the code and pages against a written checklist. A pass means neither found anything open on the date and commit above. The standards are met as far as those checks can establish: it is a self-assessment, not third-party certification. Automated testing finds a minority of accessibility barriers. Testing with people who use assistive technology is still worth doing, and a change to the explorer needs a re-run.

## Code validity

No open items.

## Code security

No open items.

<details><summary>Manual checklist (10 pass, 0 fail, 10 n/a)</summary>

| Item | Result | Note |
|---|---|---|
| No secrets | pass | No secret findings; the CourtListener token is read from COURTLISTENER_TOKEN (build/courtlistener.py:38); .env is gitignored; `git log --all -p` shows no token-shaped strings. |
| Untrusted data is escaped | pass | All 27 innerHTML sinks traced and cleared: every data field goes through esc() (escapes & first, then <>"'), or the value is a number or literal. The Wayback timestamp in via() is now escaped too. |
| URLs from data are safe | pass | Every href built from data goes through safeUrl() (app.js:24, filings.js:34), which allows only http(s); Wayback and archive.org links also use fixed https prefixes. |
| Harvested data is validated | pass | build_filings.py checks CourtListener URLs, ia_recap.py matches docket paths, wayback_opinions.py now keeps a CDX row only with a 14-digit timestamp and an http(s) original, and new tests in tests/test_build.py check every link and timestamp in data/*.json, including the hand-curated coverage files. |
| Third-party code is pinned | pass | No third-party scripts or stylesheets; everything is served from the explorer. |
| No mixed content | pass | Everything loads over https or from the same origin. One coverage link is http, but it is a link, not a load. |
| Dependencies are pinned and maintained | pass | Build is standard-library Python only; no requirements file, package.json or workflows. |
| Dependencies have no known vulnerabilities | pass | No dependencies to audit; no vendored JavaScript. |
| Third parties a visitor's browser contacts | pass | None. The fonts are served from fonts/ with their licences (Libre Caslon Text, SIL OFL 1.1; Special Elite, Apache 2.0); the browser check records no third-party requests. |
| What Pages publishes | pass | Public repository; Pages serves the root, which also publishes build/, tests/, data/sources/ (the workbook CSVs and saved CourtListener responses) and .claude/launch.json. Nothing there is sensitive. |
| Server input is validated | n/a | Static site, no server. |
| Configuration is safe to serve | n/a | Static site. |
| Errors are handled and do not leak | n/a | Static site. The opinions page catches a load failure and says so in #status. |
| Commands built from data | n/a | No subprocess calls. |
| Who can write | n/a | No contributions or uploads. |
| Fetches of submitted URLs | n/a | No submitted URLs. |
| Scope of writes | n/a | No uploads. |
| Limits | n/a | No public queue. |
| Model output is untrusted | n/a | No AI components at runtime. |
| Models are pinned | n/a | No models. |

</details>

<details><summary>Cleared on review (31)</summary>

| Id | Item | Where | Why cleared |
|---|---|---|---|
| `S-8706ef` | String rendered as markup or code (innerHTML) | `app.js:70` | Assigns the empty literal "" to clear the chart before buttons are built with createElement. |
| `S-49e2a5` | String rendered as markup or code (innerHTML) | `app.js:84` | `first` and `last` are numbers (`+years[0]`, `+years[years.length - 1]`); nothing else is interpolated. |
| `S-6291c2` | String rendered as markup or code (innerHTML) | `app.js:96` | drawScale() builds only from numbers: `(v / max) * 100` and `label(v)`, which returns the number or an Intl.NumberFormat string of it. |
| `S-2ed829` | String rendered as markup or code (innerHTML) | `app.js:144` | Empty literal "". |
| `S-63a8b0` | String rendered as markup or code (innerHTML) | `app.js:150` | `p` is a key of the literal TILES table (two-letter state codes) and `counts[p]` is a number. |
| `S-c85d42` | String rendered as markup or code (innerHTML) | `app.js:156` | `counts[NATIONWIDE]` is a number and placeName(NATIONWIDE) returns a fixed string. |
| `S-7a3e17` | String rendered as markup or code (innerHTML) | `app.js:170` | Empty literal "". |
| `S-51e943` | String rendered as markup or code (innerHTML) | `app.js:177` | The facet value goes through esc() (app.js:19, replaces & first, then <>"'); `n` and the bar width are numbers. |
| `S-a63475` | String rendered as markup or code (innerHTML) | `app.js:189` | Every interpolated value is an integer from data/filings_by_year.json, which build/merge_sources.py:252 writes as `int(y)` and counts it increments itself; heights are arithmetic on those. Wrapping them in esc() or Number() anyway would keep this safe if the file's source changes. |
| `S-f5bebc` | String rendered as markup or code (innerHTML) | `app.js:196` | Years are integers written by build/merge_sources.py:252; `f.as_of` goes through esc(). |
| `S-2821b7` | String rendered as markup or code (innerHTML) | `app.js:198` | total() sums integer counts from data/filings_by_year.json (merge_sources.py:252) and the rest is literal. |
| `S-86c013` | String rendered as markup or code (innerHTML) | `app.js:232` | `y`, `first`, `last` and `avg` are numbers (`+state.year` coerces the URL value; a non-number gives NaN and the view stays hidden); counts are lengths; type names and month names are literals; square() runs case, court, date and id through esc(), and the court type it adds is a COURT_TYPES literal.  |
| `S-fd8619` | String rendered as markup or code (innerHTML) | `app.js:269` | case, court and date each go through esc(). |
| `S-8ab224` | String rendered as markup or code (innerHTML) | `app.js:336` | Two counts (array lengths) and a literal button. |
| `S-100ef3` | String rendered as markup or code (innerHTML) | `app.js:344` | card() runs every data field through esc() (app.js:19, & first, then <>"'); snippet() escapes the CourtListener snippet before restoring only <mark>; via() now escapes the Wayback timestamp (app.js:278); every href goes through esc(safeUrl(...)), which allows only http(s) (app.js:24). Year headings  |
| `S-442390` | String rendered as markup or code (innerHTML) | `app.js:374` | meta.started, meta.source and each search query go through esc(); the rest is literal. |
| `S-ffd404` | String rendered as markup or code (innerHTML) | `filings.js:90` | Same drawScale() as app.js: numbers only. |
| `S-0e3f6b` | String rendered as markup or code (innerHTML) | `filings.js:104` | Empty literals. |
| `S-5f4397` | String rendered as markup or code (innerHTML) | `filings.js:110` | Empty literal "". |
| `S-cc9444` | String rendered as markup or code (innerHTML) | `filings.js:122` | Heights are arithmetic on counts the page computes itself. |
| `S-97d6a9` | String rendered as markup or code (innerHTML) | `filings.js:129` | `first` and `last` are numbers (`+years[0]`). |
| `S-989984` | String rendered as markup or code (innerHTML) | `filings.js:130` | Literal legend markup. |
| `S-b80216` | String rendered as markup or code (innerHTML) | `filings.js:149` | Empty literal "". |
| `S-3842a5` | String rendered as markup or code (innerHTML) | `filings.js:156` | The facet value goes through esc() (filings.js:29); `n` and the width are numbers. |
| `S-ca52ba` | String rendered as markup or code (innerHTML) | `filings.js:240` | Counts through toLocaleString() on numbers, and a literal button. |
| `S-6929fa` | String rendered as markup or code (innerHTML) | `filings.js:247` | card() and filingRow() run every data field through esc(): case, court, docket, claim, nature, filed, type, description, filer, date, entry. Archive.org links use the fixed https://archive.org prefix; CourtListener links are the fixed CL origin plus a path build/build_filings.py:56-59 keeps only whe |
| `S-ac1a56` | String rendered as markup or code (innerHTML) | `filings.js:276` | Counts are numbers (integers in data/filings_ia.json, which build/ia_recap.py computes), `ia.built` goes through esc(), IA is a constant, and the rest is literal. |
| `S-3d8735` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/courtlistener.py:43` | urlopen gets the SEARCH constant (https://www.courtlistener.com/api/rest/v4/search/, courtlistener.py:22) or the API's own `next` link. Suggested hardening, not required: check that `next` starts with SITE before following it, since get() adds the COURTLISTENER_TOKEN header to every request. |
| `S-c397f8` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/ia_recap.py:47` | Every caller builds the URL from the SEARCH constant https://archive.org/advancedsearch.php (ia_recap.py:39). |
| `S-8e3d80` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/recap_text.py:33` | The URL is `ia_text`, which build/recap_harvest.py:68 builds as f"{IA}/{item}/{name}_djvu.txt" from the https://archive.org constant. |
| `S-133762` | Audit url open for permitted schemes. Allowing use of file:/ or custom schemes is often unexpected. | `build/wayback_opinions.py:59` | The URL is the CDX constant https://web.archive.org/cdx/search/cdx (wayback_opinions.py:28) with urlencoded parameters. |

</details>

## Accessibility (WCAG 2.2 AA)

No open items.

<details><summary>Manual checklist (21 pass, 0 fail, 1 n/a)</summary>

| Item | Result | Note |
|---|---|---|
| 1.1.1 Non-text content | pass | The portrait has descriptive alt text. Each chart bar is a button or role=img element named with its year and counts; map tiles and year-view squares are named. The ▶ marker in filings summaries is read aloud as text; aria-hidden="true" on .turn would be tidier. |
| 1.3.1 Info and relationships | pass | One h1, h2 per section and year, h3 per card, h4 for press. Filter groups are role=group with aria-label or aria-labelledby to a heading. Lists are lists. |
| 1.3.2 Meaningful sequence | pass | DOM order matches reading order; the grid map is laid out with grid-row/column but read in TILES order, which is fine for a set of buttons. |
| 1.4.1 Use of color | pass | Year-view court types now have a shape as well as a colour (federal square, state round, tribunal hollow), in the squares and the key, and each square's name gives the type. Selected filters have an outline as well as colour; the stacked filings bars differ in lightness (about 3.4:1) and are labelle |
| 1.4.11 Non-text contrast | pass | Bars 3.29:1 (--bar) and 11.2:1 (--bar-on) on the pad; year squares 3.56 to 5.67:1; focus ring 7.23:1; search box border 6.8:1. Select borders (--line) are only 1.59:1, but the native arrow and text identify them. |
| 1.4.4 Resize text / 1.4.12 Text spacing | pass | Both pages at 640 px wide (200% of 1280) with the WCAG text-spacing overrides applied: no clipped text and no sideways scroll. At 320 px the page reflows; the two charts and the year view's months scroll inside their own containers. |
| 2.4.4 Link purpose | pass | "court PDF", "CourtListener", "Wayback Machine" and "document on archive.org" sit inside a card headed by the case name, which gives their purpose in context. |
| 2.4.6 Headings and labels | pass | Headings name their sections; selects are named "Court", "Phrase matched" and "Who filed it". |
| 3.1.1 Language of page | pass | lang="en" on both pages; content is English. |
| 2.1.1 Keyboard | pass | Every control is a native button, link, select, input or summary. Year-view hover text also appears on focus (focusin). |
| 2.1.2 No keyboard trap | pass | No modals or embedded players; focus moves freely. |
| 2.4.1 Bypass blocks | pass | No skip link, but main and nav landmarks are present. The footer sits inside main, so it is not a contentinfo landmark; moving it out would be tidier. |
| 2.4.3 Focus order | pass | Checked with the keyboard: after a year bar (both pages), a facet or a map tile, focus stays on the button; "clear filters" moves focus to the search box; when "Show more" reveals the last page, focus goes to the first new docket. |
| 2.4.7 Focus visible | pass | The global :focus-visible ring is a 2px accent outline (7.23:1). Selected buttons, which carry an ink outline, show an accent ring with a wider offset when focused; checked by tabbing to a selected map tile. |
| 2.4.11 Focus not obscured | pass | Nothing sticky or fixed. |
| 2.5.8 Target size | pass | Year-view squares are 14 px with centres 24 px apart in both directions; axe reports no target-size violations. Year bars are at least 10 px wide and 140 px tall, and scroll in their own container on narrow screens. |
| 2.2.2 Pause, stop, hide | pass | Nothing moves except a 1.5 s highlight on a card. |
| 3.2.2 On input | pass | Changing a select or typing filters the list in place; the URL is updated with replaceState, not navigation. |
| 3.3.2 Labels or instructions | pass | The search box has a visible <label>. The selects have no visible label, but each shows its purpose in its first option ("All courts", "Any phrase", "Filed by anyone"); a visible label would be clearer, especially once a phrase is selected. |
| 4.1.2 Name, role, value | pass | Toggle buttons expose aria-pressed in step with .on; filings dockets use native details/summary. |
| 4.1.3 Status messages | pass | #status and #searchcount are aria-live="polite" on both pages and announce result counts without moving focus. |
| 1.2.2 Captions | n/a | No audio or video. |

</details>

<details><summary>Cleared on review (5)</summary>

| Id | Item | Where | Why cleared |
|---|---|---|---|
| `A-6c64c1` | Elements must meet minimum color contrast ratio thresholds | `/ color-contrast` | The "gradient" is the pad's 1px rule lines (--rule #c3d6e4) every 32px over --bg #fcf3b8. Computed against both: ink 13.06:1 and 9.85:1, muted 6.16:1 and 4.64:1, accent 7.23:1 and 5.45:1. All at least 4.5:1. |
| `A-b78730` | Elements must have their visible text as part of their accessible name | `/ label-content-name-mismatch` | The year view's close button shows only "×", a symbol rather than text, and is named "Close 2021". 2.5.3 does not apply to symbolic characters. |
| `A-cae34d` | Elements must meet minimum color contrast ratio thresholds (dark mode) | `/ color-contrast (dark mode)` | Dark mode changes only the desk colours (--desk, --lamp, --binding, site.css:19-22); the pad keeps --bg and --rule, so the ratios are the same as in light mode: muted text 4.64:1 at worst. |
| `A-0d4c3c` | Elements must meet minimum color contrast ratio thresholds | `/filings.html color-contrast` | Same pad background and palette as the opinions page (site.css): muted text 4.64:1 at worst against the rule lines. |
| `A-66e24a` | Elements must meet minimum color contrast ratio thresholds (dark mode) | `/filings.html color-contrast (dark mode)` | Dark mode changes only the desk; the pad and its text colours are unchanged. |

</details>

## Fixed since the last run

- `A-176c0d` In the year view, court type is shown by colour alone
- `A-17ab2d` Elements must have their visible text as part of their accessible name
- `A-49888d` Page scrolls sideways at 320 px wide
- `A-752c97` Keyboard focus is lost to the top of the page after picking a year or a filings filter
- `A-a0fb70` A selected filter button looks the same with and without focus
- `A-c52fb3` All touch targets must be 24px large, or leave sufficient space
- `S-100ef3` String rendered as markup or code (innerHTML)
- `S-383608` Links built from data do not check the URL scheme
- `S-910db1` Every visit is reported to Google Fonts
- `S-9c46b9` Wayback timestamp reaches the page unescaped and unchecked

## Advisory (3)

Optional. These items never block a pass.

| Id | Check | Item | Where | Reference | Suggestion |
|---|---|---|---|---|---|
| `V-667718` | validity | Do not assign a `lambda` expression, use a `def` | `build/merge_sources.py:210` |  | Rewrite `count` as a `def` |
| `S-46b447` | security | No content-security-policy header | `https://internetarchivecanada.github.io/legal-opinions-using-wayback/` | A02:2025 · ASVS V3 | Set it; it limits the damage of any XSS that gets through; a <meta http-equiv> CSP works on static hosts. |
| `S-09212f` | security | No x-content-type-options header | `https://internetarchivecanada.github.io/legal-opinions-using-wayback/` | A02:2025 · ASVS V3 | Set it; it stops browsers guessing content types. It has no <meta> form, so on a host that cannot set headers (GitHub Pages) it stays open; the explorer's owners decide whether that matters enough to change host. |

<!-- explorer-checks:state {"passing": true, "date": "2026-11-05", "commit": "6de6f8c14448b0bc1fcd087dbd1c7d18d3057c2a", "open": [], "titles": {}} -->
