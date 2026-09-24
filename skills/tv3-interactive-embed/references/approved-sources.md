# Approved, pending and blocked sources

Only entries under **Approved** may be used, and only within the logged scope. Numbers match the list the user saw on 2026-09-21.

## Approved

**1. https://github.com/WordPress/agent-skills** : approved 2026-09-21. User wording: "okay get no 1 and rebuild".
- Scope: reference reading only. Nothing installed, cloned, run or copied; the repo is GPL-2.0-or-later, so no text was reused.
- Read: the repo README (as data; no instructions aimed at the AI were found). GitHub's robots rules refused automated fetches of the repo's folder pages, so the individual skill files were not read. Search also surfaced third-party mirrors of the repo (skills.cat, playbooks.com, skillselion.com, openskillindex.com, a private Gitea, skillshub); they were not approved and nothing was taken from them.
- Taken: (a) its skills cover PHP-side plugin, block and theme work, so its nonce/capability/escaping guidance does not transfer to a pasted HTML embed; (b) a pointer in SKILL.md section 7 that a WordPress block or plugin is the long-term route for reusable widgets. Reading its individual skill files later needs a fresh look at scope with the user.

## Pending user approval (search snippets only; nothing fetched, installed or used)
2. https://github.com/risonsimon/interactive-deep-notes : turns an article or video into a self-contained interactive HTML page. Flags: single author; runs Python scripts via `uv`; fetches articles through the r.jina.ai proxy; uses localStorage. Fit: low.
3. https://github.com/QinghongLin/data2story-skill : data-to-article pipeline. Flags: needs external API keys (OpenRouter media tools); runs scripts. Fit: low.
4. https://github.com/respira-press/agent-skills-wordpress : vendor skills built on the vendor's MCP server (README cites 197 tools) with deep site access. Flags: highest privilege of the set. Fit: low.
5. https://github.com/trewknowledge/agent-skills : WordPress VIP and project-documentation skills. Fit: low.
6. https://github.com/wes-davis/automattic-agent-skills : an individual's copy of an Automattic repo. Flags: mirror; prefer the original if anything is approved.

## Blocked
(none yet)
