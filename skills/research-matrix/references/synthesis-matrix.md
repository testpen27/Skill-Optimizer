# Synthesis matrix (only when the user asks for one)

A synthesis matrix puts **themes down the side and sources across the top**.
Each cell holds what that source says about that theme. It is the matrix used
to write a literature review chapter: you read along a row to see how the
sources agree or differ on one theme. It is documented by university writing
centers and libraries (for example NC State's Writing and Speaking Tutorial
Services, Johns Hopkins Sheridan Libraries, Williams College Libraries), so
it is a standard academic tool.

How it differs from the LRM: the LRM is organised by paper (what each paper
did and found); the synthesis matrix is organised by theme (what the
literature says about each idea).

## Steps

1. Have the LRM (or at least a list of papers with their codes). Build it
   first if it does not exist, because the synthesis matrix reuses its codes
   and labels through `--lrm`.
2. Agree the **themes** with the user. Take them from the user's research
   question or the recurring ideas in the LRM rows. Draft the list in chat and
   let them change it. If the user brings their lecturer's or supervisor's
   template, use its themes and wording.
3. Key each cell by the paper's `id` or DOI as written in `lrm.json`, never by
   its P-code (the codes renumber when the paper list changes). Fill each cell
   from what the paper actually says, paraphrased, in the
   third person, one or two short sentences. Leave a cell empty when the paper
   does not address the theme: the empty cell is a finding. Quote only short
   phrases, with a page number.
4. Optional `across` text per theme: one or two sentences on how the sources
   agree or disagree. Write it from the cells.
5. Write `synthesis.json` (format at the top of `scripts/build_synthesis.py`),
   then:
   ```
   python3 scripts/build_synthesis.py synthesis.json --lrm lrm.json --check
   python3 scripts/build_synthesis.py synthesis.json --lrm lrm.json --out "<folder>/Matrix.xlsx"
   ```
   This adds the `Synthesis matrix` sheet to the project workbook. An empty
   cell is shaded; the `Sources covering` column counts the filled cells with
   a live formula, and a theme covered by 0 or 1 sources is shaded as a gap.
   Open or render the sheet and look at it.
