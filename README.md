# Skill-Optimizer

Workspace for evaluating and optimizing Claude skill descriptions with the
`skill-creator` description-optimization loop.

- `skills/` — skills under evaluation
- `evals/` — trigger eval sets (query + should_trigger label)
- `results/` — optimization run outputs (results.json, HTML reports)
- `reports/` — written-up findings per skill

Some skills (e.g. `skills/tv3-interactive-embed/`) keep their own eval set,
run results, report and packaged `.skill` build under an `evals/` subfolder
inside the skill directory itself, rather than in the shared top-level
`evals/`/`results/`/`reports/`. `evals/` at any depth is excluded from
`package_skill.py`'s output, so this stays self-contained without bloating
the distributable `.skill` file.
