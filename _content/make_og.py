#!/usr/bin/env python3
"""Generate the social-share images: the site-wide card and the per-service thumbnails.

These five existed but were made by hand in an early session, so when permit.webp was
rebuilt (to strip the retired logo) its thumbnail was never regenerated and 86 permitting
pages pointed at a missing file. Owning them in a script is the fix: run this after any
change to a service photo.

Method matches the originals exactly — cover-fit centre crop to 1200x630, JPEG q88.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PLAN = json.loads((ROOT / "_content" / "site_plan.json").read_text())
SIZE = (1200, 630)
INK, BG = (26, 26, 24), (242, 241, 238)
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


def wordmark_plate(height: int = 116, width: int = 268) -> Image.Image:
    """The real logo on a light plate, rasterised from images/pgx-wordmark.svg.

    The retired make_brand_assets.py drew this with the system Didot face, which is a
    different mark from the one Andres supplied — different G spur, different X
    terminals — so the site-wide share card carried a logo the site does not use.
    Always render from the SVG, never from a font that merely resembles it.
    """
    src = (ROOT / "images" / "pgx-wordmark.svg").read_text()
    d = re.search(r'\sd="([^"]+)"', src).group(1)
    vb = re.search(r'viewBox="([^"]+)"', src).group(1)
    x, y, w, h = (float(v) for v in vb.split())
    svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}">'
           f'<path d="{d}" fill="rgb{INK}" fill-rule="evenodd"/></svg>\n')
    tmp = Path("/tmp/_pgx_og_mark.svg")
    tmp.write_text(svg)
    subprocess.run(["qlmanage", "-t", "-s", "1600", "-o", "/tmp", str(tmp)], capture_output=True)
    got = Path("/tmp/_pgx_og_mark.svg.png")
    if not got.exists():
        raise SystemExit("wordmark render failed (qlmanage)")
    # qlmanage returns an opaque square on white, so pasting it straight in would drop a
    # white box inside the off-white plate. Key the ink out by luminance instead: dark
    # pixels become opaque, white becomes transparent, and antialiasing survives intact.
    grey = Image.open(got).convert("L")
    got.unlink()
    alpha = Image.eval(grey, lambda v: 255 - v)
    bbox = alpha.getbbox()
    if bbox is None:
        raise SystemExit("wordmark render was blank")
    alpha = alpha.crop(bbox)

    plate = Image.new("RGB", (width, height), BG)
    mw = round(width * 0.78)
    mh = round(mw * alpha.height / alpha.width)
    if mh > height * 0.68:
        mh = round(height * 0.68)
        mw = round(mh * alpha.width / alpha.height)
    alpha = alpha.resize((mw, mh), Image.LANCZOS)
    ink = Image.new("RGB", (mw, mh), INK)
    plate.paste(ink, ((width - mw) // 2, (height - mh) // 2), alpha)
    return plate


def site_card(src: Path, out: Path) -> None:
    """The share card for the homepage and every page without a service photo."""
    im = Image.open(src).convert("RGB")
    r = max(SIZE[0] / im.width, SIZE[1] / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    l, t = (im.width - SIZE[0]) // 2, (im.height - SIZE[1]) // 2
    im = im.crop((l, t, l + SIZE[0], t + SIZE[1]))
    plate = wordmark_plate()
    m = 44
    im.paste(plate, (m, SIZE[1] - plate.height - m))
    im.save(out, "JPEG", quality=88, optimize=True, progressive=True)


def main() -> int:
    force = "--force" in sys.argv
    og = ROOT / "images" / "og"
    og.mkdir(parents=True, exist_ok=True)
    # every image any page type can use as its hero
    stems = {Path(s["image"]).stem for s in PLAN["services"]}
    stems |= {Path(t["image"]).stem for t in PLAN.get("property_types", [])}
    missing = 0
    card = ROOT / "og-image.jpg"
    if force or not card.exists():
        site_card(ROOT / "images" / "hero.webp", card)
        print(f"  WROTE   og-image.jpg  {card.stat().st_size // 1024}KB")
    else:
        print("  ok      og-image.jpg")
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
