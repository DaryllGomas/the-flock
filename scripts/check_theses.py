#!/usr/bin/env python3
"""Check the published thesis and every research thesis.

    python3 scripts/check_theses.py                  # thesis/THESIS.md + research/theses/*.md
    python3 scripts/check_theses.py --thesis FILE    # check FILE as the Running Thesis instead (for testing a draft)

The Running Thesis (thesis/THESIS.md) must have a Sources section with a real https link, the "Not investment advice"
line, and an Open calls table in which every row starts with a call ID (like `T-1023-W3`, or F-2026-10-25-1), no ID twice.
Each research thesis must have the template's sections, a named model and a source link.
"""
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
THESIS = ROOT / "thesis/THESIS.md"
SECTIONS = ["Bull case", "Bear case", "What would prove this wrong", "Explain it like I'm new", "Sources"]
DISCLAIMER = "Not financial advice"
CALL_ID = re.compile(r"[A-Z]-\d{4}-[A-Z0-9]+|F-(\d{4}-\d{2}-\d{2})-\d+")


def section(text, heading):
    """The body under a '## heading' line, up to the next '## ' heading; None if there is no such heading."""
    m = re.search(rf"^##[ \t]+{re.escape(heading)}[ \t]*$", text, re.M)
    if not m:
        return None
    rest = text[m.end():]
    nxt = re.search(r"^##[ \t]", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def links(body):
    return [u.rstrip(".,;:") for u in re.findall(r"https://[^\s)>\]]+", body)]


def source_errors(body, where):
    found = links(body)
    errors = [f"{where} has a link that is not a real https link: {u}" for u in found if not check.real_https_url(u)]
    if not any(check.real_https_url(u) for u in found):
        errors.append(f"no real https source link under {where}")
    return errors


def check_open_calls(body):
    rows = []  # the first table only: its first run of '|' lines
    for ln in body.splitlines():
        if ln.strip().startswith("|"):
            rows.append(ln.strip())
        elif rows:
            break
    cells = [[c.strip() for c in ln.strip("|").split("|")] for ln in rows]
    data = [c for c in cells if not all(re.fullmatch(r":?-{3,}:?", x) for x in c)][1:]  # drop header and separator
    if not data:
        return ["the Open calls table has no rows"]
    errors, seen = [], set()
    for n, row in enumerate(data, 1):
        ident = row[0].strip("`").strip()
        m = CALL_ID.fullmatch(ident) if row[0].strip() else None
        if m and m.group(1):
            try:
                date.fromisoformat(m.group(1))
            except ValueError:
                m = None
        if not m:
            errors.append(f"Open calls row {n} has no call ID in its first column (like `T-1023-W3`): {row[0][:60]!r}")
        elif ident in seen:
            errors.append(f"Open calls: call ID {ident} appears twice")
        seen.add(ident)
    return errors


def check_thesis(text):
    errors = []
    src = section(text, "Sources")
    if src is None:
        errors.append("missing a '## Sources' section")
    else:
        errors += source_errors(src, "Sources")
    if not re.search(r"not investment advice", text, re.I):
        errors.append("missing the 'Not investment advice' line")
    calls = section(text, "Open calls")
    if calls is None:
        errors.append("missing an '## Open calls' section")
    else:
        errors += check_open_calls(calls)
    return errors


def check_research(text):
    errors = [f"missing '## {s}'" for s in SECTIONS if section(text, s) is None]
    if not re.search(r"\*\*Model:\*\*\s*\S", text):
        errors.append("no model named")
    src = section(text, "Sources")
    if src is not None:
        errors += source_errors(src, "Sources")
    if DISCLAIMER not in text:
        errors.append("missing the not-financial-advice line")
    return errors


def main(argv):
    thesis = THESIS
    if argv[:1] == ["--thesis"] and len(argv) == 2:
        thesis = Path(argv[1])
    elif argv:
        print("usage: check_theses.py [--thesis FILE]")
        return 2
    failed = False
    try:
        main_errors = check_thesis(thesis.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        main_errors = [f"cannot read it: {e}"]
    for e in main_errors:
        print(f"FAIL {thesis.name}: {e}")
        failed = True
    theses = [p for p in sorted((ROOT / "research/theses").glob("*.md")) if p.name != "TEMPLATE.md"]
    for p in theses:
        for e in check_research(p.read_text(encoding="utf-8")):
            print(f"FAIL {p.name}: {e}")
            failed = True
    if failed:
        return 1
    print(f"ok: {thesis.name} and {len(theses)} research thesis file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
