# Model routing

Each step has a planned model. Steps marked **helper** go to a subagent through the `Agent` tool with its `model` parameter set as below. The session (the model NIK chose) coordinates, talks to NIK, and checks every helper's output before anything goes into the report.

## The plan

| Step | Runs on | Why this model |
|---|---|---|
| Step 0: read the brief, pick the mode (case or incident), agree length and format | Session | A conversation with NIK |
| Issue spotting: parties, what each did, the legal issues, the facts each issue turns on | Helper, `opus` | Every later step depends on it, and a missed issue costs more marks than a thin one. The output is short |
| Status check for each law cited (in force, amended, repealed, proposed, with date) | Helpers, `haiku`, one per law, in parallel | Repetitive look-ups. Each returns the status, the date and a primary-source URL. The session compares the results with `references/malaysia-law-status.md` and sends anything that conflicts to a `sonnet` helper |
| Reading the judgment or the incident sources: facts, procedural history, coram, holdings, confirmed vs alleged | Helper, `sonnet` | Judgments are long and accuracy matters. A misread holding spoils every ILAC block |
| Comparator jurisdictions (one per country) for the Discussion table | Helpers, `sonnet`, in parallel | Foreign law has to be current and correctly stated, but each country is a separate job |
| Drafting the report: the ILAC blocks and the Discussion | Helper, `opus` | This is where the marks are: element-by-element application, analogy with precedent, the theory's fit and misfit, both sides of the critique. Write it in one pass so the Discussion links back to the ILAC findings |
| Citation check: each case, statute, article and news item exists and its details are right | Helpers, `haiku`, in batches of about 10, in parallel | Look-ups. Anything not found becomes "[citation to verify]", and is never guessed |
| APA 7 reference list and in-text citation format | Helper, `haiku` | Fixed rules |
| Final checklist review | Helper, `sonnet` | Fresh eyes on the draft against the checklist in SKILL.md. Returns a list of failures; the session fixes them or sends them back to the drafting helper |
| Delivery (Claude Docs or .docx) and the offer to save to the COM741 project | Session | Needs NIK's tools and answers |

Running the session on Sonnet is enough, because the heavy writing goes to an `opus` helper. A skill cannot change the session model, so say so once if NIK asks.

## Changing the plan

Follow the table by default. If NIK asks for a different model for a step, or for everything to run in the session, do that.

When a helper's output is clearly not good enough and a stronger model is the likely fix, ask before moving the step up (`haiku` to `sonnet`, or `sonnet` to `opus`). Examples: a status helper returning a date without a source, a judgment reader mixing up majority and dissent, or a citation helper "confirming" a case it could not find. Say which step, what went wrong and which model you propose, and wait for a yes. Never move a step to a weaker model without being asked.

## Handing work to a helper

A helper cannot see the conversation, so its prompt must carry:
- the mode, the case or incident, and NIK's brief (length, required headings, referencing style);
- the exact input: the issue list, the judgment URL or text, the laws to check, the citations to verify;
- the rules for that step from SKILL.md (for drafting: the whole of "Writing each ILAC part well", Step 3 and the style rules);
- the shape of the answer, for example one line per law: `law | status | date | source URL`.

Run independent helpers in parallel. If a helper fails or returns nothing, retry it once on the same model. If it fails again, do the step in the session and say so.

## Where there are no helpers

claude.ai on the web has no `Agent` tool. There, every step runs in the session on the model chosen in the chat's model menu, and the workflow is otherwise the same. Tell NIK once that per-step models only apply in the Claude desktop app, Claude Code and Cowork. For a full report on claude.ai, Opus is the better choice of chat model.
