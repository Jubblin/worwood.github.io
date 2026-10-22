#!/usr/bin/env python3
"""Smoke checks for the EmDash (Astro SSR) site served at a base URL.

Usage: smoke_check_url.py http://localhost:4329
"""

from __future__ import annotations

import re
import sys
import urllib.request


def fetch(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as err:
        return err.code, ""


def main() -> int:
    base = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:4321").rstrip("/")
    status, html = fetch(base + "/")
    if status != 200:
        print(f"GET / returned {status}")
        return 1

    errors: list[str] = []
    if "<html" not in html.lower():
        errors.append("homepage missing <html tag")
    # An empty database still renders the page shell; require seeded resume content.
    for marker in ('class="section-title"', 'class="company"'):
        if marker not in html:
            errors.append(f"homepage missing {marker} (resume content not rendered)")

    refs = set(re.findall(r"""(?:href|src)=["'](/[^"'#?]*)""", html))
    for ref in sorted(refs):
        code, _ = fetch(base + ref)
        if code != 200:
            errors.append(f"broken local reference '{ref}' ({code})")

    if errors:
        print("Smoke checks failed:")
        for err in errors:
            print(f"- {err}")
        return 1
    print(f"Smoke checks passed for {base}/ ({len(refs)} local references).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
