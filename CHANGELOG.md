# Changelog

## 1.6.0 (2026-08-07)

Built after reading six rival anti-slop skills end to end, including the only one that publishes
a measured false-positive rate against a human control corpus. Its per-category numbers are the
reason this release is shaped the way it is: on that corpus a rhythm-uniformity flag fired on
2.1 percent of human documents and 25.1 percent of machine ones, while a vocabulary ban fired
slightly more often on humans than on machines. So this release adds the rhythm measurement the
scanner never had, and stops a single filler word from failing a draft.

### Changed (breaking)

- **Vocabulary bans now fire in tiers rather than on sight.** A single `seamless`, `leverage`,
  `empower`, `robust framework`, or hedge no longer produces a finding. They fire when two or
  more land in one paragraph (`[tier 2]`), or when the whole document is saturated: at least
  three held hits and at least ten per thousand words (`[tier 2, N/1000]`). `journey` as a
  metaphor moved further, to tier 3, which fires only above three per thousand words. Anyone
  diffing output against 1.5.x will see hit counts drop on ordinary human prose, which is the
  point: a report that fires on one word choice gets closed before the reader reaches the
  fabricated quote on the next line.
- **`delve` was split out of the filler list and kept firing on sight**, under its own label
  `'delve'`. It is the one word on any published list with a real frequency gap and no innocent
  single use. Consumers matching the literal label `filler vocab` for it must update.
- **Output lines carry markers.** `[tier 2]`, `[tier 2, N/1000]`, `[tier 3, N/1000]`, `(1B)`,
  and `(P0)` now appear in the category field, and `rhythm uniformity` is a new whole-document
  line alongside the existing staccato line. Anything parsing scanner output needs updating. The
  subcommands, the exit-code contract, and the stdout/stderr split are unchanged.

### Added

- **Paste tells, marked `(P0)`.** Chat-interface residue: `citeturn...`, `oai_citation`,
  `contentReference[oaicite:N]`, `[attached_file:N]`, `grok_card`, `utm_source=chatgpt.com` and
  its siblings, `[Your Name]`, `[INSERT ...]`, `2026-XX-XX`. These are evidence rather than
  taste, so unlike every other pattern they fire inside quotations and blockquotes: a paste tell
  in a quotation proves the quotation was pasted without being read. Exempt only in code, so
  this repository can name them.
- **Rhythm dispersion.** Sentence-length variation measured as the ratio of standard deviation
  to mean, which is scale-free: a memo of short sentences has a small absolute spread for an
  innocent reason, and an absolute floor flagged one of this repo's own clean fixtures on
  exactly that mistake. Flags below a ratio of 0.40, or when 65 percent or more of sentences sit
  between 12 and 26 words. Needs at least 12 sentences to say anything, and is suppressed when
  the staccato run already fired, since both describe one document's rhythm and a report that
  bills a defect twice invites the reader to discount the rest of it.
- **A wordiness class, marked `(1B)`.** `utilize`, `in order to`, `a wide range of` at tier 2,
  and `due to the fact that` on sight. These fire on ordinary human professional prose and say
  nothing about how a text was produced, so they print under their own marker and must never be
  counted toward AI texture. Presenting a wordiness fix as authorship evidence is the error the
  marker exists to prevent.
- **Participial editorializing**: a trailing `-ing` clause that tells the reader what the fact
  they just read means (`, underscoring the importance of`). Restricted to the verbs that
  editorialize, so `, using the` and `, following the` stay clean.
- **Knowledge-gap speculation**: `while specific details are limited`, `is believed to have`,
  `maintains a low public profile`, `based on available information`. Under this skill's own
  never-inject rule these should have been a marked placeholder and a flagged gap, so naming
  them turns an invisible violation into a printed line.
- The `Reading the scan output` key in `references/taste-gate.md`, explaining what each marker
  means and what to do with it, with a shorter version in `SKILL.md`.

### Fixed

- **A backticked span broken across a hard wrap was scanned as prose.** `INLINE_CODE` never
  spans a newline and was applied only to the raw text, so the exemption missed any wrapped
  span. The skill instructs auditors to render every matched span in backticks, and in an
  eighty-column report a wrapped span is the normal case, not the edge case: audit reports were
  failing their own scan on the tells they were reporting. Inline code is now blanked per joined
  paragraph as well, where the wrap has become an ordinary space, guarded by an odd-backtick
  check so one stray backtick cannot exempt a paragraph.

### Tests

Twenty-eight to fifty-three. The twenty-eight from 1.5.1 pass unmodified. One fixture inside the
tier-3 density test was rewritten because its repetitive filler tripped the new rhythm check.
Its assertions are unchanged.

One eval fixture output changed: `audit-quote-defects-draft.md` goes from seventeen findings to
eighteen, gaining the rhythm flag at a ratio of 0.37 across sixteen sentences. It is the fixture
written to be slop, so this is coverage rather than a regression.

### Known margin

The dispersion threshold is tight. Across every fixture and this repository's own prose, clean
writing measures between 0.44 and 0.76 and the slop fixture measures 0.37, so 0.40 separates
them with less room than is comfortable. `references/taste-gate.md` itself sits at 0.44. Re-run
the self-scan after editing it, and do not move the threshold without new corpus evidence.

## 1.5.1 (2026-08-04)

Packaging and documentation only. No scanner behavior changed; the suite is unchanged at
twenty-eight tests, all passing.

### Added
- `skills/no-slop/LICENSE`, so the MIT claim in `SKILL.md` travels with the distributed skill
  instead of living only at the repo root.
- A ten-second opener in the skill readme: one AI-texture paragraph before and after, then a
  quotation welded from two real documents that a tell-hunting scanner reads as clean prose.
  Both examples are literal, and both are fenced, so the skill still passes its own scan
  without exempting itself.
- A **Testing** section naming `pytest` as a development dependency and stating what the
  scanner needs at runtime: the standard library, no network, no subprocess, no shell.

### Fixed
- The benchmark claim named a score with nothing in reach to check it against. It now points at
  `evals/` and `CHANGELOG.md` and invites a rerun. The copy of the readme inside the packaged
  skill, which ships without those directories, says so plainly rather than implying proof the
  reader does not have.

## 1.5.0 (2026-08-04)

### Added
- **Fourteen new tic patterns** covering the highest-frequency tells the scanner previously
  missed entirely: `a testament to`, `plays a crucial role`, `harness the power of`,
  `navigate the complexities`, era openers (`in an era of`, `in a world where`),
  `whether you're a ... or`, `it's no secret`, `look no further`, `let's dive in`, performed
  candor (`let's be honest`, `let's face it`, `real talk`, `here's the thing`), stock
  metaphors (`treasure trove`, `a beacon of`, `tapestry of`, `in the realm of`), and
  `unleash` plus `game-changing` in the filler set. A probe paragraph saturated with these
  scanned clean before this release.
- **Context-guarded enforcement of `unlock`, `journey`, and `robust`.** All three sat on the
  banned list while the scanner never flagged them. They now match only in their filler frames
  (`unlock the full potential`, `learning journey`, `robust framework`), so literal uses
  (unlocking a door, a journey home, robust standard errors) stay clean.
- **Curly single quotes are extracted by the quotes scan.** A closing mark followed by a word
  character is read as an apostrophe, so `the team's plan` never fabricates a span. A real
  quote set in curly singles previously checked nothing and exited 0, the worst kind of clean.
- **Ellipsis-elided quotes verify segment by segment.** A quote with an honest omission is a
  MATCH only when every segment around the ellipsis is verbatim in one source file, reported
  as `(elided)`. Segments found only across different files are a fusion and stay flagged.
  Legitimate elision previously reported PARTIAL, labeling correct quoting practice as
  probable paraphrase drift.
- **The manuscript is excluded from its own corpus.** Pointing `--corpus` at a directory
  containing the draft made every quote verify against itself.
- An eleventh eval, `elided-quote-and-fusion`: an honest elided quote and a curly-single quote
  that must verify, plus a planted cross-source fusion that must be caught. Adversarial in
  both directions.
- **Typographic apostrophes are folded to straight ones before matching.** Patterns are written
  with `'` and editors emit `'`, so on a draft out of Notion, Word or Docs the phrase set
  matched nothing. Six of the new patterns were dead on arrival on most real prose.
- **An elision that omits a negation is no longer a MATCH.** Every segment must be verbatim, in
  one file, in source order, and the check now reads what the ellipsis actually skipped in the
  source: `"we are ... planning any layoffs"` against a source saying "we are not planning any
  layoffs" is text-perfect and means the opposite. A gap holding a negation, or one under three
  words, reports PARTIAL and names what was cut. Ordering closes the same-file half of the
  fusion hole, which the cross-file eval never touched.
- **A paragraph with an odd number of double-quote marks is scanned in full**, and stderr names
  it. Blanking from a stray mark to whatever mark came next exempted prose that was never
  quoted; a silent exemption is worse than a false finding, because it never prints a line.
- Sixteen regression tests; the suite is now twenty-eight.
- The root readme documents the Claude Code marketplace install path, which shipped in 1.4.0
  without a mention anywhere.

### Fixed
- **Bold-opening paragraphs skipped paragraph joining.** The structural-line check read the
  `*` of `**bold**` as a list marker, so the 1.4.0 hard-wrap fix silently never applied to any
  paragraph opening with emphasis, and a wrapped cadence inside one was invisible. List
  markers now require the space markdown requires, which also stops a line starting with a
  bare number like `1.5` from reading as a list item.
- **A quotation wrapped across a hard line break lost its exemption.** Quoted-span blanking
  ran per line, so a banned phrase inside a wrapped quote was flagged, the exemption-side twin
  of the 1.4.0 matching fix. Blanking now runs per joined paragraph, where the wrap has become
  a space.
- **Structural lines rejoin their indented continuations.** A bullet is matched as one unit,
  so a cadence broken across a bullet's wrap is caught, and its short fragments never read as
  prose to the staccato check.
- The quotes scan prints one finding per line even when the quoted span wraps in the draft,
  keeping stdout to its parse contract.
- The zero-spans warning no longer implies curly quotes were skipped; both curly forms are
  extracted, and the warning now names the one true gap, straight single quotes.
- **A quotation span no longer crosses a paragraph break.** A lone elision apostrophe (`'em`)
  paired with a possessive two paragraphs later and reported a quotation the draft never
  contained, failing the fidelity gate on a piece that quotes nobody.
- **A curly single quote nested inside a double quote counts once.** Two result lines for one
  quotation padded the verified ratio the correction log rests on, exactly where a careful
  writer quotes a source quoting someone else.
- **A bold pseudo-heading no longer swallows the sentence after it.** The sentence splitter
  wanted `[.!?]` then whitespace, and `happens.**` has an asterisk in between, so a heading and
  the run beneath it merged into one long unit and the over-correction check lost the run.
- `plays a critical role`, the most common form of the phrase, was missing from that pattern.
- `harness the energy of the jet stream` and `harness the forces on the hull` are literal and
  now stay clean, guarded the same way `unlock`, `journey` and `robust` are. `let us be clear`
  is formal register and left the performed-candor list.
- SKILL.md and the scanner agree again about `unlock`, `journey` and `robust`. The doc listed
  all three flatly while the scanner context-guarded them, so the rewriting agent, which reads
  the doc and not the regexes, still stripped "unlock the door".
- CI's self-scan gate now includes `CHANGELOG.md` and `THIRD-PARTY-NOTICES.md`.

## 1.4.0 (2026-08-01)

First public release.

### Added
- Repository packaging for publication: MIT `LICENSE`, `THIRD-PARTY-NOTICES.md` crediting the
  Apache-2.0 material the narrative-tells section adapts, `.gitignore`, and a
  `.claude-plugin/marketplace.json` so one repo serves both the skills CLI and Claude Code.
- `tools/validate_skills.py`: validates frontmatter against the agent-skills spec (allowed
  keys, kebab-case name matching its directory, description length and angle brackets, body
  line count, dangling reference paths) and refuses content that trips registry security
  scanners. Runs in CI.
- CI that validates the spec, runs the tests, gates on the skill passing its own tic scan, and
  fails if any eval fixture referenced in `evals.json` is missing.
- Ten eval scenarios with real fixtures, three of them adversarial (over-correction,
  never-inject, academic register).
- Verdict criteria for SHIP, FIX THEN SHIP, and REWRITE, so two auditors reach the same call.
- Two stated carve-outs the scanner cannot make: factual contrast is not the banned cadence,
  and register beats the banned list where the venue requires it. Both must be justified in the
  report rather than silently suppressed.

### Fixed
- **Blockquoted quotes were invisible to the quotes scan.** A dead `continue` in
  `apply_exemptions` meant `code_only` also blanked blockquotes, so a fabricated epigraph, the
  highest-visibility quote in a piece, passed Gate 1 unchecked.
- **Hard-wrapped drafts evaded every multi-word pattern.** Tic matching now runs per paragraph
  rather than per line, so a cadence broken across a line wrap is caught.
- **I/O errors exited 1, the same code as findings.** A typo'd path read as "draft has
  findings" to any caller. Errors now exit 2.
- **The AI-smell required-fix threshold was inverted**, firing on clean prose and never on
  generated-sounding prose.
- **Abbreviations produced false staccato runs.** "Call Dr. Lee about it." split into
  fragments and failed the gate on ordinary prose.
- Audit reports now bind to the style rules and render matched text in backticks, so a report
  that removes a user's dashes cannot ship with four of its own.
- `It should be noted that` added to the throat-clearing pattern.
- Corpus matching is per file rather than one concatenated blob, so a quote cannot match across
  a file boundary, and the matching file is named in the output.
- Hidden directories are skipped when a corpus path is a directory, so pointing at a repo root
  no longer slurps git internals.
- Quote scanning now reports skipped short spans and warns when zero spans were extracted, so
  "nothing checked" no longer looks like "checked clean".
- Guidance moved from stdout to stderr; stdout is now a stable, parseable format.
- Tests no longer shell out through `subprocess` or use `exec_module`, both of which are
  registry-scanner keywords.

## 1.3.0 (2026-07-31)

- Exemption masking: fenced code, inline code, blockquotes, and quoted spans are blanked before
  the tic scan, preserving line offsets. Fixes the scanner flagging its own banned list.
- Over-correction guard: a rule plus a detector for runs of three or more very short sentences.
- Never-inject rewrite constraints with the provenance test and marked placeholders.
- The verify loop: re-scan your own output, capped at four passes.
- Recorded position on shareability against the rival "cut quotables" rule.

## 1.2.0 (2026-07-31)

- Description rebuilt to the trigger pattern with an explicit do-not-use clause.
- Progressive disclosure: gate procedures moved to `references/`.
- README and the first tests.

## 1.1.0 (2026-07-30)

- Narrative tells for fiction, with three of them added to the scanner.
- The reasons behind the banned patterns, and the contract-not-a-detector rule.

## 1.0.0 (2026-07-30)

- Initial build: two gates, two modes, the banned list, and the scanner.
