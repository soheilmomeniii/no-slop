#!/usr/bin/env python3
"""Validate every SKILL.md in this repo against the agent-skills spec.

Rules enforced (https://agentskills.io/specification):
  name          required, 1-64 chars, ^[a-z0-9-]+$, no leading/trailing or
                doubled hyphen, must equal the parent directory name, and may
                not contain the reserved words "anthropic" or "claude"
  description   required, 1-1024 chars, no angle brackets
  compatibility optional, <= 500 chars
  keys          only {name, description, license, allowed-tools, metadata,
                compatibility}
  body          <= 500 lines

Also refuses content that trips skill-registry security scanners: zero-width
Unicode, HTML comments, and any instruction piping a download into a shell.

The banned characters are written here as escape sequences on purpose, so this
file does not contain the literals it rejects. Same discipline the skill itself
uses: fix a self-reference in band, never by exempting yourself.

Usage: python tools/validate_skills.py [root]     exit 0 pass, 1 fail
"""

import re
import sys
from pathlib import Path

ALLOWED = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ZERO_WIDTH = re.compile("[\\u200b-\\u200d\\ufeff\\u2060]")
HTML_COMMENT = re.compile("<" + "!--")
CURL_PIPE = re.compile(r"\bcu" + r"rl\b[^\n|]*\|\s*(?:ba)?sh\b")


def parse_frontmatter(text):
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end == -1:
        return None, text
    raw, body = text[4:end], text[end + 4:]
    data, key, buf = {}, None, []
    for line in raw.splitlines():
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if m and not line.startswith(" "):
            if key:
                data[key] = " ".join(buf).strip()
            key, first = m.group(1), m.group(2).strip()
            buf = [] if first in (">-", ">", "|", "|-", "") else [first]
        elif key:
            buf.append(line.strip())
    if key:
        data[key] = " ".join(buf).strip()
    return data, body


def check(path: Path, errors, warnings):
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    rel = path.as_posix()
    if fm is None:
        errors.append(f"{rel}: missing or malformed YAML frontmatter")
        return
    for k in fm:
        if k not in ALLOWED:
            errors.append(f"{rel}: frontmatter key '{k}' is not in the spec's allowed set")
    name = fm.get("name", "")
    if not name:
        errors.append(f"{rel}: name is required")
    else:
        if not NAME_RE.match(name):
            errors.append(f"{rel}: name '{name}' must be kebab-case [a-z0-9-]")
        if len(name) > 64:
            errors.append(f"{rel}: name is {len(name)} chars (max 64)")
        if name != path.parent.name:
            errors.append(f"{rel}: name '{name}' must equal directory '{path.parent.name}'")
        if "anthropic" in name or "claude" in name:
            errors.append(f"{rel}: name may not contain a reserved word")
    desc = fm.get("description", "")
    if not desc:
        errors.append(f"{rel}: description is required")
    elif len(desc) > 1024:
        errors.append(f"{rel}: description is {len(desc)} chars (max 1024)")
    if "<" in desc or ">" in desc:
        errors.append(f"{rel}: description may not contain angle brackets")
    if len(fm.get("compatibility", "")) > 500:
        errors.append(f"{rel}: compatibility exceeds 500 chars")
    lines = len(body.splitlines())
    if lines > 500:
        errors.append(f"{rel}: body is {lines} lines (max 500)")
    elif lines > 400:
        warnings.append(f"{rel}: body is {lines} lines, approaching the 500 limit")
    if "license" not in fm:
        warnings.append(f"{rel}: no license key in frontmatter")
    for ref in re.findall(r"`(references/[\w./-]+|scripts/[\w./-]+)`", body):
        if not (path.parent / ref).exists():
            errors.append(f"{rel}: references '{ref}', which does not exist")
    print(f"  {rel}: name={name} desc={len(desc)} body={lines} lines")


def scan_security(root: Path, errors):
    for f in root.rglob("*"):
        if not f.is_file() or ".git/" in f.as_posix():
            continue
        rel_early = f.relative_to(root).as_posix()
        # Checked before the suffix filter, or the filter would skip the very
        # extensions this rule exists to catch.
        if f.suffix == ".pyc" or "__pycache__" in rel_early or ".pytest_cache" in rel_early:
            errors.append(f"{rel_early}: build artifact committed")
            continue
        if f.suffix.lower() not in {".md", ".py", ".json", ".yml", ".yaml", ".sh", ".txt"}:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = f.relative_to(root).as_posix()
        if ZERO_WIDTH.search(text):
            errors.append(f"{rel}: contains zero-width Unicode")
        if f.suffix == ".md" and HTML_COMMENT.search(text):
            errors.append(f"{rel}: contains an HTML comment (hidden-payload vector)")
        if CURL_PIPE.search(text):
            errors.append(f"{rel}: contains a curl-pipe-to-shell instruction")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    skills = sorted(p for p in root.rglob("SKILL.md") if ".git" not in p.parts)
    if not skills:
        print(f"No SKILL.md found under {root}", file=sys.stderr)
        return 1
    errors, warnings = [], []
    print(f"Validating {len(skills)} skill(s) under {root}:")
    for s in skills:
        check(s, errors, warnings)
    scan_security(root, errors)
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"FAIL  {e}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
