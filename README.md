# no-slop

[![skills.sh](https://skills.sh/b/soheilmomeniii/no-slop)](https://skills.sh/soheilmomeniii/no-slop)
[![CI](https://github.com/soheilmomeniii/no-slop/actions/workflows/ci.yml/badge.svg)](https://github.com/soheilmomeniii/no-slop/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Write prose clean of AI texture, or audit a draft until it survives scrutiny.

```
npx skills add soheilmomeniii/no-slop
```

Or as a Claude Code plugin:

```
/plugin marketplace add soheilmomeniii/no-slop
/plugin install no-slop@somo-writing-skills
```

Every other de-slop skill removes AI tells. This one also checks whether the piece is telling
the truth.

## Two gates

**Gate 1, source fidelity.** Every quoted or attributed line is verified against primary
sources and assigned one of four verdicts: verbatim, close-paraphrase, unverified, or
misattributed. Silent paraphrase drift, fused quotes, and coinages credited to the wrong person
all get caught. The standard is one line: if you cannot point to where a quote came from, it is
not a quote yet.

**Gate 2, taste.** A mechanical scan for banned phrases, cadences, dashes, narrative cliches,
and over-correction, then a nine-dimension scorecard scored by judgment. Fidelity beats polish
on every tiebreak, because a shareable lie is still a lie.

## Two rules a scanner cannot check

**Never inject.** A de-slop pass must not add a fact, number, name, stance, or first person the
source never had. A fabricated specific is worse than the vague phrasing it replaced, so the
skill leaves a marked placeholder and flags the gap rather than filling it.

**Never overcorrect.** Prose scrubbed to fragments with every hedge stripped is not clean, it
carries a second fingerprint. The skill keeps roughness the author chose and the register the
venue requires, and the scanner flags staccato runs so the failure is visible.

## The scanner

```
python skills/no-slop/scripts/slop_check.py tics   <draft.md>
python skills/no-slop/scripts/slop_check.py quotes <draft.md> --corpus <sources-dir>
```

Pure Python, standard library only, no network, no subprocess, no shell. `tics` flags banned
constructions and over-correction; `quotes` reports MATCH, PARTIAL, or NONE per quoted span
against your sources and names the file each one matched. It reads curly single quotes as well
as double quotes, verifies an ellipsis-elided quote segment by segment, in order, inside one
source file, refuses to call it verified when the ellipsis omits a negation (text-perfect and
meaning-inverted is the misquote a fidelity gate exists to catch), and never counts the
manuscript as part of its own corpus. Exit codes are the contract: 0 clean,
1 findings, 2 error. Findings print to stdout, guidance to stderr, so the output pipes cleanly.

Exempt spans are blanked before matching, so a draft may quote bad writing on purpose without
tripping the scan. The skill's own files pass their own scan, and a test enforces it.

## Evals

Eleven scenarios in `skills/no-slop/evals/`, with fixtures. Four are adversarial by design:
they punish a skill that scrubs too hard, that invents a specific to sound punchier, that
strips hedges from an academic limitations section, or that flags an honest ellipsis-elided
quote while missing a real cross-source fusion. On the v1.4.0 run recorded in `CHANGELOG.md`,
ten independent agents passed ten of ten.

## Layout

```
skills/no-slop/
├── SKILL.md                    the contract: modes, banned list, gates, report format
├── README.md                   the skill's own readme
├── references/
│   ├── fidelity-gate.md        Gate 1: verdicts, traps, correction log
│   └── taste-gate.md           Gate 2: scorecard, verdict criteria, carve-outs
├── scripts/slop_check.py       the scanner
├── tests/                      28 tests, including a self-scan gate
└── evals/                      11 scenarios plus fixtures
tools/validate_skills.py        spec + security validator, run in CI
```

## Honest limits

The banned list is house style, enforced as taste. It is not an AI detector, and a hit is never
proof that a text was machine-written. Published measurements find vocabulary lists barely
separate machine prose from human prose, while rhythm uniformity separates them well, so treat
every finding as a revision trigger and never as an accusation. For voice imitation use a
style-converter skill; no-slop governs texture and truth, and composes with any voice on top.

## License

MIT, see `LICENSE`. One section adapts Apache-2.0 material, credited in
`THIRD-PARTY-NOTICES.md`.
