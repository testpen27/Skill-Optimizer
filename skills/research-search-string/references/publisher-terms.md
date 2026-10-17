# Paywalled papers: who clicks Download

Papers without a free copy come through the user's own university access. Universities license that access on terms that usually forbid automated or systematic downloading, and publishers enforce it against the whole institution, not just one person. UC Davis Library's policy (read October 2026) is typical: providers "may take action when their monitoring systems suggest a breach", including "denying access to the entire campus", and it names "use of automation (robots, scraping, spiders, AI agents, etc.) to programmatically download content" and "downloading a large amount of content over a short period of time" as breaches. So the rule is: **the publisher's terms decide, and when in doubt the user clicks.**

## Publishers already checked

| Publisher | Platform | What the terms say | What to do |
|---|---|---|---|
| Elsevier | ScienceDirect (and Scopus) | "The use of automation is strictly prohibited" (Elsevier support page on blocked access, read October 2026); automated-looking activity is blocked at the firewall. | Open each article in a new tab and ask the user to click Download PDF. Never click it yourself. |

Add a row whenever you check another publisher, with the date and where you read it, so the next run does not repeat the check.

## Checking a publisher that is not in the table

Do this once per publisher per session, before touching any of its article pages:

1. Find the terms that cover the user's access: the site's terms of use or conditions of use page (usually linked in the footer), and any "text and data mining" policy. Fetch them with Firecrawl, or read them in the browser.
2. Look for wording about automated access: "automated", "robot", "spider", "crawler", "scraping", "systematic downloading", "bulk download", "text and data mining".
3. Decide:
   - **The terms explicitly allow an individual subscriber's automated downloading** (rare): you may click Download yourself, one paper at a time, waiting for each to finish, while the user watches. Stop at any bot check.
   - **The terms forbid it, or say nothing clear**: open each article in a new tab and ask the user to click Download.
   - **A text-and-data-mining clause that requires an API or a separate agreement** is not permission to download through the website: treat it as forbidden.
4. Tell the user what you found in one line, with the link to the terms.

## Handing a paper to the user

- Open the article page (the DOI link resolves to it) in a new tab of the browser pane.
- Tell the user which paper it is and ask them to click the PDF or Download button, and to say when it is saved.
- Find the new file (normally the newest PDF in their Downloads folder) and file it:
  ```
  python3 scripts/retrieve.py adopt "<folder>/manifest.json" --file "<path>" --doi <doi> --move
  ```
  The script rejects a file that is not a complete PDF, which catches a saved web page or an unfinished download.
- Go through the papers in a steady rhythm. Opening dozens of article pages in a burst looks like the automated pattern the terms forbid even when a person clicks.

## Never

- Sci-Hub, LibGen, Anna's Archive or any site that hosts copies without the publisher's permission.
- Getting past a paywall, a CAPTCHA or a "verify you are human" page.
- Using the user's credentials, cookies or proxy session from a script.
- Sharing downloaded paywalled PDFs beyond the user's own folder.
