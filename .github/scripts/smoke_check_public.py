#!/usr/bin/env python3
"""Lightweight smoke checks for Hugo public output."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def check_file(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8", errors="ignore")

    if "<html" not in text.lower():
        errors.append(f"{path}: missing <html tag")

    refs = re.findall(r"""(?:href|src)=["']([^"']+)["']""", text, flags=re.IGNORECASE)
    for ref in refs:
        if not ref:
            continue
        if ref.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:")):
            continue

        if ref.startswith("/"):
            target = Path("public") / ref.lstrip("/")
        else:
            target = path.parent / ref

        # Hugo commonly serves directory routes via index.html.
        if not target.exists():
            alt = target / "index.html"
            if alt.exists():
                continue
            errors.append(f"{path}: broken local reference '{ref}'")


def main() -> int:
    public_dir = Path("public")
    errors: list[str] = []

    if not public_dir.exists():
        print("public directory not found; run Hugo build first", file=sys.stderr)
        return 1

    index_file = public_dir / "index.html"
    if not index_file.exists():
        print("public/index.html not found", file=sys.stderr)
        return 1

    html_files = sorted(public_dir.rglob("*.html"))
    if not html_files:
        print("no html files found under public/", file=sys.stderr)
        return 1

    for html_file in html_files:
        check_file(html_file, errors)

    if errors:
        print("Smoke checks failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print(f"Smoke checks passed for {len(html_files)} HTML files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
