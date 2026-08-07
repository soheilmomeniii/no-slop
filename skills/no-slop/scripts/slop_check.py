#!/usr/bin/env python3
"""slop_check.py: mechanical scans for the no-slop skill.

Subcommands:

  tics    Scan files for banned AI tells (dashes, phrases, cadences) plus the
          staccato check that catches over-corrected, humanizer-flavored prose.
  quotes  Extract quoted spans from a manuscript and match them against a
          source corpus (normalized), reporting MATCH / PARTIAL / NONE.
          Double quotes (straight or curly) and curly single quotes are both
          extracted; straight single quotes never are, because apostrophes
          make them unrecoverable by pattern. A quote elided with an ellipsis
          is a MATCH only when every segment around the ellipsis is verbatim
          in one source file; segments found only across different files are
          a fusion and stay flagged.

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
# the rest of the document and silently exempt it. Wrapped quotes are still
# handled, because the tic scan re-applies this per joined paragraph, where a
# hard wrap has become an ordinary space.
QUOTED_SPAN = re.compile(r"[“\"][^“”\"\n]{1,600}[”\"]")
# Curly single quotes only. The closing mark must not be followed by a word
# character, which is what separates a closing quote from an apostrophe
# (the team’s plan). Straight single quotes are never treated as quotes:
# plurals and decades ('80s) make them unrecoverable by pattern.
SINGLE_QUOTED_SPAN = re.compile(r"‘[^‘\n]{1,600}?’(?!\w)")


def _blank(m):
    """Replace every visible character with a space, preserving newlines."""
    return re.sub(r"[^\n]", " ", m.group(0))


def fold_apostrophes(text):
    """Rewrite the typographic apostrophe as a straight one, same length.

    Editors emit ’ by default, so patterns written with ' silently matched
    nothing on most real drafts. Folding once here means every pattern can be
    written with a plain apostrophe and still catch both forms, and character
    offsets are preserved so line numbers and blanking stay exact. The curly
    quote scans run before this, on the unfolded text, because they need ’ to
    tell a closing quote from an apostrophe.
    """
    return text.replace("’", "'")


DOUBLE_MARK = re.compile(r"[“”\"]")


def unbalanced_doubles(text):
    """True when a chunk holds an odd number of double-quote marks.

    Blanking such a chunk would run from the stray mark to whatever mark comes
    next, exempting prose that was never quoted. The old per-line rule bounded
    that damage to one line; joining paragraphs removed the bound.
    """
    return len(DOUBLE_MARK.findall(text)) % 2 == 1


BACKTICK = re.compile(r"`")


def unbalanced_backticks(text):
    """True when a chunk holds an odd number of backticks.

    Re-applying the inline-code exemption to a joined paragraph would
    otherwise run from a stray backtick to whatever backtick comes next,
    exempting prose that was never code. Same reasoning as
    unbalanced_doubles: a missed tic is better than a silent exemption.
    """
    return len(BACKTICK.findall(text)) % 2 == 1


def blank_inline_code(text):
    """Blank inline code within one joined paragraph.

    INLINE_CODE never spans a newline, so a backticked span broken across a
    hard wrap survived the full-text pass and was scanned as prose. After
    joining, the wrap has become an ordinary space and the pattern matches.
    The skill instructs auditors to render every matched span in backticks,
    so a wrapped backticked span in an eighty-column report is the normal
    case, not the edge case.
    """
    if unbalanced_backticks(text):
        return text
    return INLINE_CODE.sub(_blank, text)


def blank_quoted(text):
    """Blank double- and single-curly-quoted spans within one paragraph.

    A chunk with an odd number of double-quote marks is left alone: silently
    exempting real prose is the worse failure, since an exemption hides tics
    without ever printing a line.
    """
    if not unbalanced_doubles(text):
        text = QUOTED_SPAN.sub(_blank, text)
    return SINGLE_QUOTED_SPAN.sub(_blank, text)


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
        text = blank_quoted(text)
    return text


# --------------------------------------------------------- paste tells ----
# Mechanical residue of an unedited paste from a chat interface. Unlike every
# other pattern here, these are evidence rather than taste: their presence
# proves the text was moved out of a tool without being read, whatever the
# prose around them reads like. They therefore fire inside quotations and
# blockquotes too, and are exempt only inside code, so this file and the
# skill's own documentation can name them.

PASTE_TELLS = [
    ("chat citation markup", re.compile(r"citeturn\d+\w*|oai_citation|contentReference\[oaicite:\d+\]|\[attached_file:\d+\]|grok_card")),
    ("AI referrer URL parameter", re.compile(r"utm_source=(?:chatgpt\.com|claude\.ai|perplexity\.ai)|referrer=grok\.com", re.I)),
    ("unfilled placeholder", re.compile(r"\[Your Name\]|\[INSERT [A-Z][A-Z ]*\]|\b\d{4}-XX-XX\b")),
]


# ---------------------------------------------------------------- tics ----

# Every entry is (label, pattern, tier). The tier is when the pattern fires,
# not how bad it is.
#
#   1  on sight. Cadences, dashes, stock flourishes: constructions that carry
#      no content and have no innocent reading at any density.
#   2  only when two or more tier-2 hits land in one paragraph. Ordinary words
#      used as filler. One `seamless` in a page is a word choice; two in a
#      paragraph is a texture. Measurement on published corpora finds
#      vocabulary bans fire about as often on human prose as on machine prose,
#      so firing them singly spends the reader's trust for nothing.
#   3  only above three hits per thousand words. Reserved for words common
#      enough that only their density is evidence.
#
# Demoting a pattern never means the word is fine. It means a single instance
# is not proof, and a report that cries wolf on one `robust framework` gets
# closed before the reader reaches the fabricated quote on the next line.

TIC_PATTERNS = [
    ("em dash", re.compile(r"—|―|(?<=\w)--(?=\w)|(?<=\w)--(?=\s)|\s--\s"), 1),
    ("spaced en dash (em-dash substitute)", re.compile(r"\s–\s"), 1),
    ("landscape opener", re.compile(r"in today'?s [\w\s,-]{0,40}(landscape|world|environment|era)", re.I), 1),
    ("'this piece explores'", re.compile(r"this (chapter|article|post|essay|piece|guide|section) (explores|examines|delves|dives)", re.I), 1),
    ("'important to note'", re.compile(r"it should be (noted|mentioned|pointed out)|it('| i)s (important|worth) (to (note|mention|point out)|noting|mentioning)", re.I), 1),
    ("'excited to announce'", re.compile(r"(we|i)('re| are| am|'m) (thrilled|excited|proud) to (announce|share|introduce)", re.I), 1),
    ("'not X, but Y' cadence", re.compile(r"(?:\bnot|n['’]t)\s+(?:just\s+|only\s+|merely\s+)?[\w\s'-]{1,30}, but [\w\s'-]{1,30}", re.I), 1),
    ("'Not X. It is Y.' cadence", re.compile(r"(?:\bnot|n['’]t)\s+[\w\s'-]{1,30}[.;] (it is|it's|this is)\b", re.I), 1),
    ("'not just X, it's Y' cadence", re.compile(r"(?:\bnot|n['’]t)\s+(?:just|only|merely)\s+[\w\s'-]{1,30}, (it's|it is|this is)\b", re.I), 1),
    ("'That is' opener", re.compile(r"(?:(?<=[.!?] )|^)That is,?\s", re.M), 1),
    ("'By understanding X...'", re.compile(r"\bby understanding [\w\s'-]{1,40}, (you|we|readers|founders|teams)\b", re.I), 1),
    ("hedge", re.compile(r"\b(arguably|in many ways|to some extent|one could argue)\b", re.I), 2),
    ("recap marker", re.compile(r"(?:(?<=[.!?] )|^)(in short|ultimately|at the end of the day|in conclusion)\b", re.I | re.M), 1),
    # Split out of the filler list and kept at tier 1 deliberately. Of every
    # word on any published list this is the one with a real gap between how
    # often a model reaches for it and how often a person does, and no
    # innocent register uses it once by accident.
    ("'delve'", re.compile(r"\b(delve|delves|delved|delving)\b", re.I), 1),
    ("filler vocab", re.compile(r"\b(unpack(?:ing)?|game.?chang(?:er|ing)|deep.?dive|seamless(?:ly)?|supercharge[ds]?|empower(?:ing|s)?|elevate[sd]?|unleash(?:es|ed|ing)?)\b", re.I), 2),
    ("leverage-as-verb", re.compile(r"\bleverag(e[sd]?|ing)\b", re.I), 2),
    ("'a testament to'", re.compile(r"\ba testament to\b", re.I), 1),
    ("'plays a crucial role'", re.compile(r"\bplay(?:s|ed|ing)? an? (?:crucial|critical|pivotal|vital|key|significant|essential|integral) role\b", re.I), 1),
    # Guarded like unlock and robust: the abstract object is the tell, so
    # turbines that harness the energy of the jet stream stay clean.
    # Guarded like unlock and robust: the abstract object is the tell. Turbines
    # that harness the energy of the jet stream, and sailors who harness the
    # forces on a hull, stay clean.
    ("'harness the power'", re.compile(r"\bharness(?:es|ing)? the (?:power|potential|full potential|magic|collective \w+) of\b", re.I), 1),
    ("'navigate the complexities'", re.compile(r"\bnavigat(?:e|es|ing) the (?:complexit|landscape|challenge|world of|waters of|intricac|nuances|ever.chang)", re.I), 1),
    ("era opener", re.compile(r"\bin an era (?:of|where|when|defined by|marked by)\b|\bin a world where\b", re.I), 1),
    ("'whether you're a ... or'", re.compile(r"\bwhether you(?:'| a)re an? [\w\s',-]{1,40}? or an? \w", re.I), 1),
    ("'it's no secret'", re.compile(r"\bit(?:'| i)s no secret\b", re.I), 1),
    ("'look no further'", re.compile(r"\blook no further\b", re.I), 1),
    # "let us be clear" is ordinary formal register in legal and academic
    # writing, so it is not in this list. The others perform candor instead of
    # showing it.
    ("performed candor", re.compile(r"\blet(?:'| u)s (?:be (?:honest|real)|face it)\b|\breal talk\b|\bhere(?:'| i)s the (?:thing|kicker|catch)\b", re.I), 1),
    ("'let's dive in'", re.compile(r"\blet(?:'| u)s dive (?:in|into|right in|deeper)\b|\bdive into the world of\b", re.I), 1),
    ("stock metaphor", re.compile(r"\btreasure trove\b|\ba beacon of\b|\b(?:rich )?tapestry of\b|\bin the realm of\b", re.I), 1),
    ("unlock-the-potential", re.compile(r"\bunlock(?:s|ing|ed)? (?:the |your |its |their |a |new )?(?:full |true |real |hidden |untapped )?(?:potential|power|value|growth|insight|opportunit|possibilit|secret|benefit|capabilit)", re.I), 1),
    ("metaphorical journey", re.compile(r"\b(?:learning|customer|user|personal|digital|transformation|entrepreneurial|startup|brand|wellness|fitness|career|writing|reading)(?:'s)? journey\b|\bjourney (?:of (?:self.)?discovery|to becoming|toward|towards)\b", re.I), 3),
    ("robust-as-filler", re.compile(r"\brobust (?:framework|solution|approach|strateg|foundation|understanding|suite|ecosystem|pipeline|toolkit|set of)", re.I), 2),
    ("emotional choreography", re.compile(r"\b(breath (caught|catches|catching|hitched)|jaw (clenched|clenching|tightened)|stomach (dropped|drops|churned|twisted)|heart (hammered|hammering|pounded|pounding|raced|racing))\b", re.I), 1),
    ("named emotion", re.compile(r"\bfelt a (surge|wave|pang|rush|flicker|flash) of \w+", re.I), 1),
    ("tidy realization ending", re.compile(r"\bfor the first time,? (i|she|he|they) (truly )?(understood|realized|saw|felt)\b", re.I), 1),
    # A trailing -ing clause that tells the reader what the fact they just
    # read means. The fix is always the same: cut everything after the fact.
    # Restricted to the verbs that do the editorializing, because ", using
    # the" and ", following the" are ordinary subordination.
    ("participial editorializing", re.compile(r",\s+(?:highlight|underscor|underlin|emphasiz|showcas|reflect|signal|solidify|cement|reinforc|demonstrat|illustrat|mark|ensur|cap)(?:ing|ying)\s+(?:its|their|his|her|the|a|an|what|how|why|broader|continued|why)\b", re.I), 1),
    # Hedged non-knowledge dressed as reporting. Under this skill's own
    # never-inject rule these sentences should have been a marked placeholder
    # and a flagged gap, so naming them turns an invisible violation into a
    # printed line.
    ("knowledge-gap speculation", re.compile(r"\b(?:while |although )?(?:specific |exact |further )?details (?:are|remain) (?:limited|scarce|sparse|unclear|not (?:widely |publicly )?(?:available|documented|disclosed))|\bbased on (?:the )?available information\b|\bis believed to have\b|\b(?:maintains|keeps) an? (?:relatively )?low (?:public )?profile\b|\blikely began (?:his|her|their) career\b|\bnot (?:widely|publicly) (?:documented|disclosed|available)\b", re.I), 1),
    # 1B: wordiness, not authorship evidence. See WORDINESS_LABELS.
    ("wordy: 'utilize'", re.compile(r"\butiliz(?:e|es|ed|ing|ation)\b", re.I), 2),
    ("wordy: 'in order to'", re.compile(r"\bin order to\b", re.I), 2),
    ("wordy: 'a wide range of'", re.compile(r"\ba (?:wide|broad|diverse|vast) (?:range|array|variety) of\b", re.I), 2),
    ("wordy: 'due to the fact that'", re.compile(r"\bdue to the fact that\b", re.I), 1),
]

# Tier 1A versus 1B. Everything above is a texture judgment except these,
# which are ordinary wordiness: they fire on perfectly human professional
# prose and say nothing about how the text was produced. They print under
# their own marker and must never be counted as evidence of authorship.
# Presenting a wordiness fix as authorship evidence is the error this split
# exists to prevent.
WORDINESS_LABELS = {
    "wordy: 'utilize'",
    "wordy: 'in order to'",
    "wordy: 'a wide range of'",
    "wordy: 'due to the fact that'",
}


def mark(label):
    return f"{label} (1B)" if label in WORDINESS_LABELS else label

# A list marker needs the space that markdown requires after it, so a
# paragraph opening with **bold** or *italic*, or a line starting with a bare
# number like 1.5, is prose rather than structure. Without the space rule,
# every bold-opening paragraph skipped paragraph joining, which quietly
# re-opened the hard-wrap hole for exactly those paragraphs.
SKIP_LINE = re.compile(r"^\s*(?:[-*+]\s|[>#|]|\d+[.)]\s)")


def blocks(text):
    """Yield (start_line, scannable_text, structural).

    Running prose is joined per paragraph so a cadence broken across a hard
    wrap is still matched. A structural line (list item, heading, table row)
    is joined with its indented continuation lines and flagged structural, so
    a full bullet is matched as one unit but its short fragments never read
    as prose to the staccato check.
    """
    out, buf, start, structural = [], [], None, False

    def flush():
        nonlocal buf, start, structural
        if buf:
            out.append((start, " ".join(buf), structural))
        buf, start, structural = [], None, False

    for i, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            flush()
            continue
        if SKIP_LINE.match(line):
            flush()
            buf, start, structural = [line.strip()], i, True
            continue
        if structural and line[:1] in (" ", "\t"):
            buf.append(line.strip())
            continue
        if structural:
            flush()
        if start is None:
            start = i
        buf.append(line.strip())
    flush()
    return out


# ------------------------------------------------------------ staccato ----
# Over-correction check. Scrubbing slop at maximum strictness produces a second
# fingerprint: fragments, forced punch endings, every hedge stripped. Runs of
# very short sentences are the mechanical signature of that failure.

# Markup may sit between the terminator and the space: a bold pseudo-heading
# ends `happens.**`, a parenthetical ends `(so far).`, a quotation ends `done."`
# Without this, the heading swallows the sentence after it and a staccato run
# hides inside the merged unit.
UNIT_SPLIT = re.compile(r"(?<=[.!?])[*_)\]”\"’']*\s+")
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


# ------------------------------------------------------------- dispersion ---
# The other half of the over-correction check, and the one with the strongest
# evidence behind it. Published measurement across human and machine corpora
# finds vocabulary bans separate the two barely at all, while rhythm
# uniformity separates them well: on one published corpus a uniformity flag
# fired on 2.1 percent of human documents and 25.1 percent of machine ones.
# The staccato run catches prose scrubbed too short. This catches prose that
# never varies: a document whose sentences all sit in the mid-length band with
# little spread reads machine-stamped however clean its vocabulary is.
#
# It reports rather than fails on its own. Dispersion is a property of a whole
# piece, so it needs enough sentences to mean anything, and the honest output
# is the numbers plus a flag the auditor scores against the rhythm dimension.

# Spread is measured relative to length, not in absolute words. A memo of
# short sentences has a small standard deviation for an innocent reason, and
# an absolute floor flagged one of this repo's own clean fixtures on exactly
# that mistake. The ratio of deviation to mean is scale-free: across the
# fixtures and the repo's own prose it runs 0.45 to 0.80 on writing nobody
# objects to, and drops to 0.37 on the draft written to be slop.
DISPERSION_MIN_UNITS = 12
DISPERSION_MIN_CV = 0.40
DISPERSION_BAND = (12, 26)
DISPERSION_BAND_SHARE = 0.65


def dispersion(text):
    """Sentence-length spread. Returns None when there is too little to judge.

    A flag means: variation collapsed relative to sentence length, or most
    sentences sit inside one narrow band. Either shape is the machine-stamped
    skeleton the taste gate asks about, made countable.
    """
    units = [u.strip() for u in split_sentences(" ".join(prose_lines(text)))
             if u.strip()]
    lengths = [len(WORD.findall(u)) for u in units]
    lengths = [n for n in lengths if n > 0]
    if len(lengths) < DISPERSION_MIN_UNITS:
        return None
    mean = sum(lengths) / len(lengths)
    var = sum((n - mean) ** 2 for n in lengths) / len(lengths)
    sd = var ** 0.5
    cv = sd / mean if mean else 0.0
    lo, hi = DISPERSION_BAND
    share = sum(1 for n in lengths if lo <= n <= hi) / len(lengths)
    flagged = cv < DISPERSION_MIN_CV or share >= DISPERSION_BAND_SHARE
    return {"n": len(lengths), "mean": mean, "stdev": sd, "cv": cv,
            "band_share": share, "flagged": flagged}


# The paragraph is the unit a reader feels texture in, but short-form and
# bulleted writing puts one tell per paragraph by construction, which silences
# the rule exactly where the writing is worst. The launch-post fixture runs
# five filler words through 133 words and scored zero under the paragraph rule
# alone. Both conditions have to hold: density says the document is saturated,
# the minimum count says it is saturated with more than one editorial habit.
# Two spread hits in a short post is a word choice twice. Three is a texture.
TIER2_DOC_MIN = 3
TIER2_DOC_PER_1000 = 10.0
TIER3_PER_1000 = 3.0


def scan_paste_tells(raw, path):
    """Fire on chat-interface residue, inside quotations as well as outside.

    Exempt only inside code. A paste tell in a quoted block still proves the
    quotation was pasted without being read, so the usual quote exemption
    would defeat the check.
    """
    text = apply_exemptions(raw, code_only=True)
    found = 0
    for lineno, chunk, _structural in blocks(text):
        for label, pat in PASTE_TELLS:
            for m in pat.finditer(chunk):
                found += 1
                print(f"{path}:{lineno} | {label} (P0) | {m.group(0).strip()!r}")
    return found


def scan_tics(paths, include_quoted=False):
    hits = 0
    for p in paths:
        raw = Path(p).read_text(encoding="utf-8", errors="replace")
        hits += scan_paste_tells(raw, p)
        # Code and blockquotes are line-anchored, so blank them on the full
        # text. Quoted spans and wrapped inline code are blanked per joined
        # paragraph instead, where a hard wrap has become an ordinary space,
        # so a quotation or a backticked span broken across a line break is
        # exempt exactly like its one-line form.
        text = apply_exemptions(raw, include_quoted=True)
        prose_chunks, stray = [], []
        tier2_held, tier2_total, tier3, words = [], 0, [], 0
        for lineno, chunk, structural in blocks(text):
            chunk = blank_inline_code(chunk)
            if not include_quoted:
                if unbalanced_doubles(chunk):
                    stray.append(lineno)
                chunk = blank_quoted(chunk)
            # Fold ’ to ' after the quote-mark work, which needs the curly
            # form, and before matching, which is written in straight ones.
            chunk = fold_apostrophes(chunk)
            if not structural:
                prose_chunks.append(chunk)
            words += len(WORD.findall(chunk))
            deferred = []
            for label, pat, tier in TIC_PATTERNS:
                for m in pat.finditer(chunk):
                    found = (lineno, label, m.group(0).strip())
                    if tier == 1:
                        hits += 1
                        print(f"{p}:{found[0]} | {mark(label)} | {found[2]!r}")
                    elif tier == 2:
                        deferred.append(found)
                    else:
                        tier3.append(found)
            # A tier-2 word alone is a word choice. Two in one paragraph is a
            # texture, and the paragraph is the unit a reader feels it in.
            tier2_total += len(deferred)
            if len(deferred) >= 2:
                for lno, label, text_ in deferred:
                    hits += 1
                    print(f"{p}:{lno} | {mark(label)} [tier 2] | {text_!r}")
            else:
                tier2_held.extend(deferred)
        if tier2_held and words and len(tier2_held) >= TIER2_DOC_MIN:
            density = tier2_total * 1000.0 / words
            if density >= TIER2_DOC_PER_1000:
                for lno, label, text_ in tier2_held:
                    hits += 1
                    print(f"{p}:{lno} | {mark(label)} [tier 2, {density:.1f}/1000] "
                          f"| {text_!r}")
        if tier3 and words:
            density = len(tier3) * 1000.0 / words
            if density >= TIER3_PER_1000:
                for lno, label, text_ in tier3:
                    hits += 1
                    print(f"{p}:{lno} | {mark(label)} [tier 3, {density:.1f}/1000] "
                          f"| {text_!r}")
        prose = "\n".join(prose_chunks)
        run, units = staccato_run(prose)
        if run:
            hits += 1
            print(f"{p} | over-correction (staccato run of {run}) | "
                  f"{' / '.join(units[:4])!r}")
        # Suppressed when the staccato run already fired. Both measure the
        # same document's rhythm, and a report that bills one defect twice
        # invites the reader to discount the rest of it.
        d = dispersion(prose)
        if d and d["flagged"] and not run:
            hits += 1
            print(f"{p} | rhythm uniformity (n={d['n']}, mean="
                  f"{d['mean']:.1f}, sd={d['stdev']:.1f}, cv={d['cv']:.2f}, "
                  f"{d['band_share']*100:.0f}% in {DISPERSION_BAND[0]}-"
                  f"{DISPERSION_BAND[1]} words) | "
                  f"'sentence lengths do not vary'")
        if stray:
            lines = ", ".join(str(n) for n in stray[:5])
            print(f"slop_check: {p}: odd number of double-quote marks in the "
                  f"paragraph(s) starting at line {lines}. Those paragraphs "
                  f"were scanned in full rather than quote-exempted, so a "
                  f"finding inside a quotation there is expected.",
                  file=sys.stderr)
    print(f"\n{hits} tic(s) found." if hits else "Clean: 0 tics found.")
    return 1 if hits else 0


# -------------------------------------------------------------- quotes ----

QUOTE_RE = re.compile(r'[“"]([^“”"]{12,600})[”"]')
# Same apostrophe rule as the exemption pattern: a closing ’ followed by a
# word character is an apostrophe, not a quote mark.
SINGLE_QUOTE_RE = re.compile(r"‘([^‘]{12,600}?)’(?!\w)")
# A quotation may wrap across a hard line break, so neither quote pattern can
# forbid newlines. It may not cross a paragraph break: a span that does is an
# unpaired mark reaching for the next one, which is how a lone elision
# apostrophe (‘em) pairs with a possessive two paragraphs later and reports a
# quotation the draft never contained.
PARA_BREAK = re.compile(r"\n\s*\n")
# An ellipsis inside a quotation marks a deliberate omission. Each segment
# around it must still be verbatim, and in the same source file: segments that
# only exist in different files are a fusion, not an elision.
ELLIPSIS = re.compile(r"\[\s*(?:\.{3,}|…)\s*\]|\.{3,}|…")
# Words whose removal reverses a sentence. Checked against what an ellipsis
# actually omits in the source, not against the quote.
NEGATION = re.compile(
    r"\b(?:not|never|no|nor|none|without|unless|cannot|hardly|barely|rarely|"
    r"\w+n['’]t)\b", re.I)


def normalize(s: str) -> str:
    s = html.unescape(s)
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.lower()
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def corpus_files(corpus: str, exclude=None):
    """Normalized text per source file, so a quote cannot false-match across a
    file boundary and so the matching file can be named in the correction log.

    exclude is the manuscript path: when the corpus directory contains the
    manuscript itself, every quote would silently verify against its own text,
    so the manuscript is never part of its own corpus."""
    path = Path(corpus)
    skip = Path(exclude).resolve() if exclude else None
    if path.is_file():
        if skip and path.resolve() == skip:
            return {}
        return {path.name: normalize(path.read_text(encoding="utf-8", errors="replace"))}
    out = {}
    for f in sorted(path.rglob("*")):
        if any(part.startswith(".") for part in f.relative_to(path).parts):
            continue  # skip .git and other hidden trees
        if skip and f.resolve() == skip:
            continue
        if f.is_file() and f.suffix.lower() in {".md", ".txt", ".html", ".json", ".csv", ""}:
            out[str(f.relative_to(path))] = normalize(f.read_text(encoding="utf-8", errors="replace"))
    return out


def scan_quotes(manuscript: str, corpus: str, min_words: int) -> int:
    raw = Path(manuscript).read_text(encoding="utf-8", errors="replace")
    # Code only: blockquoted epigraphs are the highest-visibility quotes in a
    # piece, so they must stay visible to this scan.
    text = apply_exemptions(raw, code_only=True)
    corp = corpus_files(corpus, exclude=manuscript)
    if not corp:
        print(f"slop_check: no readable corpus files under {corpus}", file=sys.stderr)
        return 2
    found = [(m.start(), m.end(), m.group(1)) for m in QUOTE_RE.finditer(text)]
    found += [(m.start(), m.end(), m.group(1)) for m in SINGLE_QUOTE_RE.finditer(text)]
    found = [f for f in found if not PARA_BREAK.search(f[2])]
    # A curly single quote nested inside a double quote is one quotation, not
    # two. Counting it twice pads the verified ratio the correction log rests
    # on, and does it exactly where a careful writer quotes a source quoting
    # someone else.
    outer = sorted(found)
    spans = [s for a, b, s in outer
             if not any(x < a and b <= y for x, y, _ in outer)]
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
        if status == "NONE" and ELLIPSIS.search(span):
            # Every segment must be verbatim, in one file, in source order.
            # Dropping short segments would leave the word a sentence turns on
            # unchecked: "we are ... planning any layoffs" reads as verified
            # against a source saying "we are not planning any layoffs".
            # Order matters for the same reason: segments that appear in the
            # file but not in sequence are a fusion wearing an ellipsis.
            parts = [normalize(p) for p in ELLIPSIS.split(span)]
            parts = [p for p in parts if p]
            if len(parts) >= 2:
                for name, body in corp.items():
                    cursor, ok, gaps = 0, True, []
                    for p in parts:
                        at = body.find(p, cursor)
                        if at < 0:
                            ok = False
                            break
                        if cursor:
                            gaps.append(body[cursor:at])
                        cursor = at + len(p)
                    if not ok:
                        continue
                    # An ellipsis that swallows a negation is formally legal
                    # elision and substantively a misquote: "we are ...
                    # planning any layoffs" against a source that says "we are
                    # not planning any layoffs". So is a gap too small to be
                    # worth eliding, which is the shape that trick takes. Both
                    # verify as text and still need a human, which is what
                    # PARTIAL means.
                    swallowed = next((g for g in gaps if NEGATION.search(g)), None)
                    if swallowed:
                        cut = swallowed.strip()
                        if len(cut) > 60:
                            cut = f"{cut[:28]}...{cut[-28:]}"
                        status = "PARTIAL"
                        where = f"{name} (elision omits a negation: {cut!r})"
                    elif any(len(g.split()) < 3 for g in gaps):
                        status = "PARTIAL"
                        where = f"{name} (elision omits under three words; check what)"
                    else:
                        status, where = "MATCH", f"{name} (elided)"
                    break
        if status == "NONE":
            win = min(6, len(words))
            windows = [" ".join(words[i:i + win]) for i in range(0, max(1, len(words) - win + 1))]
            for name, body in corp.items():
                if any(w in body for w in windows):
                    status, where = "PARTIAL", name
                    break
        results[status] += 1
        flat = re.sub(r"\s+", " ", span).strip()
        short = flat if len(flat) <= 90 else flat[:87] + "..."
        suffix = f"  <- {where}" if where else ""
        print(f"[{status:7}] “{short}”{suffix}")
    total = sum(results.values())
    print(f"\n{total} quoted span(s) >= {min_words} words: "
          f"{results['MATCH']} MATCH / {results['PARTIAL']} PARTIAL / {results['NONE']} NONE")
    if skipped:
        print(f"slop_check: {skipped} span(s) shorter than {min_words} words were not checked.",
              file=sys.stderr)
    if total == 0:
        print("slop_check: no quoted spans extracted. Straight single quotes are never "
              "treated as quote marks; if this draft uses them, the scan checked nothing "
              "and every quote needs hand verification.", file=sys.stderr)
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
