#!/usr/bin/env python3
"""Apply verified Spanish copy corrections to the .es.json content packs.

Each fix is an exact substring replacement that must match EXACTLY ONCE in its file —
anything else (missing, or ambiguous) is refused and reported rather than guessed at,
so a stale or overly short `old` string can never silently rewrite the wrong sentence.
"""
import json
import pathlib
import re
import sys

# A reviewer only sees one pack and its English twin, so it cannot know which wordings are
# deliberate site-wide policy. These vetoes protect decisions recorded in CLAUDE.md from
# being "corrected" back into defects by a well-meaning proposal.
VETOES = [
    (re.compile(r"habitables?"),
     "removes 'habitable' from the milestone threshold — HB 913 (2025) narrowed it to three "
     "HABITABLE stories on purpose"),
    (re.compile(r"\b(25|30|40|50)\s*a\xf1os\b|\bcada\s+(diez|10)\s+a\xf1os\b"),
     "reintroduces a numeric inspection threshold, which the site states qualitatively"),
]


def vetoed(old: str, new: str):
    """Refuse a fix that strips a deliberate wording or adds a banned number."""
    for pat, why in VETOES:
        if pat.search(old) and not pat.search(new):
            return why
        if pat.search(new) and not pat.search(old):
            return why
    return None


def main() -> int:
    fixes_path = pathlib.Path(sys.argv[1])
    root = pathlib.Path(__file__).resolve().parent
    by_area = json.loads(fixes_path.read_text())

    applied, refused = 0, []
    for area, fixes in sorted(by_area.items()):
        p = root / f"{area}.es.json"
        if not p.exists():
            refused.append((area, "-", "no such pack")); continue
        txt = p.read_text()
        before = txt
        for fx in fixes:
            old, new = fx["old"], fx["new"]
            veto = vetoed(old, new)
            if veto:
                refused.append((area, fx.get("field", "?"), f"VETOED: {veto}"))
                continue
            n = txt.count(old)
            if n != 1:
                refused.append((area, fx.get("field", "?"), f"matches {n}x: {old[:60]!r}"))
                continue
            txt = txt.replace(old, new, 1)
            applied += 1
        if txt != before:
            json.loads(txt)              # never write a pack that stopped parsing
            p.write_text(txt)

    print(f"applied {applied} fixes; refused {len(refused)}")
    for a, f, why in refused:
        print(f"  REFUSED {a}/{f}: {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
