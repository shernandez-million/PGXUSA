#!/usr/bin/env python3
"""Regenerate the PGX brand raster assets (favicons + social share image) from the
Didone wordmark. Run after any change to the brand palette.

Didot ships with macOS and is the closest system match to the PGX wordmark; the site
itself sets the mark in Bodoni Moda via webfont, so these rasters only need to read
as the same mark, not to be pixel-identical.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DIDOT = "/System/Library/Fonts/Supplemental/Didot.ttc"
INK = (26, 26, 24)
BG = (242, 241, 238)

SS = 8  # supersample factor — Didone hairlines alias badly without it


def wordmark(size, fg, bg, text="PGX", pad_ratio=0.14, face=0, tracking=0.05):
    """Render `text` centred on a square canvas, optically fitted to the width."""
    W = size * SS
    img = Image.new("RGB", (W, W), bg)
    d = ImageDraw.Draw(img)
    target = W * (1 - 2 * pad_ratio)
    lo, hi, best = 10, W * 2, None
    while lo <= hi:  # binary-search the point size that fills the target width
        mid = (lo + hi) // 2
        f = ImageFont.truetype(DIDOT, mid, index=face)
        track = int(mid * tracking)
        w = sum(d.textlength(c, font=f) for c in text) + track * (len(text) - 1)
        if w <= target:
            best = (mid, f, w, track)
            lo = mid + 1
        else:
            hi = mid - 1
    pt, f, w, track = best
    a = f.getbbox(text)
    h = a[3] - a[1]
    x = (W - w) / 2
    y = (W - h) / 2 - a[1]
    for c in text:  # draw per-glyph so tracking is honoured
        d.text((x, y), c, font=f, fill=fg)
        x += d.textlength(c, font=f) + track
    return img.resize((size, size), Image.LANCZOS)


def social(out, photo, size=(1200, 630)):
    """Hero photo with a wordmark plate, replacing the retired house badge."""
    im = Image.open(photo).convert("RGB")
    sr = max(size[0] / im.width, size[1] / im.height)
    im = im.resize((round(im.width * sr), round(im.height * sr)), Image.LANCZOS)
    l, t = (im.width - size[0]) // 2, (im.height - size[1]) // 2
    im = im.crop((l, t, l + size[0], t + size[1]))

    # the mark stands alone — no descriptor line
    plate_w, plate_h, m = 268, 116, 44
    plate = Image.new("RGB", (plate_w, plate_h), BG)
    mark = wordmark(96, INK, BG, pad_ratio=0.02)
    plate.paste(mark, ((plate_w - 96) // 2, (plate_h - 96) // 2))
    im.paste(plate, (m, size[1] - plate_h - m))
    im.save(out, "JPEG", quality=88, optimize=True, progressive=True)
    return out


if __name__ == "__main__":
    # At tab size three Didone letters collapse into a smudge, so the small icon drops
    # to the initial alone and the full wordmark returns once there is room for it.
    wordmark(32, INK, BG, text="P", face=0, pad_ratio=0.16).save(ROOT / "favicon-32.png")
    wordmark(192, INK, BG, face=0).save(ROOT / "favicon.png")
    wordmark(180, BG, INK, face=0).save(ROOT / "apple-touch-icon.png")
    social(ROOT / "og-image.jpg", ROOT / "images" / "hero.webp")
    for p in ["favicon-32.png", "favicon.png", "apple-touch-icon.png", "og-image.jpg"]:
        print(f"  {p}  {(ROOT / p).stat().st_size // 1024}KB")
