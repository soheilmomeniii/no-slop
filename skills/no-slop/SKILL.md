---
name: no-slop
license: MIT
description: >-
  Write prose clean of AI texture, or audit a draft through two gates: source fidelity
  (every quoted or attributed line verified against primary sources, four verdicts,
  correction log) and taste (mechanical tell scan plus a nine-dimension scorecard). Use
  when the user says "de-slop this", "slop check", "AI smell", "sounds like ChatGPT",
  "make it human", "humanize this", "sounds robotic", "reads like AI", "kill the em
  dashes", "verify the quotes", "fidelity check", "run the audit", or "taste pass", and
  when writing or rewriting X posts, threads, articles,
  essays, fiction scenes, book chapters, or landing copy that must not read AI-generated.
  Works at any length; the fidelity gate activates whenever quotes or attributions are
  present. Do not use for voice imitation (use a style-converter skill), UI design, or
  proving a text was AI-written: the banned list is house style, not a detector.
---

# No-Slop: write clean, audit hard

Two failure modes kill a piece of writing. It can be **false** (a quote that was never said, a
borrowed idea claimed as original), or it can be **slop** (generic AI texture nobody finishes,
trusts, or shares). This skill guards against both, in a fixed order: fidelity first, taste
second. When polish ever pulls against truth, **fidelity wins**. A shareable lie is still a
lie. Sharpen the framing, never the facts.

## Two modes

- **Write mode**: drafting or rewriting. Apply the style rules below from the first sentence,
  not as a cleanup step; prose written slop-first and scrubbed later keeps the skeleton of
  slop. Before delivering, run both gates on your own draft and fix what fails.
- **Audit mode**: the user hands you a draft. Run Gate 1, then Gate 2, and return the audit
  report (format below). Apply mechanical fixes when asked; flag judgment calls (an
  unverifiable-but-probably-real quote) for the user, who often knows the sources best.

This skill governs texture and truth, not voice, and composes with any voice skill. One
precedence rule: the punctuation bans stay in force even under a voice skill, unless the user
explicitly opts out.

## The style rules (always on)

### Banned: zero tolerance

One tell might survive review; three brand the piece as generated. Do not write:

- em dashes or double-hyphen separators, in any form (use periods, colons, commas, parentheses)
- "In today's rapidly evolving landscape..." and every cousin of it
- "This chapter/article/post explores..."
- "It is important to note..." / "It's worth noting..." / "We're excited to announce..."
- the "not X, but Y" cadence, and its staccato variant "Not X. It is Y."
- "That is..." as a sentence opener; "By understanding X, readers can..."
- hedges: "arguably", "in many ways", "to some extent", "one could argue"
- recap markers: "In short", "Ultimately", "At the end of the day", "In conclusion"
- filler: `delve`, `leverage` (verb), `unpack`, `seamless`, `game-changer`, `deep dive`,
  `empower`, `elevate`, `supercharge`, `unleash`
- filler only in its filler frame, literal use is fine: `unlock the potential` (not a door),
  `robust framework` (not robust standard errors), `the learning journey` (not a journey home),
  `harness the power of` (not harness the energy of the jet stream). Cutting the literal use is
  the over-correction this skill exists to prevent
- stock flourishes: `a testament to`, `plays a crucial role` and every adjective in that slot,
  `navigate the complexities`, `in an era of`, `in a world where`, `whether you're a...`,
  `it's no secret`, `look no further`, `let's dive in`, `treasure trove`, `a beacon of`,
  `tapestry of`, `in the realm of`
- performed candor as filler: `let's be honest`, `let's be real`, `let's face it`, `real talk`,
  `here's the thing`, `here's the kicker`, `here's the catch` (these are also injection
  failures; see the rewrite constraints). `let us be clear` is formal register, not this
- perfectly symmetrical sections; a generic recap after every section
- fake-deep abstractions with no quote or case behind them; strategy-deck phrasing

When you feel the pull to smooth, resolve, or summarize, that is the instinct talking, not the
reader's need. `references/taste-gate.md` explains why each pressure exists, which is what lets
you catch a tell the list does not name.

### Narrative tells (fiction and story-driven prose)

Recycled emotional choreography (`breath catching`, `jaw clenching`, `heart hammering`); named
emotions ("she felt a surge of determination") instead of the action the feeling produces;
tidy-summary endings ("For the first time, I understood...") instead of ending on action or
image; sentiment skew (dark scenes silver-lined, tension resolved in the paragraph that raised
it); one arc stamp on every scene; cluster metaphors (weight, light, drowning); zero subtext.
The scanner catches the first three; the rest need judgment.

### Prefer

- short claims
- primary-source-led sections
- concrete consequences: name the market, the number, the person
- cases before abstractions
- blunt operator sentences
- fewer transitions
- compression over explanation
- ambiguity where reality is ambiguous

**The style test:** if a paragraph could appear in a generic business ebook, cut or rewrite it.
**The repetition budget:** rotate examples, include an instructive failure, and never let three
sections share one skeleton.

## Rewrite constraints (govern what you produce)

Gate 1 audits the draft you were handed. These govern the text you write, and no scanner can
enforce them, because the difference is provenance and provenance is invisible to a pattern.

**Never inject.** None of the following may be added to a text that did not already contain it,
and each is a failure even when the result scans clean: fake first person (if the source has no
"I", the rewrite has no "I"); manufactured stakes ("now more than ever"); forced contrarianism
(inventing a foil is inventing a claim); performed candor ("let's be honest", "real talk");
staccato conversion (chopping ordinary sentences to manufacture rhythm); and **invented
specifics**, a number, name, date, tool, or mechanism the source never contained. Specificity is
the most tempting fix because it always reads better, and a fabricated specific is worse than
the vague phrasing it replaced. If the concrete detail is missing, leave a marked placeholder
(`[ADD: which study?]`) and flag the gap. Never fill it.

**The test:** subtraction and sharpening are in scope (cutting filler, making an existing claim
concrete, surfacing a buried point). Addition of stance, personality, or fact is not.

**Do not overcorrect.** Scrubbing at maximum strictness produces a second fingerprint:
fragments, forced punch endings, every hedge stripped from a sentence whose uncertainty was
real. That reads as humanizer output, which is its own genre of slop. Never write three
sentences of five words or fewer in a row (the scanner flags runs of three). Keep roughness the
author chose, keep a hedge that carries real uncertainty, and keep the register the venue
requires: academic prose keeps calibrated hedging, safety text keeps its absolutes, legal text
keeps its exceptions. You cut filler, not a language's natural redundancy. This rule tunes how
hard you cut; it never relaxes the banned list.

## Gate 1: source-fidelity audit

Runs whenever the content quotes anyone, attributes an idea, or presents a method as someone's;
skip only when nothing is attributed. Extract every quoted span, verify each against the quote
bank or live primary sources, and assign one of four verdicts: **VERBATIM**,
**CLOSE-PARAPHRASE**, **UNVERIFIED**, or **MISATTRIBUTED**. Run it adversarially: try to catch
the draft lying. Read `references/fidelity-gate.md` for the full procedure, the traps found in
real audits (fabricated fusion, silent paraphrase drift, mechanical false positives), and the
correction-log format. The standard in one line: if you cannot point to where a quote came
from, it is not a quote yet.

```
python scripts/slop_check.py quotes <draft.md> --corpus <sources-file-or-dir>
```

## Gate 2: taste audit

Run the mechanical scan, then score nine dimensions from 1 to 5: source density, primary
voice, case proof, originality, AI smell (inverted), rhythm variation, shareability,
usefulness, public-object feel. Read `references/taste-gate.md` for the scorecard anchors,
scoring units per content type, and the required fixes. Never trade a Gate 1 fact back for a
smoother sentence.

```
python scripts/slop_check.py tics <draft.md>
```

The scan blanks fenced code, inline code, blockquotes, and quoted spans before matching, so a
draft may quote bad writing on purpose without tripping it. Pass `--include-quoted` to scan
inside quotations too.

## The verify loop (both modes)

Re-run the scan on everything you emit, and not only on the input: rewritten text and, in audit
mode, the report itself. Skipping this step is the common failure: the model producing the fix
carries the priors that produced the tell, so a flagged "not X, but Y" reliably comes back as
"less about X than Y", the same move in a wig. Fix and re-scan until a pass returns zero hits.
**Cap at four passes.** If a pattern survives four, rewrite that sentence from scratch starting
from its bare claim: what fact or opinion is this sentence for? Report how many passes it took.

## Audit report format (audit mode output)

```
# No-Slop Audit: <piece name>
## Summary
- Quotes checked: N (VERBATIM x / CLOSE-PARAPHRASE y / UNVERIFIED z / MISATTRIBUTED w)
- Tic scan: N hits, clean after P verify passes | Taste: lowest dimensions named
- Verdict: SHIP / FIX THEN SHIP / REWRITE
## Gate 1: correction log   (table per references/fidelity-gate.md)
## Gate 2: tic scan         (file:line | matched text in backticks | replacement)
## Gate 2: taste scorecard  (9 rows, scored, one line of evidence each)
## Required fixes           (numbered, most damaging first)
```

Lead with the summary counts. In write mode, the report collapses to one line per gate
confirming the checks ran clean, plus anything you had to fix.

**The report is prose you produced, so the style rules govern it too.** This is the failure
mode that discredits an audit fastest: a report that spends a paragraph removing the user's em
dashes while using four of its own. Render every matched span, banned phrase, and dash you
quote inside backticks, which the scanner exempts as inline code, then scan the report before
delivering it. An audit report that fails its own scan is not deliverable. Verdict criteria are
in `references/taste-gate.md`; use them so two auditors reach the same call.
