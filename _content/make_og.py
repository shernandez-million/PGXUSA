#!/usr/bin/env python3
"""Generate the per-service social-share thumbnails.

These five existed but were made by hand in an early session, so when permit.webp was
rebuilt (to strip the retired logo) its thumbnail was never regenerated and 86 permitting
pages pointed at a missing file. Owning them in a script is the fix: run this after any
change to a service photo.

Method matches the originals exactly — cover-fit centre crop to 1200x630, JPEG q88.
"""
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PLAN = json.loads((ROOT / "_content" / "site_plan.json").read_text())
SIZE = (1200, 630)
# Where to take the crop from. A centre crop is right for the room photos, but permit.webp
# puts its subject — the plan set and the tablet — in the lower half, and a centre crop of it
# returns a sofa. Anchor is the vertical position of the crop window, 0 = top, 1 = bottom.
ANCHOR = {"permit": 1.0}


def social(src: Path, out: Path, anchor: float = 0.5) -> None:
    im = Image.open(src).convert("RGB")
    # take the widest window of the target aspect that fits, so nothing is upscaled
    ar = SIZE[0] / SIZE[1]
    if im.width / im.height > ar:
        cw, ch = round(im.height * ar), im.height
    else:
        cw, ch = im.width, round(im.width / ar)
    l = (im.width - cw) // 2
    t = round((im.height - ch) * anchor)
    im.crop((l, t, l + cw, t + ch)).resize(SIZE, Image.LANCZOS).save(
        out, "JPEG", quality=88, optimize=True, progressive=True)


def main() -> int:
    force = "--force" in sys.argv
    og = ROOT / "images" / "og"
    og.mkdir(parents=True, exist_ok=True)
    # every image any page type can use as its hero
    stems = {Path(s["image"]).stem for s in PLAN["services"]}
    stems |= {Path(t["image"]).stem for t in PLAN.get("property_types", [])}
    missing = 0
    for stem in sorted(stems):
        src, out = ROOT / "images" / f"{stem}.webp", og / f"{stem}-og.jpg"
        if not src.exists():
            print(f"  !! source missing: {src.relative_to(ROOT)}")
            missing += 1
            continue
        if out.exists() and not force:
            print(f"  ok      {out.relative_to(ROOT)}")
            continue
        social(src, out, ANCHOR.get(stem, 0.5))
        print(f"  WROTE   {out.relative_to(ROOT)}  {out.stat().st_size // 1024}KB")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
