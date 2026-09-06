#!/usr/bin/env python3
"""Provenance check for every binary asset — house rule P-11.

Three questions, in order of how badly a wrong answer would hurt:

  1. Is there a media file on the site that `_content/ASSETS.md` does not
     register?  That is the shape the rule exists to catch: an agent dropping a
     downloaded photograph into the repo.
  2. Did a registered file change without its entry changing?
  3. Are the derived images really derived — is each width variant a downscale
     of the base it claims, and (with --deep) is each detail crop a region of
     its own base rather than of another service's photo?

Usage:  python3 _content/verify_assets.py [--deep]
"""
import hashlib, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "_content/ASSETS.md"
BASES = ["hero", "kitchen", "bath", "addition", "outdoor", "permit", "remodel"]
MEDIA = ("*.webp", "*.jpg", "*.jpeg", "*.png", "*.svg", "*.woff2", "*.gif", "*.mp4")
# generated wholesale from a registered source; the derivation check covers them
# trailing slashes matter: without them "images/r" prefix-matches "images/remodel.webp"
# and the base photograph exempts itself from the registration check
DERIVED_DIRS = ("images/r/", "images/detail/", "images/og/")
SKIP = ("_content/images-original/", ".worktrees/", ".git/")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def registered():
    """path -> 32-hex prefix, from the manifest's tables."""
    out = {}
    for path, digest in re.findall(r"^\| `([^`]+)` \| `([0-9a-f]{32})…` \|",
                                   MANIFEST.read_text(), re.M):
        out[path] = digest
    return out


def media_files():
    for pat in MEDIA:
        for p in ROOT.rglob(pat):
            rel = str(p.relative_to(ROOT))
            if any(rel.startswith(s) for s in SKIP):
                continue
            yield rel, p


def main():
    deep = "--deep" in sys.argv
    reg, problems = registered(), []
    if not reg:
        sys.exit("ASSETS.md holds no registered hashes — manifest unreadable")

    seen = set()
    for rel, p in media_files():
        if any(rel.startswith(d) for d in DERIVED_DIRS):
            continue
        seen.add(rel)
        if rel not in reg:
            problems.append(f"UNREGISTERED  {rel} — add it to _content/ASSETS.md "
                            f"with its origin before this ships")
        elif not sha(p).startswith(reg[rel]):
            problems.append(f"CHANGED       {rel} — content differs from its manifest entry")
    for rel in reg:
        if rel not in seen and not (ROOT / rel).exists():
            problems.append(f"MISSING       {rel} — registered but not on disk")

    # derivation: every variant must be a downscale of the base it names
    try:
        from PIL import Image
    except ImportError:
        problems.append("SKIPPED       derivation check — Pillow not installed")
    else:
        def arr(im):
            return list(im.convert("RGB").getdata())

        def diff(a, b):
            return sum(abs(x[0] - y[0]) + abs(x[1] - y[1]) + abs(x[2] - y[2])
                       for x, y in zip(a, b)) / (3 * len(a))

        base = {b: Image.open(ROOT / f"images/{b}.webp").convert("RGB") for b in BASES}
        for p in sorted((ROOT / "images/r").glob("*.webp")):
            stem = p.stem.rsplit("-", 1)[0]
            if stem not in base:
                problems.append(f"ORPHAN        images/r/{p.name} — no base named {stem}")
                continue
            cand = Image.open(p).convert("RGB").resize((96, 64), Image.LANCZOS)
            ref = base[stem].resize((96, 64), Image.LANCZOS)
            d = diff(arr(cand), arr(ref))
            if d > 8.0:
                problems.append(f"NOT DERIVED   images/r/{p.name} — differs from "
                                f"images/{stem}.webp by {d:.1f}/255")
        if deep:
            problems += deep_crop_check(Image, base, arr, diff)

    for line in problems:
        print(line)
    print(f"\n{len(reg)} assets registered, {len(problems)} problem(s)")
    sys.exit(1 if problems else 0)


def deep_crop_check(Image, base, arr, diff):
    """Each detail crop must match its OWN base better than any other service's."""
    out = []
    for p in sorted((ROOT / "images/detail").glob("*.webp")):
        stem = p.stem.split("-")[0]
        ci = Image.open(p).convert("RGB")
        ar = ci.width / ci.height
        probe = arr(ci.resize((48, max(1, round(48 / ar))), Image.LANCZOS))
        ph = max(1, round(48 / ar))
        best, who = 1e9, None
        for name, bi in base.items():
            for scale in (1.0, 0.8, 0.65, 0.5, 0.4, 0.3):
                cw = round(bi.width * scale); ch = round(cw / ar)
                if ch > bi.height or cw < 32:
                    continue
                sx = max(1, (bi.width - cw) // 6); sy = max(1, (bi.height - ch) // 6)
                for y in range(0, bi.height - ch + 1, sy):
                    for x in range(0, bi.width - cw + 1, sx):
                        d = diff(arr(bi.crop((x, y, x + cw, y + ch))
                                     .resize((48, ph), Image.LANCZOS)), probe)
                        if d < best:
                            best, who = d, name
        if who != stem:
            out.append(f"WRONG SOURCE  images/detail/{p.name} — matches "
                       f"images/{who}.webp, not images/{stem}.webp")
    return out


if __name__ == "__main__":
    main()
