# Instructions for agents working in this repository

**The data source is the Wayback Machine or an Internet Archive collection
whenever one holds the item; CourtListener is secondary.** Never link
CourtListener live where an Internet Archive copy has been found.

Read [METHODOLOGY.md](METHODOLOGY.md) before adding or changing any link,
data file or build script. It sets the order of sources (Internet Archive
first, CourtListener in support), the matching rules, and the traps already
found. Follow it; where it is silent, ask rather than guess, then add the
answer to it.

## Working rules

- **Branch from a freshly fetched `origin/main`**, in its own worktree when
  another session may be using the main checkout. Commit and push the branch,
  open a PR with `gh pr create --base main`, and do not merge unless told to.
- **Verify against the live service before writing a field name, URL pattern
  or count.** Report what it returned, including when it undercuts the plan.
- **Every new link is loaded and confirmed** to be what it claims before it is
  committed: the case named on the page, the right docket, the right date.
- **Record what could not be verified** in the data or the PR, never silently
  drop it and never link around it.
- **Never record an error as a negative.** A refused connection is not "not
  archived"; keep it as an error so a rerun retries it.
- **One Wayback Machine lookup at a time**, paced as METHODOLOGY.md says.
  Long runs go in the background and must resume from their cache.
- Run `python3 -m unittest discover -s tests` before every PR, and check both
  pages in a browser for changes to `app.js`, `filings.js` or the HTML.
- After a merge, check the live site once GitHub Pages has rebuilt, bypassing
  the browser cache.
- When you find a new trap, add it to METHODOLOGY.md in the same PR as the
  fix.
