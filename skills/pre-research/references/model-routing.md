# Model routing

Each step runs on a planned model. Steps marked **helper** go to a subagent through the `Agent` tool with the `model` parameter set as below; the session (the model the user chose in Claude) coordinates, talks to the user, and checks every helper's output before anything is saved or shown as final.

## The plan

| Step | Runs on | Why this model |
|---|---|---|
| Intake questions | Session | A dialogue with the user |
| Building the search strings (concepts, synonyms, tiers, Scholar and local-language strings) | Helper, `opus` | Everything downstream depends on them; one short job. The session then runs `search_tool.js` on the result |
| Running Scopus / Web of Science / Scholar searches in the browser | Session | The user watches, signs in and clears checks |
| Quick search: running the queries and collecting candidates | Helpers, `haiku`, in parallel (one per source or batch of queries) | Repetitive; the session writes the queries and decides which papers stay |
| Finding free copies on the web for records OpenAlex could not place | Helpers, `haiku`, about 10 records each | Repetitive look-ups; `retrieve.py` rejects anything that is not a real PDF |
| Reading a publisher's terms | Helper, `sonnet` | A wrong call risks the user's university access |
| Screening | Session | The reviewer decides; Claude records |
| Downloads, PRISMA counts, PDFs | Scripts | No model |

The user is advised to run the session on Sonnet. A skill cannot change the session model, so say so once if they ask.

## The plan is fixed

Follow the table on every run. If the user asks to change a step's model, or to stop using helpers, explain briefly that the skill runs each step on a planned model so results stay consistent and costs predictable, and carry on with the plan. The table is changed by editing this file, not during a run.

**The one exception is moving a step up to a stronger model, and only after asking.** Ask when a helper's output is clearly not good enough and a stronger model is the likely fix: for example a strings helper missing an obvious synonym family, a terms-reading helper that does not quote the clause it relies on, or a free-copy helper returning links that are not PDFs. Say which step, what went wrong, and which model you propose (`haiku` to `sonnet`, or `sonnet` to `opus`), and wait for a yes. Never move a step to a weaker model, and never switch without asking.

## Handing work to a helper

Give each helper everything it needs in its prompt, because it cannot see the conversation:
- the relevant intake answers (field, title, population, niche, year ranges);
- the exact input (queries to run, record list, paper files or URLs);
- the rules for that step from the branch file;
- the exact shape of what to return (for example one JSON object per record with the fields `retrieve.py` expects), so the session can check it and write it to the project files.

Run helpers for independent batches in parallel. When one fails or returns nothing, retry once on the same model, then do that batch in the session and say so.

## Where there are no helpers

claude.ai on the web has no `Agent` tool. There, every step runs in the session on the model the user picked in the chat's model menu; the workflow is otherwise identical. Tell the user once that the per-step models apply only in the Claude desktop app, Claude Code and Cowork.
