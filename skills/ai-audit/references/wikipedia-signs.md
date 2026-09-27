# Wikipedia:Signs of AI Writing — Full Summary

**Source:** https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
**Type:** Advice page from WikiProject AI Cleanup — explicitly **not** a Wikipedia policy or guideline. Shortcuts: `WP:AISIGNS`, `WP:AITELLS`, `WP:LLMSIGNS`. "Wikipedia:AI writing" redirects here; the sibling page `Wikipedia:Signs of AI-generated comments` covers AI-written talk/discussion comments specifically.
**Basis for this document:** the full wikitext source of the article, supplied directly, retrieved 2026-09-11. This is now a complete structural pass over the article — every section and subsection is represented. Per copyright caution, the article's many real, multi-sentence **illustrative examples** (pulled from actual Wikipedia edit diffs, talk comments, and drafts) are described/paraphrased here rather than quoted at length; "words to watch" lists (short functional word lists, not prose) are reproduced directly since they're the essay's core reference tool.

---

## Lead / Purpose

The page is a field guide to detect **undisclosed AI-generated content on Wikipedia**, built from real examples pulled from articles, drafts, comments, and other content. It explicitly cautions that:

- Not all text with these signs is AI-generated — LLMs are trained on human writing (including Wikipedia itself), and many of the same patterns show up in editorials, blogs, and fan fiction.
- The list is **descriptive, not prescriptive** — it's observations, not house style rules (style rules belong in the Manual of Style, not here).
- **These are signs of a possible problem, not the problem itself.** Superficial issues (excess boldface, broken markup, citation quirks) can be easy to fix but may point to deeper, more serious policy risks (fabrication, undisclosed paid editing, etc.). The guide explicitly warns: don't just fix the surface signs and consider the matter closed — that can make the underlying problem *harder* to detect.
- Wikipedia's speedy-deletion criterion `G15` (LLM-generated pages without human review) covers only the most objective signs; the rest of what's on this page is **not sufficient on its own** for speedy deletion.

## Caveats

### AI detection tools (`WP:AIDETECTION`, `WP:AIDETECTOR`)
Don't rely solely on detectors like GPTZero or Pangram — they beat random chance but have real error rates, and are vulnerable to paraphrasing, formatting/spacing changes, and models they weren't trained to recognize. A detector flagging text as AI-written is explicitly **not** a valid reason for G15 speedy deletion.

### Your detection ability (`WP:AIDETECTIVE`)
Human judgment alone is unreliable too:
- One 2025 study found human ability to tell LLM text from human text was no better than chance.
- Another (on German theses) found ~57% recognition of AI text and ~64% of human text — barely better than a coin flip.
- A different 2025 preprint found *heavy LLM users* could correctly judge AI-vs-human authorship ~90% of the time, while light/non-users did only slightly better than chance — implying an expert flagging 10 pages will average roughly one false positive.
- Human writing itself is increasingly influenced by LLM style (shown in podcasts/spoken language as well as text), which will make the two harder to tell apart over time.
- Writers may also consciously adjust their style to avoid AI accusations.
- The page links to a self-test: `Wikipedia:AI or not quiz`.

---

## Content
*(Shortcuts: `WP:AIWTW`, `WP:AI-ISM`, `WP:LLMISM`)*

Framing: LLMs statistically "regress to the mean" — they favor the most statistically common phrasing/fact across many cases, so specific, unusual, nuanced details get smoothed into generic, positive-sounding descriptions (e.g., a specific historical achievement becomes a vague "revolutionary titan of industry"). This loss of specificity, paired with inflated generic praise, is a core detectable signature.

### Undue emphasis on significance, legacy, and broader trends (`WP:AILEGACY`, `WP:AITREND`)
> **Words to watch:** *stands/serves as, is a testament/reminder, a crucial/pivotal/vital/significant/key role/moment, underscores/highlights its importance/significance, reflects broader, symbolizing its ongoing/enduring/lasting, contributing to the, setting the stage for, marking/shaping the, represents/marks a shift, key turning point, evolving landscape, focal point, indelible mark, deeply rooted*

LLM text tends to puff up a subject's importance by tying mundane facts to broader trends/debates/legacies, sometimes with hedges that concede a topic is minor before insisting on its significance anyway. Illustrated with several real diffs (e.g., a statistics institute's founding described as "marking a pivotal moment"; a Cameroonian town's roads "solidifying its role as a regional hub"; an obituary-bot-style article on an AI "deadbot" service framed as "generating debate" and "shaping emerging policy discussions"; even an etymology note framed as reflecting "the enduring legacy" of a community). Also common in biology articles: over-emphasizing a species' connection to its ecosystem or belaboring vague/nonexistent conservation concerns.

### Canned emphasis on notability, attribution, and media coverage (`WP:OVERATTRIBUTION`, `WP:AIATTR`)
> **Words to watch:** *independent coverage, local/regional/national/[country] media outlets, music/business/tech outlets, trade publications, cited/featured/profiled in, written by a leading expert, active social media presence*

LLMs try to "prove" notability by cataloguing *what kind* of sources covered a subject rather than summarizing what the sources actually say — and often misattribute their own superficial analysis to the source itself. Distinct from ordinary press-release language because the focus lands on the sources' own characteristics (availability, classification) rather than the subject. Also flags LLMs echoing Wikipedia's own notability-guideline wording verbatim, and a stock claim that a subject "maintains an active social media presence" (rare on Wikipedia before ~2024). Several real examples are given, including one from a Wikipedia "Articles for Creation" help-desk comment stacking many notability buzzwords at once.

### Superficial analyses (`WP:SUPERFICIAL`)
> **Words to watch:** *highlighting/underscoring/emphasizing…, ensuring…, reflecting/symbolizing…, contributing to…, cultivating/fostering…, encompassing…, enhancing…, valuable insights, align/resonate with*

A tendency to tack a present-participle ("-ing") clause onto the end of sentences with vague third-party attribution, functioning as unattributed synthesis/opinion. Newer RAG-based chatbots may even attach these to a real named source ("Roger Ebert highlighted the lasting influence") regardless of whether that source said anything like it. Multiple real examples spanning 2023–2026 are given, including an AfC-help-desk comment showing a chatbot literally offering three ChatGPT-flavored rewrites of the same sentence.

### Promotional and advertisement-like language (`WP:AIPUFFERY`, `WP:AIPEACOCK`)
> **Words to watch:** *boasts a, vibrant, rich, profound, enhancing, showcasing, exemplifies, commitment to, natural beauty, nestled, in the heart of, groundbreaking, renowned, featuring, diverse array*

LLMs struggle to hold a neutral tone even when prompted to — output skews toward travel-guide or ad copy. Can occur even without deliberate promotional intent, and even while an edit summary claims to have *removed* promotional tone. Older LLMs (GPT‑4-era) are more bluntly superlative; newer ones are more subtly positive and avoid phrases like "the best." Two named sub-patterns: (1) "cultural heritage" framing that constantly reminds the reader of a place's importance (e.g., "nestled... vibrant town with a rich cultural heritage"); (2) press-release/commercial tone for people or companies (e.g., a CEO quote "emphasizing the airline's commitment to sustainability").

### Vague attributions and overgeneralization of opinions (`WP:AIWEASEL`)
> **Words to watch:** *industry reports, observers have cited, experts argue, some critics argue, several sources/publications* (when only a few are cited), *such as* (before a list implied to be non-exhaustive)

Classic weasel-wording: attributing opinions to vague, uncounted authorities, or exaggerating how many sources back a claim (e.g., "researchers and conservationists," "described in scholarship," "toy industry publications" backed by only one or two citations).

### Outline-like conclusions about challenges and future prospects (`WP:FACESCHALLENGES`)
> **Words to watch:** *Despite its... faces several challenges..., Despite these challenges, Challenges and Legacy, Future Outlook*

A rigid formula: articles get a "Challenges" (or "Challenges and Future Directions") section opening with "Despite its [positive traits], [subject] faces challenges..." and closing with either a vaguely upbeat assessment or speculation about future initiatives — often paired with a separate "Future Prospects" section. The essay stresses this sign is about the **rigid template**, not merely discussing real challenges. Many real examples spanning 2023–2026 are cited (economic-law, energy, transit, and even a Spanish-fashion-industry draft), all following essentially the same shape.

### Leads treating Wikipedia lists or broad article titles as proper nouns
When an article's title isn't a proper name (e.g., a list article), AI-written leads sometimes define the title itself as though it were a standalone real-world entity ("**Catchment area (health)** refers to...", "**EuroGames editions** is the chronological list..."), in a way the Manual of Style permits only when done more naturally than these examples are.

### "Awards and recognition" section
Section headers in the generic "X and Y" pattern are common in AI-generated articles, and "Awards and recognition" (or just "Recognition") is called out as a near-ubiquitous specific instance, tied to the broader tendency to vaguely allude to "coverage" of a subject.

---

## Language and grammar

Framing: AI text shows consistent syntax/word-choice/sentence-construction patterns regardless of topic, giving it an identifiable "voice." Some models (e.g., GPT‑4o) deviate from human writing more than others.

### High density of "AI vocabulary" words (`WP:AIVOCAB`, `WP:AIWORDS`)
> **Words to watch:** *Additionally* (esp. sentence-initial), *align with, boasts* (meaning "has")*, bolstered, crucial, deep dive, delve, emphasizing, enduring, enhance, fostering, garner, highlight* (as a verb)*, interplay, intricate/intricacies, key* (adjective)*, landscape* (abstract noun)*, meticulous/meticulously, pivotal, robust, showcase, tapestry* (abstract noun)*, testament, underscore* (as a verb)*, valuable, vibrant*

Multiple studies show LLMs overuse specific words, a pattern that surged after 2022; these words tend to co-occur (find one, expect others). One or two appearing in an edit may be coincidence — many, repeatedly, in a post-2022 edit is one of the **strongest tells**. The overused set shifts by era:
- **2023–mid-2024 (GPT‑4):** *Additionally, boasts, bolstered, crucial, delve, emphasizing, enduring, garner, intricate/intricacies, interplay, key, landscape, meticulous/meticulously, pivotal, underscore, tapestry, testament, valuable, vibrant*
- **Mid-2024–mid-2025 (GPT‑4o):** *align with, bolstered, crucial, emphasizing, enhance, enduring, fostering, highlighting, pivotal, showcasing, underscore, vibrant*
- **Mid-2025 on (GPT‑5):** *emphasizing, enhance, highlighting, showcasing*, plus notability/attribution-related words (see above)

Notably, *delve* was the famous 2023–early-2024 ChatGPT tell, then dropped off sharply through 2025. Grok is idiosyncratic, favoring pseudo-scientific words (*causal, empirical, correlate*) and still overusing *underscore* as of 2026. The essay cautions this is about literal overused words, not their synonyms, and that context matters (e.g., "underscore" can be a literal underline or refer to incidental music).

### Avoidance of basic copulatives ("is"/"are" phrases) (`WP:AINOCOPULA`, `WP:AIREPRESENTS`)
> **Words to watch:** *serves as/stands as/marks/functions as/operates as/represents [a], boasts/features/maintains/offers [a], refers to*

LLMs replace simple "is"/"are" constructions with fancier verbs (*serves as a* instead of *is a*), and prefer marketing verbs (*features, offers*) over neutral *has*. One study found a >10% drop in "is"/"are" usage in academic writing starting in 2023; a similar decline is seen on Wikipedia (controlling for lead-sentence structure). In lead sentences specifically, LLMs may write "refers to" as though the article were about the *term* rather than the subject itself.

### Vague expression of connection or association (`WP:AICONNECT`, `WP:AIASSOCIATION`)
> **Words to watch:** *in connection with/to..., connected with/to, in association with..., associated with*

Instead of directly stating a relationship ("X was CEO of Y"), LLMs allude vaguely to two things being "associated" or "connected," often stacked with promotional buzzwords. Flagged as only meaningful in combination with other signs, not alone.

### Negative parallelisms (`WP:AIPARALLEL`)
When describing a subject, LLM output often reads as though correcting a misconception, contrasting one trait against another. Three named variants, each with several real illustrative diffs:
- **"Not just X, but also Y"** — "not only... but...", "it's not just..., it's...". 
- **"Not X, but Y"** — a stronger form flatly denying the first trait: "it's not..., it's...", "no..., no..., just...".
- **"Y rather than X"** — the same contrast reversed; called out as particularly common in **Grok** output (illustrated with a Grokipedia-sourced edit).

Also noted as common in AI-written *talk page/AfD comments*, not just articles.

### Rule of three (`WP:RO3`)
LLMs overuse tricolon structures ("adjective, adjective, adjective" or "phrase, phrase, and phrase"), often to make superficial analysis look more thorough. Flagged as a stronger signal in contexts where humans rarely bother with such flourishes (e.g., edit summaries). Illustrated with a real "canned-format" Markdown-style list from an edit to an article about rotary saws.

---

## Style

### Title heading
AI chatbots sometimes prepend a heading repeating the article's own title before the content — since they don't picture that a page title is already displayed automatically.

### Title case (`WP:AITITLECASE`)
AI strongly tends to capitalize all main words in section headings (Title Case), contrary to Wikipedia's sentence-case convention.

### Headings only containing other headings
AI sometimes generates a heading whose only content is more (sub)headings, with no actual prose under it.

### Overuse of boldface (`WP:AIBOLD`)
Bolds phrases excessively and mechanically — inherited from readmes, listicles, and sales decks — sometimes bolding every instance of a repeated key term in a "key takeaways" style. (Some newer models are now instructed to avoid this.)

### Inline-header vertical lists (`WP:AILIST`)
A distinctive list format: a bullet/number marker followed by an inline **bolded header**, then a colon, then descriptive text. Bullets may render as a literal •, -, –, #, or emoji character instead of proper wikitext list markup; numbered lists may use literal "1." instead of wikitext numbering. Copy-pasted plain text can also lose line breaks. Multiple real examples given (AfD comments, an article on a Cold-War-era weapon project, an SEO-terminology draft), including one where the boldfaced items had no separating punctuation at all.

### Overuse of em dashes (`WP:AIDASH`)
*(The article itself flags this sign as possibly outdated as of Sept. 2026, pending newer examples.)* LLM output uses em dashes more than typical human writing of the same genre, often in a formulaic "punched up" way, and typically with spaces around the dash (unlike common human typographic convention). Explicitly a **weak signal alone** — more useful combined with other signs, and more common in discussion/talk pages than articles. Some companies (notably OpenAI's GPT‑5.1) have tuned newer models to suppress em-dash overuse. A July 2026 study found only Claude, among contemporary models, used em dashes *more* than professional human writers; ChatGPT used them less by then.

### Emoji as formatting (`WP:AIEMOJI`)
Chatbots have decorated headings/bullets with emoji, especially in talk comments and edit summaries — less common now but still seen. Real examples include an emoji-heavy user page and a village-pump comment structured entirely around emoji-labeled sections (🧠, 🧱, 🚨, 🧭).

### Unusual use of tables (`WP:AITABLE`)
AI sometimes generates small, thin wikitables that would read better as prose or an infobox — e.g., a two-column "market statistics" table, or comparison tables of cultural artifacts. Occasionally raw Markdown table syntax leaks into a wikitable, rendering as a garbled mess.

### Curly quotation marks and apostrophes (`WP:AICURLY`)
ChatGPT and DeepSeek typically output curly quotes (" " / ' ') and curly apostrophes instead of straight ones, sometimes inconsistently mixed within one response. Explicitly **not proof by itself** — curly quotes/apostrophes are standard in Chicago Manual of Style-edited prose, are auto-applied by Microsoft Word's "smart quotes," macOS/iOS system-wide, and by tools like LanguageTool and the Citer citation tool (which can carry a curly quote in from a page's title). Also, some Wikipedia custom fonts render curly and straight apostrophes identically, and — notably — Gemini and Claude models typically do *not* use curly quotes.

### Skipping heading levels
AI tends to skip level-2 (`==`) headings and start straight at level-3 (`===`), which goes against Wikipedia's accessibility/style conventions — making it very unlikely for manually-formatted human content to do this.

### Overuse of level 1 headings
Level-1 headings (`=`) are rare on Wikipedia (normally reserved for the MediaWiki-generated article title) — AI sometimes uses them throughout an article, likely from mistranslating Markdown's `#` top-level heading syntax.

### Thematic breaks between sections
AI sometimes inserts a Markdown-style horizontal rule (`----`) between sections — a Markdown convention with no real Wikipedia equivalent use case.

---

## Communication intended for the user

### Collaborative communication (`WP:CERTAINLY`, `WP:COLLABCOMM`)
> **Words to watch:** *I hope this helps, Of course!, Certainly!, You're absolutely right!, Would you like..., is there anything else, let me know, more detailed breakdown, here is a*

Text meant as chatbot-to-user correspondence (advice, prewriting, meta-commentary) gets left in article text or comments instead of being replaced with actual content — sometimes explicitly mentioning that the output is meant "for Wikipedia" or citing policies by name in an oddly self-aware way, and the advice given is often wrong or non-compliant. Many real examples: a "background information" boilerplate paragraph left in an article; a chatbot literally advising an editor how to word a controversial section "neutrally"; a "here's a template for your wiki user page" message left on a user page; leftover HTML-comment instructions to a human editor about how to submit a draft and disclose a conflict of interest; and the "before creating a real Wikipedia page" YouTuber-notability checklist mentioned in earlier passes of this document.

### Knowledge-cutoff disclaimers and speculation about gaps in sources (`WP:AICUTOFF`, `WP:AIDISCLAIMER`)
> **Words to watch:** *Up to my last training update, as of my last knowledge update, While specific details are limited/scarce..., not widely available/documented/disclosed, ...in the provided/available sources / search results..., based on available information*

Older, fixed-cutoff models (GPT‑3.5/GPT‑4) explicitly disclaimed that their answer might be outdated. Newer RAG-based chatbots produce a similar-sounding disclaimer when they simply fail to find sources, sometimes paired with speculation about what the missing information "likely" is — which the essay stresses is **entirely speculative** (even the claim that something is "undocumented" is itself unverified) and may be fabricated. When the missing info is about a person's private life, models often speculate they "maintain a low profile" — also unverified. Real examples span a 2023 article that literally states a January-2022 knowledge cutoff, through 2026 drafts speculating about an "underground" artist's undocumented lyrics.

### Phrasal templates and placeholder text (`WP:AIPLACEHOLDER`)
Chatbots generate Mad-Libs-style fill-in-the-blank templates for the user to complete, and users sometimes forget to fill them in — leaving bracketed placeholders like `[Describe the specific section...]` or `[Your Name]` in live content. Also covers: placeholder dates like `2025-XX-XX` left in citation `access-date` fields; other placeholder citation fields (`INSERT_SOURCE_URL_30`, `PASTE_SPOTIFY_TRACK_URL_HERE`); and placeholder HTML comments in infobox fields suggesting information be added later ("Add if available with citation"). The essay cautions to first check whether a template comment is actually a *predefined* infobox-template boilerplate (e.g., "Add spouse if reliably sourced" in `Infobox military person`) before treating it as an AI tell.

---

## Markup

### Use of Markdown (`WP:MARKDOWN`, `WP:AIMARKDOWN`)
Wikitext is a niche markup language mostly unknown outside Wikipedia/MediaWiki; chatbots default to Markdown instead (their much more common training/output format), because their system prompts often explicitly instruct Markdown formatting (the essay quotes Anthropic's own November 2024 Claude Sonnet 3.5 system-prompt language about Markdown conventions as an example). Markdown syntax conflicts with wikitext throughout: asterisks/underscores instead of single-quote bold/italic markup, `#` instead of `==` for headings, `()` instead of `[]` around links, and `---`/`***`/`___` instead of `----` for horizontal rules. When asked to "generate an article," chatbots often output raw Markdown by default; if asked to convert to wikitext, the result is often broken, and may get wrapped in a Markdown fenced code block (triple backticks, e.g. `` ```wikitext ``) that a user can copy-paste along with the actual content, leaving stray backtick markers in the final page. A dedicated sub-page, `Wikipedia:Signs of AI writing/Wikitext wrapped in Markdown code blocks from chatbots`, documents this specific footprint further. LLMs also sometimes render `##` literally in output, which MediaWiki misinterprets as a numbered list rather than a heading. The essay is explicit that Markdown **alone** is a weak signal — it's common among developers, researchers, and users of Reddit/Discord/Slack/Obsidian/GitHub, all of which use Markdown natively.

### Broken wikitext
Because chatbots aren't fluent in wikitext/templates, they can produce badly garbled syntax — illustrated with a real, severely mangled `AfC submission` category tag full of duplicated date/timestamp text, apparently from an editor asking a chatbot how to submit a draft.

### Internal formatting and reference markup bugs (`WP:OAICITE`)
Chatbot-internal citation/formatting codes sometimes leak into pasted text — an unambiguous AI tell, with per-tool signatures:
- **ChatGPT:** `:contentReference[oaicite:N]{index=N}`, `citeturn0search0`-style markers (increasing index numbers, sometimes hidden inside Unicode Private Use Area characters), `iturn0image0` for image sets, and `({"attribution":{"attributableIndex":"X-Y"}})` JSON fragments.
- **Gemini:** `[cite: 1]` / `[cite: 3, 12, 13]` style markers, and `[span_N](start_span)` / `(end_span)` bug markers (`WP:STARTSPAN`).
- **Grok:** `<grok-card data-id="...">` XML-style tags, and `grok_render_citation_card_json` blocks.
- **DeepSeek:** lenticular-bracket/dagger markup like `【85†L261-269】`.
- **Perplexity:** `[attached_file:1]` / `[web:1]` tags, and Amazon-S3 URLs containing `ppl-ai-file-upload`.
- **Unclassified (as of June 2026):** `:::writing{variant="document" id="NNNNN"}` markers (also seen in non-English form, e.g. `écriture{variante=...}`), sometimes bilingual.

Each has real illustrative diffs, and the page includes ready-made Wikipedia search links for patrollers to find live occurrences of most of these.

### Non-existent or out-of-place categories (`WP:AIREDCAT`)
LLMs hallucinate plausible-sounding but nonexistent categories (they show up as red links), or use obsolete/renamed ones from their training cutoff. Not proof alone (humans make similar mistakes), but corroborating evidence alongside other signs. Example: `[[Category:American hip hop musicians]]` (missing the hyphen used in the real category name).

### Non-existent templates
Similarly, LLMs hallucinate plausible infobox/template names and parameters (e.g., an invented `{{Infobox ancient population}}` template where a real editor would have used `{{Infobox archaeological culture}}`), which render as red links or silently do nothing.

---

## Citations
*(See also: `Wikipedia:Fictitious references`, `Template:Failed verification`)*

### Broken external links
Several dead links (404s, nonexistent sites) in a new article/draft — especially ones absent from the Internet Archive — strongly suggest AI generation, since it's unlikely such a link was ever real. Caution: some broken links are innocent (accessible only via institutional proxies, mangled by bots, or truncated by human copy-paste).

### Invalid DOI and ISBNs
Invalid ISBN checksums (flagged automatically by citation templates) and unresolvable DOIs can indicate hallucinated references.

### DOIs that lead to unrelated articles
LLMs can generate references with real-*looking* DOIs that actually resolve to unrelated papers. Illustrated with a fabricated pair of "Proceedings of the IEEE" citations about Ohm's Law (paraphrased, not quoted) — one falsely attributed to an author who had been dead 30+ years at the claimed publication date, the other pointing to an issue with no matching article. Caution: a similar-looking but unrelated 2018–2023 VisualEditor bug caused *human* editors to accidentally insert low-numbered PubMed citations (e.g., a rat-liver study cited in a Disney-films list) — these resemble AI hallucinations but generally aren't.

### Book citations without page numbers or URLs
Two patterns (each with a paraphrased fabricated example in the source): (1) a page-less citation to a real, plausible book, unverifiable as a result; (2) a citation *with* a page number to a real, findable book, where searching the actual text for a key term from the prose (e.g., a named philosopher) turns up nothing — a stronger tell when the book is well-known/frequently cited and the citation lacks a URL, since human editors citing books often link an online copy.

### Incorrect or unconventional use of references (`WP:AICITESTYLE`)
Covers various malformed reference reuse: e.g., an early AI tool correctly finding one real source but citing it via a broken/irrelevant PubMed-style reused-reference syntax; and chatbots using a `↩` return-arrow character around footnotes (a web-article convention, not a wikitext one) — including one draft literally leaving in the chatbot's own "Would you like help formatting and submitting this...?" line under a "References" heading.

### `utm_source=` tracking parameters
ChatGPT may leave `utm_source=openai` or `utm_source=chatgpt.com` in cited URLs; Microsoft Copilot leaves `utm_source=copilot.com`; Grok leaves `referrer=grok.com`. Gemini/Claude do this far less often. Flagged as **near-definitive proof of that specific tool's involvement** in finding the source (Google very rarely indexes pages that still carry this parameter) — though not proof the *prose itself* was AI-written, since some editors use AI only to find citations for otherwise human-written text (checkable via edit history).

### Named references declared but unused in the article body
A common LLM referencing bug: `<ref name="x">...</ref>` entries listed inside a `<references>` block that are never actually cited inline in the prose, producing a visible Wikipedia "Cite error" — illustrated with two real broken drafts.

---

## Comment-specific indicators (`WP:AICOMMENT`)
*(Full detail lives on the sibling page `Wikipedia:Signs of AI-generated comments`; this section is a summary pointer.)* Beyond article-writing tells, editors pasting AI-generated *comments* tend to also: misquote policies or cite made-up shortcut codes; transclude maintenance banners just for mentioning them; write long comments broken into Markdown/heading-divided sections; downplay AI use by insisting they "put in the effort" to follow policy or that the words reflect their own thoughts; ask critics for specific feedback on what to fix; dismiss AI-origin concerns as unsubstantiated speculation; and redirect criticism toward "focus on the content, not its origin."

---

## Edit summaries (`WP:AISUMMARY`)

AI-generated edit summaries follow rigid templates uncommon before 2023; if the summary looks AI-generated, the edit itself likely is too (unlikely someone would bother with AI just for a one-line summary). The more a summary deviates from the pattern — even if long/formal — the *less* likely it's AI. Common abbreviations like "ce" (copy edit) are not signs. Older AI summaries (first-person, vocabulary/emoji/list-formatting tells) have given way to newer ones that are more exhaustively procedural about policy compliance.

- **General examples:** several real summaries spanning 2023–2026, including one bizarre case where a leftover Claude conversational reply ("That last sentence is the killer...") got pasted directly into the edit-summary field.
- **Canned assurance of adherence to policies/guidelines:**
  > **Words to watch:** *ensured that… adheres to, refined, enhanced, enriched, streamlined, improved, in compliance/complies with, Wikipedia [guidelines/style/standards], revised, verifiability, neutrality, neutral tone, encyclopedic tone, clarity, flow*
  Human editors citing a specific MoS violation do so briefly with a direct link (e.g., "removed excessive links per MOS:OVERLINK"); AI summaries tend to be verbose yet vague, stacking many generic "improvements" a human is unlikely to bundle into one edit.
- **"Preserved"/"retained"/"avoided" procedural language:**
  > **Words to watch:** *preserved/preserving, retained/retaining, avoided/avoiding, ensured/ensuring, aimed/aiming to*
  Unusual for a human summary to describe what *wasn't* changed — but expected from an AI prompted to edit X and Y while specifically preserving Z.
- **Overemphasis on presence/reliability of citations:**
  > **Words to watch:** *added sourced [information/content/infobox/section], added verified [...], added [coverage/citations/references], improved attribution, with [independent/secondary/third-party/peer-reviewed] sources*
  Mirrors the article-level notability-attribution sign — vaguely touting that sourcing was added/improved rather than describing the actual content change.
- **Overemphasis on parameter/template names and markup idiosyncrasies:** itemizing exact infobox/template parameter names and raw markup syntax — a level of granular detail unlikely from an unfamiliar human editor.
- **Reference to AfC review:** explicitly stating an edit addresses reviewer feedback — a fact so obvious a human usually wouldn't bother stating it.

---

## Miscellaneous

- **Pronounced shift in writing style:** a sudden jump to flawless grammar unlike an editor's other writing (especially if the older writing predates Nov 2022) suggests AI use; consistent style across pre- and post-2022 edits argues against it. A related sub-sign: **mismatched English variety** — e.g., an editor geographically tied to Indian English suddenly writing in American English, since many LLMs default to American English. (Caveat: non-native speakers naturally mix varieties too, and long-term AI users' output style tends to track whatever contemporaneous AI models produce.)
- **"Submission statements" in AfC drafts:** some LLMs insert a "reviewer note" inside a draft explaining why the subject is notable — which paradoxically signals to reviewers that the draft is AI-generated and should likely be declined/deleted without much further consideration.
- **Pre-placed maintenance templates (`WP:AIDECLINE`):** a draft arriving with an AfC-decline template already set to "declined" with no actual review reasoning (the LLM apparently added the decline template itself), or with implausible maintenance/protection templates already present.
- **Canned user pages (`WP:AIUSERPAGE`):** formulaic AI-generated user pages with headers like "About Me," "My Interests," "Let's Connect!," heavy on emoji and (attempted) Markdown bold — the Markdown-bold-that-didn't-render is called the strongest single tell here.
- **Permissions gaming:** AI's ability to churn out plausible-looking edits quickly makes it a common tool for building up edit count to unlock higher user-access levels before pursuing spam/vandalism — but rapid AI-assisted editing alone is *not* itself evidence of this, only when combined with other gaming indicators.
- **Differences between LLMs:** each model has an idiolect; e.g., ChatGPT/Grok lean more into "broader context" framing than Gemini/Claude, and Gemini/Claude responses tend to be more concise (Grokipedia articles are cited as notably long by contrast). ChatGPT is likely the most-used tool for Wikipedia edits specifically.
- **Biases in content — pro-authoritarian bias:** even major US frontier models show a measurable pro-authoritarian lean on some prompts (partly from training on state media/propaganda without exclusion, partly cited "user safety" reasoning in authoritarian countries); this is more pronounced in Chinese-language responses, and models are more willing to criticize governments in freer countries than repressive ones.

---

## Signs of human writing

- **Age relative to ChatGPT's launch (Nov 30, 2022):** text added before that date can have AI use safely ruled out (tools like "Who Wrote That?" or WikiBlame can date when specific text was inserted).
- **Ability to explain one's own editorial choices:** a human who made a real mistake (e.g., a bad URL) can usually explain how it happened; inability to account for an error is more suspicious.
- **Syntax:** AI defaults to a stiffly "formal, neutral, encyclopedic" register and avoids certain constructions that are common — and sometimes Manual-of-Style-preferred — in human Wikipedia writing, based on ~25 years of observed editing patterns:
  - Simple *is*/*has* phrasing ("there is a," "it has a")
  - Plain synonyms over stiffer/euphemistic ones (*wrote* vs. *authored*, *moved* vs. *relocated*, *used* vs. *utilized*, *died* vs. *passed away*)
  - Superlative/definitive claims ("one of the best," "was the first")
  - Hedging qualifiers/intensifiers ("very," "perhaps," "tends to")
  - Wordy filler constructions ("as a result of," "in order to," "the fact that")

---

## Ineffective indicators

Explicitly listed as **unreliable or even backwards** signals — false AI accusations can drive off new editors, so the essay warns against confirmation bias here:
- **Perfect grammar** — plenty of human editors are skilled/professional writers.
- **Mixed casual/formal or "clinical + emotional" register** — can reflect a technical-field writer, youth, playfulness, neurodivergence, or just multiple human editors on one page.
- **"Bland"/"robotic" prose** — AI's actual traits (detailed above) don't always read as "robotic" to people unfamiliar with them.
- **"Fancy"/academic/formal prose generally** — AI overuses *specific* words, not formality as a whole.
- **Transition words in isolation** (*Additionally, Consequently, Notably*) — only a few such words are actually AI-associated, and the pattern has plenty of precedent in ordinary human essay-writing.
- **Unsourced content** — over 570,000 Wikipedia articles are tagged as needing citations, mostly pre-dating LLMs; meanwhile modern AI chatbots often *do* add citations (just not necessarily accurate ones).
- **Bizarre wikitext** — most AI wikitext bugs are covered elsewhere on the page; other "random" glitches (like stray `<span>` tags) more often trace to browser-extension bugs or a known Wikipedia content-translation-tool defect, or to VisualEditor mistakes.
- **Correct wikitext** — normal for anyone using the visual editor or checking the preview button, even for complex templates.

---

## Historical indicators
*(Common in older AI models, rarer now — still useful for finding older undetected AI content.)*

- **Didactic disclaimers (Nov 2022–2024):** stock "it's important to note..." / "worth noting" hedges about safety or jurisdictional variation — appeared in OpenAI's own GPT-4 system card as example "partial refusals."
  > Words to watch: *it's important/critical/crucial to note/remember/consider, worth noting, may vary*
- **Section summaries:** older LLMs writing long output often added a "Conclusion" section or restated the core point at the end of paragraphs.
  > Words to watch: *In summary, In conclusion, Overall*
- **Prompt refusal:** older chatbots sometimes declined a request outright with an apology and an "as an AI language model" disclaimer before offering an alternative — now increasingly rare.
- **Abrupt cut-offs:** older tools (notably ChatGPT) would stop mid-generation after a token limit, requiring the user to click "continue" — though this can also result from a malformed copy-paste, or indicate a copyright violation rather than AI use.
- **Outdated `access-date` parameters:** citations with an access-date suspiciously older than the edit itself — though newer chatbots rarely make this mistake, and legitimate old access-dates do occur (copied citations, batch merges).
- **Lexical diversity / elegant variation (`WP:AIELEVAR`):** older models' repetition penalty caused them to avoid reusing the same word, producing distractingly varied synonyms for one referent across a passage — observed both pre/post-2023 on Wikipedia broadly and in GPT-4o-mini/Gemini-1.5-Flash-generated comparison text. Caveat: some non-native English speakers (the essay notes Italian-schooled writers as an example) are also taught to avoid word repetition, independent of AI use.

---

## See also / References (as listed on the page)
- `Template:Looks AI-generated`
- `Wikipedia:Artificial intelligence resources`
- `Wikipedia:Artificial intelligence`
- Further reading: Sam Kriss, *"Why Does A.I. Write Like … That?"*, The New York Times Magazine (Dec 3, 2025)
- External links: *CanYouPasstheTuringTest.com*; *Tropes – AI Writing Pattern Directory*

The article cites a substantial body of external research throughout (Juzek & Ward 2025 on "delve"; Kobak et al. 2025, *Science Advances*, on excess vocabulary in biomedical writing; Reinhart et al. 2025, *PNAS*, on grammatical/rhetorical style variation; Russell, Karpinska & Iyyer 2025, ACL, on human detection accuracy; Geng & Trotta on "is/are" decline and human-LLM co-evolution; Huang et al. on Wikipedia-specific LLM impact; a 2026 Economist study on em-dash usage by model; among others) — all inline-cited in the original wikitext.
