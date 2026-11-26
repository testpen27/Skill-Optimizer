# Haiku vs Sonnet as the reading helper (2026-11-26)

Four open-access papers (PLOS Digital Health quasi-experiment, Frontiers in
Psychology quasi-experiment, a Springer phenomenological interview study, an
MDPI mixed-methods study), full text fetched, navigation trimmed. Each model
read each paper once with `claude -p` using the skill's own Reading and Writing
rules (`reader_prompt.txt`); the billed cost and token counts come from each
run's JSON (`run_costs.json`). Accuracy: the skill's `check_evidence.py`
(`outputs/check_*.txt`), a numbers-appear-in-the-paper check, and one blind Opus
5.5 grader per paper (`grader_prompt.txt`, `grading/`, X/Y order in
`grade_mapping.json`). Paper texts are not stored here; DOIs are in the report.
