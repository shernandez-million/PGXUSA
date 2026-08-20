#!/usr/bin/env python3
"""Convert the split hero (text left / image card right) into a full-bleed media hero
with the headline set over the photograph, and enlarge the wordmark.

Applies to the landing template and both homepages. The plain `.hero` class is left
intact because the /areas and /zonas index pages use it without a photograph.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = [ROOT / "_content" / "template.html", ROOT / "index.html", ROOT / "es.html"]

HERO_CSS = """
/* ---------- full-bleed media hero ---------- */
.hero-media{
  position:relative;display:flex;align-items:flex-end;overflow:hidden;
  min-height:clamp(500px,74svh,720px);
  padding:calc(84px + clamp(30px,6vw,72px)) 0 clamp(40px,5vw,66px);
  background:var(--d-bg);
}
.hero-media .hero-bg{position:absolute;inset:0;z-index:0}
.hero-media .hero-bg img{width:100%;height:100%;object-fit:cover;display:block}
.hero-media .hero-bg::after{
  content:"";position:absolute;inset:0;
  background:
    linear-gradient(90deg,rgba(14,13,11,.90) 0%,rgba(14,13,11,.72) 38%,rgba(14,13,11,.32) 70%,rgba(14,13,11,.10) 100%),
    linear-gradient(0deg,rgba(14,13,11,.55) 0%,rgba(14,13,11,0) 58%);
}
.hero-media .hero-in{position:relative;z-index:1;width:100%}
.hero-media .h1{color:var(--d-ink)}
.hero-media .eyebrow{color:var(--d-brass)}
.hero-media .eyebrow::before{background:var(--d-brass)}
.hero-media .hero-sub{color:rgba(242,241,238,.86);max-width:50ch}
.hero-media .hero-meta{color:rgba(242,241,238,.74);margin-top:32px}
.hero-media .hero-cta{margin-top:30px}
.hero-media .crumbs,.hero-media .crumbs a{color:rgba(242,241,238,.68)}
.hero-media .crumbs a:hover{color:var(--d-ink)}
.hero-media .crumbs .sep{color:rgba(242,241,238,.32)}
.hero-media .btn-solid{background:var(--bg);color:var(--ink)}
.hero-media .btn-solid:hover{background:#FFFFFF}
.hero-media .btn-ghost{border-color:rgba(242,241,238,.5);color:var(--d-ink)}
.hero-media .btn-ghost:hover{border-color:var(--d-ink);background:rgba(242,241,238,.08)}
/* the nav floats over the photograph until the page is scrolled */
body:has(.hero-media) .nav:not(.on) .brand .wm{color:var(--d-ink)}
body:has(.hero-media) .nav:not(.on) .nav-links a{color:var(--d-ink)}
body:has(.hero-media) .nav:not(.on) .lang{color:rgba(242,241,238,.78)}
body:has(.hero-media) .nav:not(.on) .lang:hover{color:var(--d-ink)}
body:has(.hero-media) .nav:not(.on) .burger span{background:var(--d-ink)}
body:has(.hero-media) .nav:not(.on) .btn-solid{background:var(--bg);color:var(--ink)}
/* start the next section high enough that it is visible without scrolling */
.hero-media + .sec{padding-top:clamp(52px,6vw,86px)}
@media(max-width:760px){
  .hero-media{min-height:clamp(470px,66svh,620px);padding-top:calc(72px + 34px)}
  .hero-media .hero-bg::after{
    background:linear-gradient(0deg,rgba(14,13,11,.90) 0%,rgba(14,13,11,.58) 48%,rgba(14,13,11,.32) 100%);
  }
  .hero-media .hero-sub{max-width:38ch}
}
"""

# a wordmark that actually reads as the logo, not a caption
WM_SIZE = [
    (".brand .wm{font-family:var(--serif);font-weight:400;font-size:31px;letter-spacing:.055em;line-height:1;color:var(--ink)}",
     ".brand .wm{font-family:var(--serif);font-weight:400;font-size:clamp(34px,3.3vw,42px);"
     "letter-spacing:.05em;line-height:1;color:var(--ink)}"),
    (".ft-brand .wm{font-family:var(--serif);font-weight:400;font-size:34px;letter-spacing:.055em;line-height:1;color:var(--d-ink);display:block;margin-bottom:9px}",
     ".ft-brand .wm{font-family:var(--serif);font-weight:400;font-size:clamp(40px,4vw,52px);"
     "letter-spacing:.05em;line-height:1;color:var(--d-ink);display:block;margin-bottom:12px}"),
    (".nav-in{display:flex;align-items:center;justify-content:space-between;height:76px}",
     ".nav-in{display:flex;align-items:center;justify-content:space-between;height:84px}"),
]

problems = []
for path in TARGETS:
    src = path.read_text()
    if ".hero-media" in src:
        print(f"skipped (already converted): {path.name}")
        continue

    # 1. lift the image out of the figure and mount it as the section background
    fig = re.search(r'<figure class="hero-fig[^"]*">\s*(<img [^>]*>)\s*</figure>\s*', src)
    if not fig:
        problems.append(f"{path.name}: hero figure not found")
        continue
    img = fig.group(1)
    if "loading=" not in img:
        img = img.replace("<img ", '<img fetchpriority="high" ', 1) if "fetchpriority" not in img else img
    src = src[:fig.start()] + src[fig.end():]

    # 2. restructure the section
    if src.count('<section class="hero">') != 1:
        problems.append(f"{path.name}: expected exactly one hero section")
        continue
    src = src.replace(
        '<section class="hero">',
        f'<section class="hero hero-media">\n  <div class="hero-bg">{img}</div>', 1)
    if src.count('<div class="wrap hero-grid">') != 1:
        problems.append(f"{path.name}: hero-grid wrapper not found")
        continue
    src = src.replace('<div class="wrap hero-grid">', '<div class="wrap hero-in">', 1)

    # 3. styles
    for old, new in WM_SIZE:
        if old not in src:
            problems.append(f"{path.name}: wordmark rule not found :: {old[:50]}")
            continue
        src = src.replace(old, new)
    src = src.replace("</style>", HERO_CSS + "</style>", 1)

    path.write_text(src)
    print(f"converted: {path.name}")

if problems:
    print("\nPROBLEMS:")
    for p in problems:
        print("  -", p)
    sys.exit(1)
