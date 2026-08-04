# no-slop

Write prose clean of AI texture, or audit an existing draft until it survives scrutiny.

Every other de-slop skill removes AI tells. This one also checks whether the piece is telling
the truth: a two-gate audit where **Gate 1 verifies every quoted or attributed line against
primary sources** (four verdicts, correction log) and **Gate 2 scores taste** (mechanical tell
scan plus a nine-dimension scorecard). Fidelity beats polish on every tiebreak. A shareable
lie is still a lie.

## What it does, in ten seconds

Texture, before and after:

```
before  In today's rapidly evolving landscape, our robust platform doesn't just
        streamline workflows, but empowers teams to unlock their full potential.

after   The platform cuts approval time from three days to four hours. Teams stop
        waiting on a manager who is in another timezone.
```

Truth, which the tell-removers do not check. A draft quotes a source:

```
As Reyes put it, "distribution is a moat only when the buyer renews without a
meeting, and the channel you own beats the channel you rent."

$ python scripts/slop_check.py quotes draft.md --corpus sources/
[PARTIAL] “distribution is a moat only when the buyer renews without a meeting, and...”  <- memo.md
```

Both halves are real. They come from two documents eleven weeks apart, welded into a sentence
she never said. It reads beautifully, and a scanner that only hunts AI tells calls it clean.

## What's inside

```
no-slop/
├── SKILL.md                    # the contract: modes, banned list, gates, report format
├── references/
│   ├── fidelity-gate.md        # Gate 1 full procedure: verdicts, traps, correction log
│   └── taste-gate.md           # Gate 2 full procedure: scorecard, required fixes
├── scripts/slop_check.py       # mechanical scanner: tic scan + quote-vs-corpus matching
├── tests/test_slop_check.py    # regression tests for the scanner
└── LICENSE                     # MIT
```

## The scanner

```
python scripts/slop_check.py tics <draft.md>
python scripts/slop_check.py quotes <draft.md> --corpus <sources-file-or-dir>
```

`tics` flags dashes, banned phrases, cadences, stock flourishes, hedges, recaps, filler,
narrative cliches, and over-correction (runs of three or more very short sentences, the
fingerprint of prose scrubbed too hard). It blanks fenced code, inline code, blockquotes, and
quoted spans first, so a draft can quote bad writing on purpose without tripping it, and the
exemption survives a quotation wrapped across a line break; `--include-quoted` opts back in. A
paragraph holding an odd number of quote marks is scanned in full and named on stderr, because
a silent exemption hides tics without ever printing a line. Typographic apostrophes are folded
to straight ones before matching, so a draft out of Notion or Word scans the same as one typed
in a terminal.

`quotes` extracts every double-quoted and curly-single-quoted span (straight single quotes are
never treated as quote marks, since apostrophes make them unrecoverable; a nested quote counts
once, and no span crosses a paragraph break), normalizes punctuation, case, curly quotes, and
HTML escapes, then reports MATCH / PARTIAL / NONE against your source corpus. A quote elided
with an ellipsis is a MATCH only when every segment is verbatim, in one source file, in source
order, and only when what the ellipsis omits there is neither a negation nor too short to be
worth eliding: "we are ... planning any layoffs" against a source saying "we are not planning
any layoffs" is text-perfect and means the opposite. Segments found only across different files
are a fusion and stay flagged. The manuscript is never part of its own corpus, so a quote cannot
verify against itself. PARTIAL usually means silent paraphrase drift; NONE means unverified or
fabricated. The script finds candidates; verdicts stay human. Both exit 1 on any finding, so
they work as a gate in a loop.

The skill's own files pass their own scan, and the scanner runs again on every rewrite it
produces, capped at four passes.

## Testing

```
python -m pytest tests/ -q
```

`pytest` is a development dependency, needed only to run that suite. The scanner itself imports
nothing outside the Python standard library: no network, no subprocess, no shell. Running the
skill never installs anything.

## Provenance

Extracted from a real book-production pipeline: five nonfiction books, every quoted line
verified against primary sources before compile (one audit: 226 quoted spans checked, six
defects found and fixed, zero unverified lines shipped). Narrative tells adapted from
haowjy/creative-writing-skills (Apache-2.0).

The skill has also been benchmarked against a no-skill baseline, on graded scenarios including
planted quote defects. Read the scenarios and their fixtures in `evals/`, and the recorded run
results in `CHANGELOG.md`, then rerun them yourself rather than take a number on trust.

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
