# Changelog

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
