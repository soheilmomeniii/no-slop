#!/usr/bin/env python3
"""slop_check.py: mechanical scans for the no-slop skill.

Subcommands:

  tics    Scan files for banned AI tells (dashes, phrases, cadences) plus the
          staccato check that catches over-corrected, humanizer-flavored prose.
  quotes  Extract quoted spans from a manuscript and match them against a
          source corpus (normalized), reporting MATCH / PARTIAL / NONE.

Exit codes are the parse contract: 0 clean, 1 findings present, 2 error.
Findings go to stdout, one per line. Guidance and diagnostics go to stderr, so
stdout stays machine-readable:

  tics    <path>:<line> | <category> | <matched text>
  quotes  [<STATUS>] "<span>"   then a summary line

Both scans blank exempt spans before matching (fenced code, inline code, and
for tics also blockquotes and quoted text), replacing characters with spaces so
line offsets stay valid. Without this the scanner flags its own documentation
and any draft that quotes bad writing on purpose.

Tic patterns are matched per paragraph rather than per line, because a
hard-wrapped draft would otherwise hide any cadence that spans a line break.

The script finds candidates; it does not assign fidelity verdicts. Every
non-MATCH needs human review (nested quotes, curly quotes, and HTML-escaped
corpus text produce false flags).
"""

import argparse
import html
import re
import sys
import unicodedata
from pathlib import Path

# ---------------------------------------------------------- exemptions ----

FENCED_CODE = re.compile(r"^ {0,3}```.*?(?:^ {0,3}```|\Z)", re.M | re.S)
BLOCKQUOTE_LINE = re.compile(r"^ {0,3}>.*$", re.M)
INLINE_CODE = re.compile(r"`[^`\n]+`")
# Deliberately never spans a newline: one unclosed quote would otherwise blank
# the rest of the document and silently exempt it.
QUOTED_SPAN = re.compile(r"[“\"][^“”\"\n]{1,600}[”\"]")


def _blank(m):
    """Replace every visible character with a space, preserving newlines."""
    return re.sub(r"[^\n]", " ", m.group(0))


def apply_exemptions(text, include_quoted=False, code_only=False):
    """Blank spans the scanner must ignore.

    code_only=True blanks code alone, leaving blockquotes and quotations
    visible. The quotes scan needs that: a blockquoted epigraph is the
    highest-visibility quote in a piece and must still be verified.
    """
    for pat in (FENCED_CODE, INLINE_CODE):
        text = pat.sub(_blank, text)
    if code_only:
        return text
    text = BLOCKQUOTE_LINE.sub(_blank, text)
    if not include_quoted:
        text = QUOTED_SPAN.sub(_blank, text)
    return text


# ---------------------------------------------------------------- tics ----

TIC_PATTERNS = [
    ("em dash", re.compile(r"—|―|(?<=\w)--(?=\w)|(?<=\w)--(?=\s)|\s--\s")),
    ("spaced en dash (em-dash substitute)", re.compile(r"\s–\s")),
    ("landscape opener", re.compile(r"in today'?s [\w\s,-]{0,40}(landscape|world|environment|era)", re.I)),
    ("'this piece explores'", re.compile(r"this (chapter|article|post|essay|piece|guide|section) (explores|examines|delves|dives)", re.I)),
    ("'important to note'", re.compile(r"it should be (noted|mentioned|pointed out)|it('| i)s (important|worth) (to (note|mention|point out)|noting|mentioning)", re.I)),
    ("'excited to announce'", re.compile(r"(we|i)('re| are| am|'m) (thrilled|excited|proud) to (announce|share|introduce)", re.I)),
    ("'not X, but Y' cadence", re.compile(r"(?:\bnot|n['’]t)\s+(?:just\s+|only\s+|merely\s+)?[\w\s'-]{1,30}, but [\w\s'-]{1,30}", re.I)),
    ("'Not X. It is Y.' cadence", re.compile(r"(?:\bnot|n['’]t)\s+[\w\s'-]{1,30}[.;] (it is|it's|this is)\b", re.I)),
    ("'not just X, it's Y' cadence", re.compile(r"(?:\bnot|n['’]t)\s+(?:just|only|merely)\s+[\w\s'-]{1,30}, (it's|it is|this is)\b", re.I)),
    ("'That is' opener", re.compile(r"(?:(?<=[.!?] )|^)That is,?\s", re.M)),
    ("'By understanding X...'", re.compile(r"\bby understanding [\w\s'-]{1,40}, (you|we|readers|founders|teams)\b", re.I)),
    ("hedge", re.compile(r"\b(arguably|in many ways|to some extent|one could argue)\b", re.I)),
    ("recap marker", re.compile(r"(?:(?<=[.!?] )|^)(in short|ultimately|at the end of the day|in conclusion)\b", re.I | re.M)),
    ("filler vocab", re.compile(r"\b(delve|delves|delving|unpack(?:ing)?|game.?changer|deep.?dive|seamless(?:ly)?|supercharge[ds]?|empower(?:ing|s)?|elevate[sd]?)\b", re.I)),
    ("leverage-as-verb", re.compile(r"\bleverag(e[sd]?|ing)\b", re.I)),
    ("emotional choreography", re.compile(r"\b(breath (caught|catches|catching|hitched)|jaw (clenched|clenching|tightened)|stomach (dropped|drops|churned|twisted)|heart (hammered|hammering|pounded|pounding|raced|racing))\b", re.I)),
    ("named emotion", re.compile(r"\bfelt a (surge|wave|pang|rush|flicker|flash) of \w+", re.I)),
    ("tidy realization ending", re.compile(r"\bfor the first time,? (i|she|he|they) (truly )?(understood|realized|saw|felt)\b", re.I)),
]

SKIP_LINE = re.compile(r"^\s*(?:[-*+>#|]|\d+[.)])")


def blocks(text):
    """Yield (start_line, scannable_text).

    Running prose is joined per paragraph so a cadence broken across a hard
    wrap is still matched. Structural lines (list items, headings, tables) are
    emitted individually so their line numbers stay exact.
    """
    out, buf, start = [], [], None
    for i, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            if buf:
                out.append((start, " ".join(buf)))
            buf, start = [], None
            continue
        if SKIP_LINE.match(line):
            if buf:
                out.append((start, " ".join(buf)))
                buf, start = [], None
            out.append((i, line))
            continue
        if start is None:
            start = i
        buf.append(line.strip())
    if buf:
        out.append((start, " ".join(buf)))
    return out


# ------------------------------------------------------------ staccato ----
# Over-correction check. Scrubbing slop at maximum strictness produces a second
# fingerprint: fragments, forced punch endings, every hedge stripped. Runs of
# very short sentences are the mechanical signature of that failure.

UNIT_SPLIT = re.compile(r"(?<=[.!?])\s+")
WORD = re.compile(r"[\w'’]+")
ABBREV_END = re.compile(r"\b(?:mr|mrs|ms|dr|prof|st|jr|sr|no|fig|vs|cf|etc|al|e\.g|i\.e)\.$", re.I)


def split_sentences(text):
    """Split on terminators, re-joining units that end in a known abbreviation
    so 'Call Dr. Lee.' is one sentence rather than two fragments."""
    parts, buf = [], ""
    for piece in UNIT_SPLIT.split(text):
        buf = f"{buf} {piece}".strip() if buf else piece
        if not ABBREV_END.search(buf):
            parts.append(buf)
            buf = ""
    if buf:
        parts.append(buf)
    return parts


def prose_lines(text):
    """Lines of running prose: lists, headings, tables, and their wrapped
    continuation lines are dropped, because short bullets are legitimate
    structure rather than over-correction."""
    out, in_block = [], False
    for line in text.splitlines():
        if not line.strip():
            in_block = False
            continue
        if SKIP_LINE.match(line):
            in_block = True
            continue
        if in_block and line[:1] in (" ", "\t"):
            continue
        in_block = False
        out.append(line)
    return out


def staccato_run(text, max_words=5, min_run=3):
    """Longest run of consecutive short sentences, the over-correction tell."""
    units = [u.strip() for u in split_sentences(" ".join(prose_lines(text))) if u.strip()]
    best, best_units, run, cur = 0, [], 0, []
    for u in units:
        n = len(WORD.findall(u))
        if 0 < n <= max_words:
            run += 1
            cur.append(u)
            if run > best:
                best, best_units = run, list(cur)
        else:
            run, cur = 0, []
    return (best, best_units) if best >= min_run else (0, [])


def scan_tics(paths, include_quoted=False):
    hits = 0
    for p in paths:
        raw = Path(p).read_text(encoding="utf-8", errors="replace")
        text = apply_exemptions(raw, include_quoted=include_quoted)
        for lineno, chunk in blocks(text):
            for label, pat in TIC_PATTERNS:
                for m in pat.finditer(chunk):
                    hits += 1
                    print(f"{p}:{lineno} | {label} | {m.group(0).strip()!r}")
        run, units = staccato_run(text)
        if run:
            hits += 1
            print(f"{p} | over-correction (staccato run of {run}) | "
                  f"{' / '.join(units[:4])!r}")
    print(f"\n{hits} tic(s) found." if hits else "Clean: 0 tics found.")
    return 1 if hits else 0


# -------------------------------------------------------------- quotes ----

QUOTE_RE = re.compile(r'[“"]([^“”"]{12,600})[”"]')


def normalize(s: str) -> str:
    s = html.unescape(s)
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.lower()
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def corpus_files(corpus: str):
    """Normalized text per source file, so a quote cannot false-match across a
    file boundary and so the matching file can be named in the correction log."""
    path = Path(corpus)
    if path.is_file():
        return {path.name: normalize(path.read_text(encoding="utf-8", errors="replace"))}
    out = {}
    for f in sorted(path.rglob("*")):
        if any(part.startswith(".") for part in f.relative_to(path).parts):
            continue  # skip .git and other hidden trees
        if f.is_file() and f.suffix.lower() in {".md", ".txt", ".html", ".json", ".csv", ""}:
            out[str(f.relative_to(path))] = normalize(f.read_text(encoding="utf-8", errors="replace"))
    return out


def scan_quotes(manuscript: str, corpus: str, min_words: int) -> int:
    raw = Path(manuscript).read_text(encoding="utf-8", errors="replace")
    # Code only: blockquoted epigraphs are the highest-visibility quotes in a
    # piece, so they must stay visible to this scan.
    text = apply_exemptions(raw, code_only=True)
    corp = corpus_files(corpus)
    if not corp:
        print(f"slop_check: no readable corpus files under {corpus}", file=sys.stderr)
        return 2
    spans = [m.group(1) for m in QUOTE_RE.finditer(text)]
    results = {"MATCH": 0, "PARTIAL": 0, "NONE": 0}
    skipped = 0
    for span in spans:
        norm = normalize(span)
        words = norm.split()
        if len(words) < min_words:
            skipped += 1
            continue
        status, where = "NONE", ""
        for name, body in corp.items():
            if norm in body:
                status, where = "MATCH", name
                break
        if status == "NONE":
            win = min(6, len(words))
            windows = [" ".join(words[i:i + win]) for i in range(0, max(1, len(words) - win + 1))]
            for name, body in corp.items():
                if any(w in body for w in windows):
                    status, where = "PARTIAL", name
                    break
        results[status] += 1
        short = span if len(span) <= 90 else span[:87] + "..."
        suffix = f"  <- {where}" if where else ""
        print(f"[{status:7}] “{short}”{suffix}")
    total = sum(results.values())
    print(f"\n{total} quoted span(s) >= {min_words} words: "
          f"{results['MATCH']} MATCH / {results['PARTIAL']} PARTIAL / {results['NONE']} NONE")
    if skipped:
        print(f"slop_check: {skipped} span(s) shorter than {min_words} words were not checked.",
              file=sys.stderr)
    if total == 0:
        print("slop_check: no quoted spans extracted. If this draft uses single quotes or "
              "curly quotes the scan checked nothing; verify by hand.", file=sys.stderr)
    if results["PARTIAL"] or results["NONE"]:
        print("PARTIAL = likely silent paraphrase drift; NONE = unverified or fabricated. "
              "Manually review every non-MATCH before assigning a verdict "
              "(nested quotes / curly quotes / HTML escapes cause false flags).",
              file=sys.stderr)
    return 1 if (results["PARTIAL"] or results["NONE"]) else 0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tics", help="scan for banned AI tells and over-correction")
    t.add_argument("files", nargs="+")
    t.add_argument("--include-quoted", action="store_true",
                   help="also scan inside quoted spans (default: exempt)")
    q = sub.add_parser("quotes", help="match quoted spans against a corpus")
    q.add_argument("manuscript")
    q.add_argument("--corpus", required=True)
    q.add_argument("--min-words", type=int, default=4)
    args = ap.parse_args()
    try:
        if args.cmd == "tics":
            return scan_tics(args.files, include_quoted=args.include_quoted)
        return scan_quotes(args.manuscript, args.corpus, args.min_words)
    except OSError as e:
        print(f"slop_check: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
