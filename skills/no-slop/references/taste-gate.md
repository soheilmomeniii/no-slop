# Gate 2: the taste audit (full procedure)

Runs after Gate 1. Fidelity was locked there; never trade a fact back for a smoother sentence.

## Why the banned patterns exist

Training rewarded complete answers, so sections over-resolve and grow recaps. It rewarded one
safe register, so voice flattens toward competent and slightly formal. It rewarded thorough
delivery, so explanations bloat and transitions multiply. The banned list is the surface of
those three pressures. Knowing the cause is what lets you catch a tell the list does not name:
when the pull is to smooth, resolve, or summarize, that is the instinct talking.

The list is house style enforced as taste, never evidence of authorship. Word and phrase
frequencies shift with every model, prompt, and genre, and published measurements find
vocabulary lists barely separate machine text from human text at all, while rhythm uniformity
separates them well. Score the rhythm dimensions with that in mind, and never tell a user a hit
proves a text was generated.

First run `scripts/slop_check.py tics` for the mechanical scan (banned phrases, dashes,
cadences, narrative cliches), then score the nine dimensions, which need judgment:

| Dimension | 1 (fail) | 5 (pass) |
|---|---|---|
| Source density | claims float free | quotes, dates, receipts where claims need them |
| Primary voice | the author talks over the sources | the subject's words carry the authority |
| Case proof | pure abstraction | a real win/failure/ambiguous case anchors it |
| Originality | could be by anyone | unmistakably this author/corpus |
| AI smell (inverted) | generic transitions, symmetry, filler | blunt, compressed, human |
| Rhythm variation | machine-stamped skeleton | deliberate, varied structure |
| Shareability | nothing quotable | lines a reader would screenshot (see the note below) |
| Usefulness | inspiring but inert | the reader can act on it |
| Public-object feel | a homework file | a curated artifact |

**Scoring unit:** per chapter for books; per piece for articles, posts, and threads. For
short-form, "rhythm variation" means line and sentence shape (not every line the same length,
not a listicle stamp), and "source density" means receipts present where claims invite doubt.
For fiction, score per scene or chapter, and read "AI smell" as including the narrative tells
in SKILL.md.

**On shareability, a deliberate disagreement.** Several de-slop skills instruct the opposite:
"cut quotables, if it sounds like a pull-quote, rewrite it." Their reasoning is sound for the
case they have in mind, a line polished into aphorism to substitute for evidence. This skill
takes the other side, because the work it was built for (books, essays, and threads designed to
be cited) depends on lines a reader can lift. The resolution is the anchor, not the ban: score
shareability high only when the quotable line is earned by a case, a source, or a number in
the surrounding text. A pull-quote that floats free of evidence is fake-deep abstraction under
a different name, and the banned list already covers it.

## Required fixes

- **Source density below 3:** add primary material, or downgrade the claim to match what you
  can actually source.
- **Case proof below 3:** add a win, failure, or ambiguous case, or cut the abstraction.
- **AI smell below 3** (the piece smells generated): compress, vary rhythm, add a source or
  case, cut generic transitions.
- **Three sections sharing one pattern:** break the template.
- **Over-correction flagged** (a staccato run, stripped hedges, forced punch endings): restore
  the register the piece needs. Scrubbed-to-fragments prose is a second fingerprint, not the
  absence of one. See the rewrite constraints in SKILL.md.

## The verdict

Pick one, by these criteria, so two auditors reach the same call:

- **REWRITE**: any fabricated quote or misattribution the author cannot resolve, or three or
  more dimensions at 2 or below, or the piece runs on one repeated skeleton throughout.
- **FIX THEN SHIP**: defects are named and fixable in place. Any unresolved UNVERIFIED or
  MISATTRIBUTED line caps the verdict here at best, however clean the prose is.
- **SHIP**: Gate 1 clean or fully corrected, tic scan clean, no dimension below 3.

## Two carve-outs the scanner cannot make

**Factual contrast is not the banned cadence.** The ban targets the emphasis move ("not just a
tool, but a movement"), where the negated half carries no content. A sentence where both halves
are load-bearing facts ("the sample was not random, but stratified") is legitimate and stays.
The scanner will still flag it, so say so in the report and give the reason rather than
silently ignoring the hit.

**Register beats the banned list where the venue requires it.** Academic prose keeps calibrated
hedges, safety documentation keeps its absolutes, legal text keeps its exceptions. Note the
exemption and why. Every other suppressed hit needs a written reason too: an unexplained
suppression is indistinguishable from a miss.

## What finished feels like

**Passing:** sourced, sharp, quote-led where sources exist, case-proven, rhythm-varied, low
author ego, honest about uncertainty. **Failing:** a course PDF, an AI-generated textbook,
over-symmetrical, over-explained, under-sourced, more author than subject.
