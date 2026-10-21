import sys
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

out = sys.argv[1]
ss = getSampleStyleSheet()
body = ParagraphStyle("b", parent=ss["Normal"], fontName="Helvetica", fontSize=7.2, leading=8.8)
head = ParagraphStyle("h", parent=body, fontName="Helvetica-Bold", textColor=colors.white)
title = ParagraphStyle("t", parent=ss["Title"], fontSize=14, leading=17, spaceAfter=2, alignment=0)
sub = ParagraphStyle("s", parent=ss["Normal"], fontSize=8.5, leading=11)
note = ParagraphStyle("n", parent=ss["Normal"], fontSize=7.5, leading=9.5)

cols = ["#", "Title", "Author(s) &amp; Year", "Quartile", "Method", "Access",
        "Introduction", "Methodology", "Results", "Discussion", "Theoretical Framework"]
widths = [0.25, 1.30, 0.80, 0.80, 0.75, 0.55, 1.05, 1.25, 1.25, 1.15, 1.05]
margin = 0.35
usable = 11 - 2 * margin
assert abs(sum(widths) - usable) < 1e-6 or sum(widths) < usable, (sum(widths), usable)

rows = [
 ["1", "Gamified quizzes and intrinsic motivation among Malaysian undergraduates",
  "Tan &amp; Rahman, 2023", "Unranked/ Unavailable", "Quantitative", "Unclear",
  "Tests whether gamified quizzes raise undergraduates' intrinsic motivation.",
  "Cross-sectional survey; n = 320 undergraduates at two public universities; analysed with PLS-SEM.",
  "Gamified quiz use significantly predicted intrinsic motivation (&beta; = 0.38, p &lt; .001).",
  "Findings back SDT; authors advise designing quizzes that support learner autonomy.",
  "Self-Determination Theory"],
 ["2", "Leaderboards in secondary science classrooms",
  "Lee, 2022", "Unranked/ Unavailable", "Quantitative", "Unclear",
  "Tests the effect of leaderboards on engagement in secondary science lessons.",
  "Quasi-experiment; n = 140 pupils in Penang; 8-week intervention.",
  "Not retrieved (results section missing from the available copy).",
  "Leaderboards may lower motivation among low-performing pupils.",
  "Not explicitly stated"],
 ["3", "Students' lived experience of gamified learning",
  "Ali &amp; Wong, 2024", "N/A (thesis)", "Qualitative", "Unclear",
  "Explores how students experience courses that use gamification.",
  "Interviews with 18 students; thematic analysis.",
  "Three themes identified: competition, autonomy and fatigue.",
  "Gamification fatigue emerges after week 6 of a course.",
  "Flow theory"],
 ["4", "Badges and engagement in MOOCs: a review",
  "Ali, 2021", "Unranked/ Unavailable", "Theoretical/ Review", "Unclear",
  "Reviews the evidence on digital badges and engagement in MOOCs.",
  "Narrative review of 40 studies.",
  "24 of 40 studies linked badges to short-term gains in course completion.",
  "Whether badges have lasting effects remains unclear.",
  "Goal-setting theory"],
]

data = [[Paragraph(c, head) for c in cols]] + [[Paragraph(c, body) for c in r] for r in rows]
t = Table(data, colWidths=[w * inch for w in widths], repeatRows=1, hAlign="LEFT")
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3A5F")),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9AA5B1")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF2F6")]),
    ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
]))

story = [
 Paragraph("Literature Review Matrix: Gamification and Student Motivation", title),
 Paragraph("Field: Education &nbsp;|&nbsp; Years: 2021-2026 &nbsp;|&nbsp; Papers: 4 (supplied by the user) &nbsp;|&nbsp; Prepared 21 October 2026", sub),
 Spacer(1, 8), t, Spacer(1, 10),
 Paragraph("<b>Synthesis.</b> Three sources each use a different theory (Self-Determination Theory, flow theory, "
   "goal-setting theory) and the leaderboard study names none, so there is no shared framework yet. Methods are spread out: "
   "two quantitative studies, one qualitative thesis and one narrative review, with no mixed-methods work. The evidence leans positive "
   "in the short term (a moderate SDT-consistent effect in the survey, short-term completion gains in 24 of 40 reviewed studies) "
   "but three sources point to limits: possible demotivation of low performers, fatigue after week 6, and unclear long-term effects. "
   "Gaps your study could fill: longitudinal designs past 6-8 weeks, mixed-methods work, and analysis of how prior achievement moderates the effect of "
   "competitive elements such as leaderboards. Two of the four studies are set in Malaysia, so findings from other settings are thin.", note),
 Spacer(1, 6),
 Paragraph("<b>Notes on labels.</b> <i>Quartile:</i> SCImago quartiles were searched for each journal on 21 October 2026. No SJR record "
   "was found for <i>Journal of Asian Education Studies</i>, <i>Science Teaching Review</i> or <i>Open Learning Letters</i>, and scimagojr.com "
   "could not be reached directly, so these are labelled Unranked/Unavailable instead of guessed. Paper 3 is a PhD thesis, so no quartile applies. "
   "<i>Access:</i> the DOIs could not be resolved and no open-access record was found, so access is Unclear for all four. "
   "<i>Paper 2:</i> its results section is missing from your copy, so that cell reads Not retrieved. "
   "All cells come only from the text copies you supplied, paraphrased.", note),
]

doc = SimpleDocTemplate(out, pagesize=landscape(letter), leftMargin=margin * inch, rightMargin=margin * inch,
                        topMargin=0.4 * inch, bottomMargin=0.4 * inch,
                        title="Literature Review Matrix - Gamification and Student Motivation")
doc.build(story)
print("widths", sum(widths), "usable", usable)
