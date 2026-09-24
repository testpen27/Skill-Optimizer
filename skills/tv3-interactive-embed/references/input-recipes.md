# Input recipes: what to hand over per piece type

How a news fact turns into working logic, split by the two shapes that differ most: quiz-style pieces (comparison logic) and calculators (formula logic).

## Facts vs formulas

Facts ("eligibility age is 17–60") come straight from the article or whatever the user pastes in — read the body copy, official quotes, and cited figures directly. Formulas ("EPF contribution is 11% of wage up to a ceiling") are riskier: one missing rate or threshold gives every reader a wrong result, silently, and a news article's prose rarely contains the actual schedule. Always ask for the source table before writing calculation logic rather than approximating one from memory — this is what SKILL.md section 1's "never invent figures" rule means in practice for a calculator.

## Recipe: quiz / Q&A

What to ask the user for, or pull from the article, if not offered:
- Topic and, optionally, a short intro line
- Per question: the question text, 2–4 options, which one is correct, and a one-line reason shown after answering
- Optional: a source name/date for the "Sumber" line
- Optional: tiered result messages by score range

Example input:
```
Kuiz: Adakah Anda Layak Menderma Darah?
1. Umur minimum untuk menderma darah? | 15 / 17 / 21 -> 17 (Sumber: PDN, umur 17-60)
2. Berat minimum? | 40kg / 45kg / 50kg -> 45kg (Sumber: PDN)
Sumber: Pusat Darah Negara, Sept 2026
```

Logic this becomes: an array `[{q, options, correctIndex, why}]`. On submit, compare each selected radio's index to `correctIndex`, accumulate a score, reveal each `why` via `textContent`, then show a score message (matched against thresholds if the user gave any). See `references/shell.html` for the working pattern.

## Recipe: calculator (worked example: salary)

A calculator's correctness depends entirely on what's supplied, so confirm all of this before writing code:
- The exact quantity being calculated ("net salary after EPF and PCB", not just "salary calculator")
- Every input field: name, type (number/select), unit, and valid range (e.g. gross salary RM, 0–999,999; age band; marital status; children)
- The full formula as officially published, tier by tier if it has brackets — for EPF/SOCSO/EIS/PCB-style figures this means the actual contribution or tax table for the year, not a remembered rate, because these change yearly and a stale rate is a wrong paycheck for a reader
- The rounding rule (nearest RM0.05, 2 decimal places, etc.) and edge behaviour (wage above/below a ceiling, zero or negative input)
- What to display: just the final figure, or a full breakdown (gross, each deduction, net)

Example input:
```
Kalkulator: Anggaran Caruman KWSP Pekerja
Input: Gaji bulanan (RM), umur (di bawah 60 / 60 & ke atas)
Formula (di bawah 60): jika gaji <= RM5,000 guna Jadual Pertama KWSP (bukan peratusan tetap);
  jika gaji > RM5,000, caruman pekerja = 11% x gaji, caruman majikan = 12% x gaji
Formula (60 & ke atas): caruman pekerja = 0%, majikan = 4%
Bundar ke RM terdekat.
Sumber: KWSP, Akta Kumpulan Wang Simpanan Pekerja (Jadual Ketiga), semakan Sept 2026
```

Logic this becomes: an ordered tier array (`[{upTo, rate}, ...]`, or a literal lookup table when the source uses one rather than a flat percentage — don't flatten a schedule into an approximate percentage), a pure function that takes validated numeric input and returns `{employee, employer, net}`, and a render step that writes each figure with `textContent` — never by interpolating raw input into `innerHTML`, per the embed contract's rule 7. `references/shell-calculator.html` implements exactly this split (validate → calculate → render) and is the starting point for any calculator.

## If the formula isn't supplied

Ask for the source table before writing the calculation. A calculator with a guessed formula is worse than no calculator — it looks authoritative while being wrong. A quiz's facts are usually short enough to pull straight from the article body; a calculator's formula almost always needs to be pasted or linked directly, since government schedules aren't reliably in general knowledge.
