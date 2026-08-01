# Gate 1: the source-fidelity audit (full procedure)

Runs whenever the content quotes anyone, attributes an idea, or presents a method as someone's.
Skip it only when nothing is attributed. This gate is the difference between a piece and a
plausible-sounding hallucination: one unverified epigraph in a piece whose selling point is
trust discredits the rest. Run it adversarially. Try to *catch* the draft lying.

## Audit more than quotes: audit authority

- Every **direct quote** (epigraphs plus inline quotations).
- Every **coinage** credited to a person (did they coin it, or inherit it?).
- Every **lineage claim** (is the originator credited correctly?).
- Every major claim presented as **someone's method**.
- Every **source note** exists and points somewhere real.
- Every **editor/author synthesis** is labeled as synthesis, not dressed as the subject's claim.

## Verify against

1. A **verbatim quote bank or source pack** if one exists (fastest, already extracted).
2. The **live primary sources** for anything the bank does not settle, especially epigraphs
   and pull-quotes, the highest-visibility lines.

Use `scripts/slop_check.py quotes` to extract every quoted span and match it against the source
corpus mechanically, then manually review every non-match (see Traps).

## The four verdicts

Assign one per quoted line:

- **VERBATIM**: found word-for-word in a primary source. Record the source and exact text.
- **CLOSE-PARAPHRASE**: clearly the person's idea, but the wording differs while sitting
  inside quotation marks. A real defect: a quote should be exact. Restore the exact wording,
  or drop the quotation marks and present it as paraphrase.
- **UNVERIFIED**: cannot be found in any available source. It may be real, but you cannot
  stand behind the precision. Downgrade to paraphrase or flag for the user. Never leave an
  unverifiable line dressed as a verified quote.
- **MISATTRIBUTED**: credited to the wrong person. Fix the attribution.

## Traps (each one found in real audits)

- **Fabricated fusion:** two separate real sentences welded into one quote never said as a
  unit. Split them, restore the contiguous wording, or mark the omission with an ellipsis.
- **Silent paraphrase drift:** a quote "improved" (a word swapped, a clause tightened, an
  "in crypto" dropped) until it is no longer what was written. The fix is the *exact* source
  text.
- **The clean-looking line with no home:** the most dangerous, because it reads perfectly.
  Confidence is not verification.
- **Mechanical false positives:** nested quotes, curly quotes, and HTML-escaped source text
  (`&gt;` for `>`) make real quotes look unmatched. Verify manually before calling them
  defects; do not "fix" a quote that was right.

## The correction log

Report findings in this table, led by a one-line summary count:

| Quoted line (truncated) | Attributed to | Verdict | Source + exact wording if it differs | Fix |
|---|---|---|---|---|

## The production-side counterpart

This gate audits a draft you were handed. The matching constraint on text *you* write lives in
SKILL.md under "Rewrite constraints": never inject a fact, name, number, or stance the source
did not contain, and leave a marked placeholder rather than filling a gap. No scanner can
enforce it, because the difference is provenance and provenance is invisible to a pattern.

## The standard, in one line

If you cannot point to where a quote came from, it is not a quote yet. Make it a paraphrase or
make it disappear.
