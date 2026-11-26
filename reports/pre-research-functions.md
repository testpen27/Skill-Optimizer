# pre-research: what the skill does, in full

pre-research is for everything a researcher does before writing a literature review. You give it a topic, a title or a research question. It works out what you want, builds the search strings, runs them with you in Scopus and Web of Science, records the hit counts, helps you screen records, draws the PRISMA 2020 flow diagram, finds and downloads the papers, and writes a PDF report of all of it.

It does **not** build a Literature Review Matrix (LRM) or look up journal quartiles. Those were removed from this version; use your own LRM tool for them.

---

## 1. The big picture

```
 your request
      |
      v
 1. Understand it  ---- unsure? ask (max 3 questions, blocker first)
      |
      v
 2. Intake: ask only what this job needs
      |
      v
 3. Choose depth:   QUICK (15-20 papers)     or     SYSTEMATIC (database search)
      |                                                   |
      |                                    strings -> run in Scopus/WoS -> hit counts
      |                                    -> exports -> de-duplicate -> screening
      v                                                   v
 4. Branches you asked for:   Strings | PRISMA | Download papers
      |
      v
 5. Deliver: PDF search report + papers folder + what is still missing
```

Everything is kept in one project folder named after your topic (for example `pre-research/ott-adoption-malaysia/`), so each step feeds the next.

---

## 2. Step 1: it works out what you want before doing anything

Most failures in a skill like this come from doing the wrong job well, so the first thing it does is read your message for three things:

| It looks for | Examples |
|---|---|
| **The job** (and what you do *not* want) | strings, fix a string, PRISMA, download, quick search; "I don't want PRISMA" |
| **Every topic keyword, in your own words** | it will not drop a word from your title, merge two, or swap in a synonym at this stage |
| **Your limits** | years, "Scopus only", "no conference papers", language, "15 papers", where to save |

It then opens its first reply with **one line saying what it understood**, in your language, so a misreading is caught before it costs anything:

> *"You want Scopus-only strings for digital literacy, Orang Asli and children, 2019 to 2025, excluding conference papers, plus a Malay string."*

**What you state always beats the skill's defaults.** If you name databases, it builds only those. If you limit document types or languages, the strings carry that limit.

### When it stops and asks

It asks before working only when it is genuinely unsure, with the blocking question first, likely answers offered so a reply can be one word, and **never more than three questions**:

- the goal is unclear ("help me with my lit review");
- "PRISMA" could mean a full search, or only a flow diagram from counts you already have;
- a key term means different things in different fields ("engagement", "adoption") and no field is given;
- the topic is too broad to search ("AI", "social media");
- two instructions conflict ("2010 to 2015, but only the last five years");
- something you mention is missing (an attachment, an export, a string);
- part of the request is outside the skill (writing the chapter, formatting references, an LRM, journal quartiles). It says what is not covered, proposes what it can do instead, and asks only whether to go ahead with that.

When nothing is unclear it does not ask; it restates and starts.

---

## 3. Step 2: the intake (only the questions the job needs)

Anything your message already answers is filled in and shown to you, not asked again.

| Question | Why it matters |
|---|---|
| A. Field or discipline | Filters out same-word-different-discipline papers |
| B. Working title or research question | The source of the concepts |
| C. Population or context | Concept 3 |
| D. Niche (country, sector, platform) | Concept 4 |
| E. Year range(s) | Several are fine, e.g. 2016-2020 and 2021-2026. With no preference it suggests the last five calendar years and says which |
| F. Review type | Systematic, scoping, bibliometric, narrative, or proposal background |
| G. Databases you have | Scopus, Web of Science, or neither |
| H. What you want at the end | Only if unclear |
| I. Where to save | A folder you name, or Downloads (your own computer only) |

| You want | It asks |
|---|---|
| A pasted string checked or fixed | Nothing (only which database, if the string does not show it) |
| New search strings | A, B, C, D, E; G only if you want them run |
| A PRISMA search | A to G, and I |
| Papers downloaded from a list or export you have | I |

When you chain several jobs, it asks the union once at the start.

"Opus" is treated as Scopus without correcting you.

---

## 4. Step 3: quick or systematic

| | Quick | Systematic |
|---|---|---|
| Output | About 15 to 20 strong papers | Database strings run, hit counts, full exports, duplicates removed |
| Good for | A proposal, background reading | PRISMA, systematic or scoping reviews, anyone who asks for hit counts |
| Reaches | Open web and paper search (Firecrawl, Google Scholar, publisher sites) | Scopus and Web of Science through your own login |
| Limit | Cannot confirm a paper is indexed in Scopus or WoS | Needs your database access |

It tells you which one it chose.

---

## 5. The branches

### 5.1 Search strings

Builds database-ready Boolean strings for Scopus, Web of Science and Google Scholar, or fixes one you wrote.

- **Concepts**: usually 3 or 4 (subject, action/outcome, population/context, niche); a fifth if your title needs it. It will not drop part of your title to stay at four.
- **Terms**: 6 to 14 per concept, quoted phrases, truncation (`adopt*`), spelling variants (`behavio*r`), place and brand names when the niche is a country.
- **Tiers**: *broad* (subject and outcome), *balanced* (adds the niche or population), *narrow* (every concept).
- **Year ranges**: any number, each built with its own database's syntax.
- **Your limits are written into the strings**: databases, document types (include or exclude, e.g. no conference papers), languages.
- **Google Scholar**: two short hand-written strings (256 characters or fewer, no truncation).
- **Local language**: a separate string (for Malaysia, Malay), run as its own search and merged afterwards, never joined with AND.
- **Checker**: every string is linted (unbalanced brackets, curly quotes, lower-case `or` in Scholar, a missing operator before a field code, wildcards used wrongly, strings too long for Scholar).
- **Fixing your own string**: it runs the checker first, then fixes what is actually broken and tells you what it changed in one or two lines. It handles too many results, too few, shortening, and Scopus-string-in-WoS mix-ups.
- **Other databases** (PubMed, IEEE, ProQuest, EBSCO): it builds the concept table and Boolean skeleton and tells you to adapt the field tags, rather than inventing codes.

Output is easy to copy on a phone: one summary line, one code block per string, and what happens next.

### 5.2 Running the searches and recording hit counts

- **You watch**: you open the browser pane, sign in through your university, and Claude runs each Scopus and Web of Science string in Advanced Search while you look on.
- **You sign in**: Claude never types your credentials or changes your account.
- **One search at a time**, about ten per database per session at most.
- **Bot checks stop everything**: a CAPTCHA, "unusual traffic" or access-denied page means Claude stops that database and hands the search to you. It never tries to get past one.
- **It reads, never guesses**: a count is recorded only if Claude can see the number. Otherwise it stays blank.
- **Exports are yours to click**: Claude does not export or download from the results page.
- **No browser?** It gives you each string and URL in a numbered list and you reply with the counts.
- A free **OpenAlex cross-check** adds an approximate count per tier and year range, labelled as an approximation.

Every count is stored with where it came from (`browser`, `user`, or OpenAlex) and the date, and appears that way in the report.

Then you choose the search together: as a guide, 100 to 2,000 records in Scopus or WoS is workable; over that, use a narrower tier, under about 50, a broader one. The decision and your reason are logged.

### 5.3 PRISMA 2020

**You screen; Claude records.** Every include/exclude decision is yours. If you ask what Claude thinks of a record it can say so as an opinion, but it records only what you decide, and the report states that the screening was the reviewer's.

1. **Strings and searches** as above.
2. **Records**: you click Export in Scopus (CSV with DOI and abstract) and WoS (tab-delimited, full record). Claude merges the files and removes duplicates by DOI, then by title and year. With no Scopus or WoS access, OpenAlex supplies the records instead, with abstracts where it has them.
3. **Eligibility criteria**: asked before screening (population, concept, context, study design, language, publication type, years) and read back with each batch.
4. **Title-and-abstract screening**, two ways: in the chat (batches of 10 to 20, e.g. "include R001-R004, exclude R005 wrong population, maybe R006") or in a spreadsheet you fill in and load back.
5. **Full texts** of everything included or "maybe" are retrieved (see 5.4).
6. **Full-text screening**, the same two ways. A full-text exclusion needs a reason, and it suggests a short fixed list (wrong population, wrong outcome, wrong study design, not peer reviewed, full text not in English) so counts group cleanly. Every "maybe" is resolved before the final diagram.
7. **The numbers and the diagram**: filled from your recorded decisions; anything unfinished shows as "to be completed".

### 5.4 Access and download

- **Free copies first**: OpenAlex (which includes Unpaywall data) marks every DOI that has a legal open-access copy. For the rest, helpers search the web through Firecrawl for repository, preprint and author-page PDFs. If you ran Google Scholar yourself, the `[PDF]` links you saw are fair to collect; Claude never sends Firecrawl to Scholar.
- **Safe downloading**: obeys each site's `robots.txt`, waits between requests to the same site, accepts only http(s) links, and keeps a file only if it is a complete PDF (a landing page, a bot-check page or a truncated file is rejected). It asks before fetching more than 50.
- **Paywalled papers** come through *your* university access, and the publisher's terms decide who clicks:
  - **Elsevier / ScienceDirect** forbids automation, so Claude opens each article in a new tab and **you click Download**.
  - **Other publishers**: Claude reads their terms first (a helper quotes the clause), and clicks Download itself only where the terms clearly allow it. Otherwise you click.
  - Papers are handed to you at a steady pace, not in a burst of tabs.
  - Each downloaded file is filed into the folder and a manifest records it.
- **Never**: Sci-Hub, LibGen, Anna's Archive, ResearchGate or Academia.edu scraping, getting past a paywall or CAPTCHA, using your cookies or proxy session from a script, or sharing paywalled PDFs beyond your own folder.
- **At the end**: how many were downloaded, how many were fetched by you, how many are still missing (as a list with DOI links), and where the folder is.

### 5.5 The PDF search report

One PDF in your project folder:

1. Search profile (your intake answers)
2. Concepts and tiers
3. Every search string with its hit count, who read it and when
4. Eligibility criteria and an "other searches" table (Scholar, quick-search queries)
5. **PRISMA 2020 flow diagram** (identification, screening, eligibility, included)
6. Full-text retrieval list

A hit count nobody read stays "not recorded"; an unfinished screening box says "to be completed". The report never fills a gap with an estimate.

---

## 6. Where files go

- **Claude desktop app, Claude Code, Cowork**: it asks whether to use a folder you name or Downloads.
- **claude.ai on the web**: files go to the outputs folder and are shared with you; your browser saves them to Downloads.

Typical project folder:

| File | What it is |
|---|---|
| `spec.json` | Concepts, terms, ranges, limits |
| `search_log.json` | Every string, count, source, date, your decisions |
| `records.json` | The records after de-duplication, with screening decisions |
| `papers/` and `papers/manifest.json` | Downloaded PDFs and what happened to each record |
| `search_report.pdf` | The report |

---

## 7. Models, helpers and cost

Each step runs on a planned model. The plan is **fixed**: if you ask to change a step's model, it explains why and carries on. The one exception is moving a step **up** to a stronger model, and only after asking you.

| Step | Runs on |
|---|---|
| Intake, browser searches, screening | The session itself (you are in the loop) |
| Building the search strings | Helper on **opus** |
| Reading a publisher's terms | Helper on **sonnet** |
| Quick-search queries; finding free copies | Helpers on **haiku**, in parallel |
| Downloads, counts, PRISMA numbers, PDFs | Scripts, no model |

Helpers exist only where there is an `Agent` tool (desktop app, Claude Code, Cowork). On claude.ai web everything runs in the session on whichever model you chose; the workflow is otherwise identical.

---

## 8. The OpenAlex key

OpenAlex works without a key, but everyone on one network shares a small daily allowance. The first time a step needs OpenAlex, Claude asks once: paste a free key, or say no. Either answer is remembered.

- The key is stored in **your own config folder** (`~/.config/pre-research`, or `$PRE_RESEARCH_CONFIG_DIR`), never inside the skill, so **sharing the skill never shares your key**.
- The script refuses a config location inside the skill folder.
- The key file is readable only by you, and only its last 4 characters are ever shown.
- If the allowance runs out and you have no key, it mentions the free key once and carries on without OpenAlex.

---

## 9. Rules that hold everywhere

1. **Never invent a number.** No estimated hit counts, no guessed results.
2. **Screening decisions are the reviewer's.** Claude records; it never decides inclusion.
3. **Stop at bot checks.** Never get past a CAPTCHA, "unusual traffic" page or paywall.
4. **Respect publisher terms.** Elsevier: you click. Others: terms first.
5. **No pirate sources**, ever.
6. **Paraphrase, do not copy**, when summarising papers.
7. Your stated limits override the skill's defaults.

---

## 10. What it will not do

- Build a Literature Review Matrix, tabulate or classify papers, or look up journal quartiles (removed from this version).
- Write the review or the chapter, format citations, or summarise a single paper.
- Confirm that a quick-search paper is indexed in Scopus or WoS (that needs your login and the systematic search).
- Verify field tags for PubMed, IEEE, ProQuest or EBSCO.
- Run searches without you: database access is your university's, and the setup assumes you are watching.

---

## 11. Example requests

- "Give me Scopus and WoS strings for OTT adoption among Malaysian consumers, 2016 to 2020 and 2021 to 2026, plus a Malay string."
- "Scopus only, exclude conference papers: digital literacy, Orang Asli, children, 2019 to 2025."
- "This string gives zero results in Scopus" (pasted).
- "Cut this string to fit Google Scholar."
- "Run my strings in Scopus and tell me the hit counts."
- "Do a PRISMA search for telemedicine adoption among elderly patients in rural areas."
- "I only need the PRISMA diagram; I already have the counts."
- "Find 15 papers from the last five years on telework and burnout among nurses, no PRISMA."
- "Download the open-access papers from this list into my Downloads folder."
- "Here is my Scopus export; remove duplicates and let's screen."

---

## 12. What the skill is made of

| Piece | Job |
|---|---|
| `SKILL.md` | Understanding, intake, depth, branches, rules (about 100 lines, always loaded when the skill triggers) |
| `references/strings.md`, `syntax.md` | Building strings; syntax of each database |
| `references/systematic-search.md`, `browser-runs.md` | Running searches, recording counts, getting records |
| `references/prisma.md` | The PRISMA workflow |
| `references/quick-search.md` | The 15-to-20-paper route |
| `references/access-download.md`, `publisher-terms.md` | Free copies, paywalled papers, who clicks |
| `references/model-routing.md` | Which model does which step |
| `scripts/search_tool.js` | Builds and checks strings; makes the search log |
| `scripts/openalex.py` | Counts, record lists, export import, open-access lookup, key storage |
| `scripts/screening.py` | Records your decisions; computes PRISMA numbers |
| `scripts/retrieve.py` | Safe downloads and the manifest |
| `scripts/build_report.py` | The PDF report with the PRISMA diagram |

Only the files for the job you asked for are read, so a strings request never loads the PRISMA instructions.

---

## 13. How it was tested

Numbers are from this repository's test files and result folders.

- **Scripts**: 80 automated checks pass (string building and linting, OpenAlex parsing, screening and PRISMA arithmetic, safe downloading, report building, key storage).
- **Understanding test** (12 requests, including unclear goals, ambiguous terms, conflicting years, "no PRISMA", out-of-scope asks): 71 of 77 checks before the fix, 77 of 77 after.
- **Skill audit** (November 2026): three problems found and fixed (a `file://` link could copy a local file, a record with no authors crashed a download run, and the skill told Claude to edit its own files).
- **When to trigger**: see section 14 for the latest run after LRM was removed.

---

## 14. Change log: LRM removed

Removed: `references/lrm.md`, `scripts/build_lrm.py`, every LRM and quartile instruction in `SKILL.md`, the four LRM rows in the model plan, and the LRM tests (replaced with checks that every file the instructions name exists and that no reference file is orphaned). The description now lists "literature review matrices, synthesis matrices or RRL tables, journal quartile lookups or ranking" under **Not for**, so it will not claim those requests when another skill is better placed to handle them.
