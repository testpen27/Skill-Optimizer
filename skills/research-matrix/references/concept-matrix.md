# Concept matrix (only when the user asks for one)

A concept matrix puts **papers down the side and concepts across the top**;
an X marks a paper that deals with a concept. It comes from Webster and
Watson (2002), "Analyzing the past to prepare for the future: Writing a
literature review", MIS Quarterly 26(2), who adapted it from Salipante,
Notz and Bigelow (1982). It is used for theoretical, scoping and
concept-centred reviews, and answers one question: which concepts has the
literature covered, and which has it left alone? A concept with no X, or one
X, is a candidate research gap.

How it differs from the other matrices: the LRM says what each paper found;
the synthesis matrix says what the literature says about each theme; the
concept matrix only records who covers what, so it is quick to read and says
nothing about findings.

Webster and Watson also describe an extended form with a **unit of analysis**
(for example individual, group, organisation): each concept is split into one
column per unit, because a concept can mean something different at each level.
Offer it only when the user's topic spans levels.

## Steps

1. Have the LRM (or a list of papers with codes); build it first if needed.
   The concept matrix reuses its codes and labels through `--lrm`.
2. Agree the **concepts** with the user: the constructs in their title and
   research question, plus any that recur in the papers. Use the user's own
   words for them. Draft the list in chat first.
3. Key each paper by its `id` or DOI as written in `lrm.json`, never by its
   P-code (the codes renumber when the paper list changes). Mark each paper
   for the concepts it actually deals with, from the paper
   itself (title, abstract, full text), not from the title alone. A paper that
   only mentions a concept in passing is not marked.
4. Write `concept.json` (format at the top of `scripts/build_concept.py`), then:
   ```
   python3 scripts/build_concept.py concept.json --lrm lrm.json --check
   python3 scripts/build_concept.py concept.json --lrm lrm.json --out "<folder>/Matrix.xlsx"
   ```
   This adds the `Concept matrix` sheet to the project workbook. The paper
   counts under each column and the coverage table are live Excel formulas over
   the X marks, so they update if the user changes a mark; concepts covered by
   0 or 1 paper are shaded as gaps. Do not type the counts. Open or render the
   sheet and look at it.
5. Tell the user what the matrix shows: which concepts are well covered, which
   are thin, and what that suggests for their study, in a few sentences.
