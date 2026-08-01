# no-slop

Write prose clean of AI texture, or audit an existing draft until it survives scrutiny.

Every other de-slop skill removes AI tells. This one also checks whether the piece is telling
the truth: a two-gate audit where **Gate 1 verifies every quoted or attributed line against
primary sources** (four verdicts, correction log) and **Gate 2 scores taste** (mechanical tell
scan plus a nine-dimension scorecard). Fidelity beats polish on every tiebreak. A shareable
lie is still a lie.

## What's inside

```
no-slop/
├── SKILL.md                    # the contract: modes, banned list, gates, report format
├── references/
│   ├── fidelity-gate.md        # Gate 1 full procedure: verdicts, traps, correction log
│   └── taste-gate.md           # Gate 2 full procedure: scorecard, required fixes
├── scripts/slop_check.py       # mechanical scanner: tic scan + quote-vs-corpus matching
└── tests/test_slop_check.py    # smoke tests for the scanner
```

## The scanner

```
python scripts/slop_check.py tics <draft.md>
python scripts/slop_check.py quotes <draft.md> --corpus <sources-file-or-dir>
```

`tics` flags dashes, banned phrases, cadences, hedges, recaps, filler, narrative cliches, and
over-correction (runs of three or more very short sentences, the fingerprint of prose scrubbed
too hard). It blanks fenced code, inline code, blockquotes, and quoted spans first, so a draft
can quote bad writing on purpose without tripping it; `--include-quoted` opts back in. `quotes`
extracts every quoted span, normalizes punctuation, case, curly quotes, and HTML escapes, then
reports MATCH / PARTIAL / NONE against your source corpus. PARTIAL usually means silent
paraphrase drift; NONE means unverified or fabricated. The script finds candidates; verdicts
stay human. Both exit 1 on any finding, so they work as a gate in a loop.

The skill's own files pass their own scan, and the scanner runs again on every rewrite it
produces, capped at four passes.

## Provenance

Extracted from a real book-production pipeline: five nonfiction books, every quoted line
verified against primary sources before compile (one audit: 226 quoted spans checked, six
defects found and fixed, zero unverified lines shipped). Narrative tells adapted from
haowjy/creative-writing-skills (Apache-2.0). In benchmarked runs against a no-skill baseline,
the skill passed 20/20 graded checks vs 18/20, and caught all four planted quote defects with
exact source wording.

## The two rules a scanner cannot check

**Never inject.** A de-slop pass must not add a fact, number, name, stance, or first person the
source never had. A fabricated specific is worse than the vague phrasing it replaced, so the
skill leaves a marked placeholder and flags the gap instead of filling it.

**Never overcorrect.** Prose scrubbed to fragments and stripped of every hedge is not clean, it
carries a second fingerprint. The skill keeps roughness the author chose and the register the
venue requires, and the scanner flags staccato runs so the failure is visible.

## Honest limits

The banned list is house style, enforced as taste. It is not an AI detector, and a hit is
never proof that a text was machine-written. For voice imitation use a style-converter skill;
no-slop governs texture and truth, and composes with any voice on top.
