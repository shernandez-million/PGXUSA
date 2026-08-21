#!/usr/bin/env python3
"""Generate the full icon set from the real PGX logo.

The wordmark is 2.78:1, so a square icon cannot show all three letters legibly at
16-32px. Small sizes therefore use the P glyph lifted straight out of the logo
path (not a font imitation); larger sizes carry the full wordmark.
"""
import re
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
INK, BG = "#1A1A18", "#F2F1EE"

src = (ROOT / "images" / "pgx-wordmark.svg").read_text()
d = re.search(r'\sd="([^"]+)"', src).group(1)
subs = [x.strip() for x in re.split(r"(?=M)", d) if x.strip()]
P_PATH = subs[0]                      # the P, x 1-237 y 7-281 in path units


def svg(path_d, box, fg, bg=None, pad=0.10):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    side = max(w, h) * (1 + pad * 2)
    cx, cy = x0 + w / 2, y0 + h / 2
    vb = f"{cx - side/2:.2f} {cy - side/2:.2f} {side:.2f} {side:.2f}"
    rect = f'<rect x="{cx - side/2:.2f}" y="{cy - side/2:.2f}" width="{side:.2f}" height="{side:.2f}" fill="{bg}"/>' if bg else ""
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}">\n'
            f'  {rect}<path d="{path_d}" fill="{fg}" fill-rule="evenodd"/>\n</svg>\n')


def raster(svg_text, size, out, tmp="/tmp/_icon.svg"):
    Path(tmp).write_text(svg_text)
    subprocess.run(["qlmanage", "-t", "-s", str(size * 4), "-o", "/tmp", tmp],
                   capture_output=True)
    got = Path("/tmp/_icon.svg.png")
    if not got.exists():
        raise SystemExit(f"render failed for {out}")
    im = Image.open(got).convert("RGBA")
    flat = Image.new("RGB", im.size, BG)
    flat.paste(im, mask=im.split()[3])
    flat.resize((size, size), Image.LANCZOS).save(ROOT / out, "PNG", optimize=True)
    got.unlink()


P_BOX = (1, 7, 237, 281)
FULL_BOX = (0, 0, 875, 298)

# scalable favicon — modern browsers prefer this and it never softens
(ROOT / "favicon.svg").write_text(svg(P_PATH, P_BOX, INK, BG, pad=0.16))

raster(svg(P_PATH, P_BOX, INK, BG, pad=0.16), 32, "favicon-32.png")
raster(svg(P_PATH, P_BOX, INK, BG, pad=0.16), 96, "favicon-96.png")
raster(svg(d, FULL_BOX, INK, BG, pad=0.18), 192, "favicon.png")
raster(svg(d, FULL_BOX, INK, BG, pad=0.18), 512, "icon-512.png")
# iOS masks and darkens light icons, so the home-screen tile is inverted
raster(svg(d, FULL_BOX, BG, INK, pad=0.18), 180, "apple-touch-icon.png")

for f in ["favicon.svg", "favicon-32.png", "favicon-96.png", "favicon.png",
          "icon-512.png", "apple-touch-icon.png"]:
    print(f"  {f}  {(ROOT / f).stat().st_size // 1024}KB")
