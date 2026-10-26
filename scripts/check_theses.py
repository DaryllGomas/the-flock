#!/usr/bin/env python3
"""Check every thesis in research/theses/ has the template's sections and at least one source link."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECTIONS = ["## Bull case", "## Bear case", "## What would prove this wrong", "## Explain it like I'm new", "## Sources"]
DISCLAIMER = "Not financial advice"


def check(path):
    text = path.read_text()
    errors = [f"missing '{s}'" for s in SECTIONS if s not in text]
    if not re.search(r"\*\*Model:\*\*\s*\S", text):
        errors.append("no model named")
    sources = text.split("## Sources", 1)[-1]
    if not re.search(r"https://\S+", sources):
        errors.append("no https source link under Sources")
    if DISCLAIMER not in text:
        errors.append("missing the not-financial-advice line")
    return errors


def main():
    failed = False
    theses = [p for p in sorted((ROOT / "research/theses").glob("*.md")) if p.name != "TEMPLATE.md"]
    for p in theses:
        for e in check(p):
            print(f"FAIL {p.name}: {e}")
            failed = True
    if failed:
        sys.exit(1)
    print(f"ok: {len(theses)} thesis file(s)")


if __name__ == "__main__":
    main()
