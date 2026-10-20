# Running the searches in the browser

Use this when Step 3 runs the strings for hit counts. Load the `built-in-browser` skill (or `chrome-browser` for Claude in Chrome) before the first browser call; it covers opening the pane, sign-ins and site approvals.

## Ground rules

These keep the searches inside what an ordinary user does, because the databases' terms (and the user's university licence) are written against automated use.

- **The user watches.** Ask them to show the browser pane before you start, and say in the chat what you searched and what you read.
- **The user signs in.** Open the database page and ask the user to log in through their university (institutional login, OpenAthens, Shibboleth or the library proxy). Never type their credentials, and never sign out of or change an account.
- **One search at a time.** Wait for each results page to finish loading before the next search. Run only the strings in the log, at most about ten per database in a session; that is plenty for three tiers and two or three year ranges. This limit is a conservative choice of this skill, not a published threshold.
- **Stop at any bot check.** A CAPTCHA, "unusual traffic", "verify you are human", rate-limit or access-denied page means stop searching that database. Never solve, click through or work around it. Tell the user, ask them to finish that search themselves, and record their count with `"source": "user"`.
- **Read, never guess.** Record a count only when you can see the number on the page. If the page shows an error or no number, leave `"hits": null` with a note.
- **Do not export or download from the results page.** Exports are the user's to click (Step 5).

Scopus belongs to Elsevier, whose terms say "the use of automation is strictly prohibited". Running a few searches while the user watches is the arrangement the user chose for this skill; if they would rather stay strictly inside the terms, paste the string into the search box and let them press Search, then read the count.

## Scopus

1. Open `https://www.scopus.com/search/form.uri?display=advanced` (Advanced document search). If it shows a sign-in or "access through your institution" page, hand over to the user.
2. Clear the query box, paste the Scopus string from the log (it already has `TITLE-ABS-KEY` and the `PUBYEAR` limits), and run the search.
3. Read the number of documents found at the top of the results.
4. A syntax error message means the string needs fixing: run `node scripts/search_tool.js check "<string>" scopus`, fix the spec, rebuild the log row, and search again.

## Web of Science

1. Open `https://www.webofscience.com/wos/woscc/advanced-search` (Core Collection, Advanced Search). Sign-in as above.
2. Paste the Web of Science string (it has `TS=` and `PY=`) into the query builder box and search.
3. Read the number of results from the Core Collection at the top of the results.
4. Note the edition coverage if the page shows it (for example SSCI and ESCI only); it belongs in the report's note for that row.

## Google Scholar

1. Open the `url` from the log row; it already carries the string and the `as_ylo` / `as_yhi` year limits.
2. Read "About N results" and record it as the text shown (for example `"About 12,300"`), with the note that Scholar counts are approximate.
3. While on that page you may note the `[PDF]` links beside results for Step 6.
4. Google Scholar is the quickest to show a CAPTCHA. Run only the Scholar rows in the log, and stop at the first check.

## If there is no browser

Give the user each string and its URL in a numbered list, ask them to run them and reply with the counts in the same order, then record each with `"source": "user"`.
