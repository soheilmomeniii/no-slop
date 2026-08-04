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


def test_stock_ai_phrases_are_caught():
    text = ("This launch is a testament to the team. The API plays a crucial role and helps "
            "you harness the power of inference. Whether you're a founder or an engineer, you "
            "can navigate the complexities of deployment in an era of change. Let's face it, "
            "here's the thing: the market is a treasure trove, a beacon of hope in the realm "
            "of AI, a rich tapestry of use cases. It's no secret that shipping wins. Look no "
            "further. Let's dive in. We unlock the full potential of data on your learning "
            "journey with a robust framework to unleash growth in a world where speed wins.")
    got = labels(text)
    for expected in ("'a testament to'", "'plays a crucial role'", "'harness the power'",
                     "'whether you're a ... or'", "'navigate the complexities'", "era opener",
                     "performed candor", "stock metaphor", "'it's no secret'",
                     "'look no further'", "'let's dive in'", "unlock-the-potential",
                     "metaphorical journey", "robust-as-filler", "filler vocab"):
        assert expected in got, f"missing {expected}"


def test_context_guards_spare_literal_uses():
    text = ("She could not unlock the door with the bent key. The paper uses robust standard "
            "errors clustered by region. The journey home took eleven hours, and the harness "
            "on the lead horse had frayed.")
    assert labels(text) == set(), "literal uses must not be flagged"


def test_quote_exemption_survives_hard_wrap():
    """Regression: a banned cadence inside a hard-wrapped quotation is exempt,
    and --include-quoted still opts back in."""
    wrapped = 'The piece mocks lines like "this is not just a tool,\nbut a movement" at length.\n'
    path = _tmp(wrapped)
    assert run(["tics", path])[0] == 0
    code, out, _ = run(["tics", path, "--include-quoted"])
    assert code == 1 and "not X, but Y" in out


def test_bold_opening_paragraph_is_prose():
    """Regression: **bold** openers and bare numbers are prose, not structure,
    so a cadence wrapped inside such a paragraph is still caught."""
    code, out, _ = run(["tics", _tmp("**The pitch.** It is not just a tool,\nbut a movement.\n")])
    assert code == 1 and "not X, but Y" in out
    kinds = {structural for _, _, structural in sc.blocks("**Bold** start.\n1.5 million users.\n- a real bullet\n")}
    assert kinds == {False, True}


def test_single_curly_quotes_extracted_and_apostrophe_safe(tmp_path):
    corpus = tmp_path / "corpus.md"
    corpus.write_text("Rio wrote: Developers don't buy tools. They join defaults.")
    draft = tmp_path / "draft.md"
    draft.write_text("As Rio put it, \u2018Developers don\u2019t buy tools. They join defaults.\u2019 So build one.")
    code, out, _ = run(["quotes", str(draft), "--corpus", str(corpus)])
    assert "1 MATCH" in out and code == 0
    # Apostrophes alone must not fabricate an exempt span that hides a tell.
    assert "'not X, but Y' cadence" in labels("The team\u2019s plan isn\u2019t just a tool, but a movement.")


def test_elided_quote_matches_within_one_file(tmp_path):
    corpus = tmp_path / "corpus.md"
    corpus.write_text("Small teams ship faster because scope stays whole. Later on he added "
                      "that the incumbent had quoted a quarter for the same scope of work.")
    draft = tmp_path / "draft.md"
    draft.write_text('He said: "Small teams ship faster ... the incumbent had quoted a quarter '
                     'for the same scope of work."')
    code, out, _ = run(["quotes", str(draft), "--corpus", str(corpus)])
    assert "1 MATCH" in out and "(elided)" in out and code == 0


def test_elided_fusion_across_files_stays_flagged(tmp_path):
    """Segments that are only verbatim in different files are a fusion, not an
    elision, and must not report MATCH."""
    (tmp_path / "a.md").write_text("Small teams ship faster because scope stays whole.")
    (tmp_path / "b.md").write_text("The incumbent had quoted a quarter for the same scope of work.")
    draft = tmp_path / "draft.md"
    draft.write_text('He said: "Small teams ship faster ... the incumbent had quoted a quarter '
                     'for the same scope of work."')
    code, out, _ = run(["quotes", str(draft), "--corpus", str(tmp_path)])
    assert "0 MATCH" in out and code == 1


def test_bullet_fragments_do_not_read_as_staccato():
    doc = ("- **First check:** add primary material, or downgrade the claim to what you\n"
           "  can actually source.\n"
           "- **Second check:** add a case, or cut the abstraction entirely from\n"
           "  the whole section.\n"
           "- **Third check:** compress and vary rhythm across every paragraph of\n"
           "  the piece itself.\n")
    code, out, _ = run(["tics", _tmp(doc)])
    assert code == 0, f"bullet continuations read as staccato prose:\n{out}"


def test_typographic_apostrophes_are_folded_before_matching():
    """Regression: patterns are written with ' and editors emit ’, so the
    phrase set matched nothing on most real drafts."""
    curly = ("Let’s be honest, the market moved. It’s no secret that shipping wins. "
             "Let’s dive in.\n\nWhether you’re a founder or an engineer, here’s "
             "the thing: this is the customer’s journey.\n")
    code, curly_out, _ = run(["tics", _tmp(curly)])
    straight_code, straight_out, _ = run(["tics", _tmp(curly.replace("’", "'"))])
    assert code == 1 and straight_code == 1
    assert len(curly_out.splitlines()) == len(straight_out.splitlines())
    for expected in ("'it's no secret'", "performed candor", "'let's dive in'",
                     "'whether you're a ... or'", "metaphorical journey"):
        assert expected in curly_out, f"missing {expected} on curly apostrophes"


def test_odd_quote_mark_does_not_exempt_the_paragraph():
    """Regression: blanking moved from per line to per joined paragraph, which
    let one stray mark exempt everything up to the next mark."""
    doc = 'She said "we ship on Friday. It is not just a tool,\nbut a movement. Then he replied "done."\n'
    code, out, err = run(["tics", _tmp(doc)])
    assert code == 1 and "not X, but Y" in out
    assert "odd number of double-quote marks" in err


def test_bold_pseudo_heading_does_not_swallow_the_next_sentence():
    """Regression: the sentence splitter needed [.!?] then whitespace, so
    `happens.**` merged the heading with the run that follows it."""
    doc = "**Why the second draft is where the real work happens.**\n\nCut it. Then cut again. Ship.\n"
    code, out, _ = run(["tics", _tmp(doc)])
    assert code == 1 and "staccato run of 3" in out
    # The abbreviation rejoin must survive the looser split.
    assert sc.split_sentences("Call Dr. Lee. Then go.") == ["Call Dr. Lee.", "Then go."]


def test_elision_that_swallows_a_negation_is_not_a_match(tmp_path):
    """The inversion trick: every segment is verbatim and in order, and the
    quote still says the opposite of the source."""
    (tmp_path / "memo.md").write_text(
        "Our margins improved this quarter. We are not planning any layoffs at this time.")
    draft = tmp_path / "draft.md"
    draft.write_text('The CFO told staff: "Our margins improved this quarter ... we are ... '
                     'planning any layoffs at this time."')
    code, out, _ = run(["quotes", str(draft), "--corpus", str(tmp_path)])
    assert code == 1 and "0 MATCH" in out and "omits a negation" in out


def test_elided_segments_must_appear_in_source_order(tmp_path):
    """Reversing the source's sequence behind an ellipsis is a fusion, even
    when both segments live in the same file."""
    (tmp_path / "src.md").write_text(
        "Small teams ship faster because scope stays whole. Many paragraphs later, on a "
        "wholly unrelated topic, he added that the incumbent had quoted a quarter for the "
        "same scope of work.")
    draft = tmp_path / "draft.md"
    draft.write_text('He said: "the incumbent had quoted a quarter for the same scope of work '
                     '... small teams ship faster because scope stays whole."')
    code, out, _ = run(["quotes", str(draft), "--corpus", str(tmp_path)])
    assert code == 1 and "0 MATCH" in out


def test_quote_spans_never_cross_a_paragraph_break(tmp_path):
    """Regression: a lone elision apostrophe paired with a later possessive
    and reported a quotation the draft never contained."""
    (tmp_path / "src.md").write_text("Nothing relevant here at all.")
    draft = tmp_path / "draft.md"
    draft.write_text("Get ‘em while the market is hot.\n\n"
                     "The founders’ mandate was clear enough for everyone.\n")
    code, out, _ = run(["quotes", str(draft), "--corpus", str(tmp_path / "src.md")])
    assert code == 0 and "0 quoted span" in out


def test_nested_quote_is_counted_once(tmp_path):
    """A curly single quote inside a double quote is one quotation. Counting
    it twice pads the verified ratio the correction log rests on."""
    (tmp_path / "src.md").write_text(
        "Rio said the plan was dead and the team moved on to the next thing entirely.")
    draft = tmp_path / "draft.md"
    draft.write_text("He recalled: “Rio said ‘the plan was dead’ and the team "
                     "moved on to the next thing entirely.”")
    _, out, _ = run(["quotes", str(draft), "--corpus", str(tmp_path / "src.md")])
    assert "1 quoted span" in out


def test_guarded_phrases_spare_literal_uses_and_still_catch_the_frame():
    literal = ("Wind turbines harness the energy of the jet stream; sailors harness the "
               "forces acting on the hull. Let us be clear about the standard of proof.")
    assert labels(literal) == set()
    got = labels("You harness the power of AI. The gene plays a critical role.")
    assert "'harness the power'" in got and "'plays a crucial role'" in got


_TMPDIR = []


def _tmp(content):
    import tempfile
    d = tempfile.mkdtemp()
    _TMPDIR.append(d)
    p = Path(d) / "t.md"
    p.write_text(content)
    return str(p)
