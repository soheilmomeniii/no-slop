"""Tests for slop_check.py. Run: python -m pytest tests/ -q"""
import io
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
import slop_check as sc  # noqa: E402

SLOP = (
    "In today's rapidly evolving landscape, this isn't just a tool, but a movement. "
    "Her breath caught and she felt a surge of relief. Ultimately, we leverage synergies."
)
CLEAN = "The checkout rebuild took eleven days. The incumbent had quoted a quarter."


def run(argv):
    """Invoke the CLI in-process. Returns (exit_code, stdout, stderr)."""
    old, sys.argv = sys.argv, ["slop_check.py", *argv]
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = sc.main()
    finally:
        sys.argv = old
    return code, out.getvalue(), err.getvalue()


def labels(text):
    return {label for label, pat in sc.TIC_PATTERNS for _ in pat.finditer(text)}


def test_tics_catch_planted_tells():
    for expected in ("landscape opener", "'not X, but Y' cadence", "emotional choreography",
                     "named emotion", "recap marker", "leverage-as-verb"):
        assert expected in labels(SLOP), f"missing {expected}"


def test_tics_pass_clean_prose():
    assert labels(CLEAN) == set()


def test_should_be_noted_variant_is_caught():
    assert "'important to note'" in labels("It should be noted that attrition was higher.")


def test_exemptions_blank_code_and_quotes_preserving_lines():
    text = ('Line one is ordinary prose.\n'
            'The list bans "in today\'s rapidly evolving landscape" as an example.\n'
            '```\nWe leverage synergies here.\n```\n'
            '> Ultimately, a quoted blockquote.\n'
            'Use `leverage` as an identifier.\n')
    masked = sc.apply_exemptions(text)
    assert labels(masked) == set(), "exempt spans still flagged"
    assert len(masked.splitlines()) == len(text.splitlines()), "line offsets shifted"
    assert "landscape opener" in labels(sc.apply_exemptions(text, include_quoted=True))


def test_code_only_keeps_blockquotes_visible():
    """Regression: a blockquoted epigraph must stay visible to the quotes scan."""
    text = '> "Developers do not buy tools. They join defaults."\n\n`code` here.\n'
    kept = sc.apply_exemptions(text, code_only=True)
    assert "Developers do not buy tools" in kept
    assert "code" not in kept


def test_tics_catch_cadence_across_a_hard_wrap():
    """Regression: hard-wrapped drafts must not hide a multi-word cadence."""
    wrapped = "This is not just a tool,\nbut a movement that people want.\n"
    code, out, _ = run(["tics", _tmp(wrapped)])
    assert code == 1 and "not X, but Y" in out


def test_staccato_flags_runs_and_ignores_lists_and_abbreviations():
    assert sc.staccato_run("Ship it. Then measure. Nothing else matters.")[0] >= 3
    assert sc.staccato_run("- short one\n- short two\n- short three\n")[0] == 0
    assert sc.staccato_run(CLEAN)[0] == 0
    prose = ("Call Dr. Lee about the follow-up. Then ask Mr. Ray for the archived "
             "consent forms. The registry closes on Friday.")
    assert sc.staccato_run(prose)[0] == 0, "abbreviations split into fake fragments"


def test_skill_files_pass_their_own_scan():
    targets = [str(SKILL / "SKILL.md"), str(SKILL / "README.md"),
               *[str(p) for p in sorted((SKILL / "references").glob("*.md"))]]
    code, out, _ = run(["tics", *targets])
    assert code == 0, f"the skill fails its own rules:\n{out}"


def test_quotes_match_and_none(tmp_path):
    corpus = tmp_path / "corpus.md"
    corpus.write_text("He wrote: Developers don't buy tools. They join defaults.")
    draft = tmp_path / "draft.md"
    draft.write_text('A: "Developers don\'t buy tools. They join defaults." '
                     'B: "This quote exists nowhere in the corpus at all."')
    code, out, _ = run(["quotes", str(draft), "--corpus", str(corpus)])
    assert "1 MATCH" in out and "1 NONE" in out and "corpus.md" in out
    assert code == 1


def test_quotes_sees_blockquoted_epigraph(tmp_path):
    corpus = tmp_path / "corpus.md"
    corpus.write_text("Developers don't buy tools. They join defaults.")
    draft = tmp_path / "draft.md"
    draft.write_text('> "Developers don\'t buy tools. They join defaults."\n\nBody text.\n')
    code, out, _ = run(["quotes", str(draft), "--corpus", str(corpus)])
    assert "1 MATCH" in out and code == 0


def test_exit_codes(tmp_path):
    bad, good = tmp_path / "bad.md", tmp_path / "good.md"
    bad.write_text(SLOP)
    good.write_text(CLEAN)
    assert run(["tics", str(bad)])[0] == 1
    assert run(["tics", str(good)])[0] == 0
    code, _, err = run(["tics", str(tmp_path / "missing.md")])
    assert code == 2 and "slop_check:" in err, "a missing file must not read as findings"


def test_stdout_stays_machine_readable(tmp_path):
    """Guidance belongs on stderr so stdout can be parsed by a caller."""
    corpus = tmp_path / "corpus.md"
    corpus.write_text("nothing relevant here")
    draft = tmp_path / "draft.md"
    draft.write_text('X: "A line that appears in no source document whatsoever."')
    _, out, err = run(["quotes", str(draft), "--corpus", str(corpus)])
    assert "PARTIAL = likely" not in out and "PARTIAL = likely" in err
    for line in [l for l in out.splitlines() if l.startswith("[")]:
        assert line.split("]")[0].strip("[ ") in {"MATCH", "PARTIAL", "NONE"}


_TMPDIR = []


def _tmp(content):
    import tempfile
    d = tempfile.mkdtemp()
    _TMPDIR.append(d)
    p = Path(d) / "t.md"
    p.write_text(content)
    return str(p)
