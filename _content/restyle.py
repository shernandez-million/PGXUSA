#!/usr/bin/env python3
"""Apply the 2026 PGX brand system (Bodoni Moda wordmark + brass accent) to every
hand-maintained HTML file: the master landing template and the two homepages.

Each replacement declares how many matches it expects, so silent drift fails loudly
instead of shipping a half-restyled page. Re-runnable: already-restyled files are
detected and skipped.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = [ROOT / "_content" / "template.html", ROOT / "index.html", ROOT / "es.html"]

FONT_LINK_OLD = ('<link href="https://fonts.googleapis.com/css2?family=Archivo:ital,wdth,wght@0,62..125,100..900'
                 '&amp;family=Inter:wght@400;500;600&amp;display=swap" rel="stylesheet">')
FONT_LINK_NEW = ('<link href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:opsz,wght@6..96,400..600'
                 '&amp;family=Inter:wght@400;500;600&amp;display=swap" rel="stylesheet">')

ROOT_VARS_NEW = """:root{
  --bg:#F2F1EE;
  --bg-soft:#E8E4DA;
  --ink:#1A1A18;
  --ink-2:#6B6862;
  --line:rgba(26,26,24,.13);
  --line-soft:rgba(26,26,24,.07);
  --brass:#9A7B4F;
  --brass-ink:#7A5F3A;
  --d-brass:#C9A86C;
  --white:#FFFFFF;
  --d-bg:#161513;
  --d-ink:#F2F1EE;
  --d-ink-2:#A8A49B;
  --d-line:rgba(242,241,238,.14);
  --serif:'Bodoni Moda',Didot,'Times New Roman',serif;
  --r-card:14px;
  --r-block:10px;
  --pill:999px;
  --w:1300px;
  --pad:clamp(20px,4vw,56px);
  --ease:cubic-bezier(.16,1,.3,1);
}"""

# (pattern, replacement, expected_count_per_file, is_regex)
REPL = [
    (FONT_LINK_OLD, FONT_LINK_NEW, 1, False),

    # ---- display type: Didone, not wide grotesque ----
    ("""".disp{
  font-family:'Archivo',Inter,sans-serif;
  font-stretch:118%;
  font-weight:640;
  letter-spacing:-.015em;
  line-height:.98;
}""".strip('"'), """.disp{
  font-family:var(--serif);
  font-weight:500;
  font-optical-sizing:auto;
  letter-spacing:-.005em;
  line-height:1.03;
}""", 1, False),

    # large display elements -> serif
    (".m-menu a{font-family:'Archivo',sans-serif;font-stretch:118%;font-weight:640;",
     ".m-menu a{font-family:var(--serif);font-weight:500;", 1, False),
    (".stat .n{font-family:'Archivo',sans-serif;font-stretch:118%;font-weight:640;",
     ".stat .n{font-family:var(--serif);font-weight:500;", 1, False),
    (".prin h3{font-family:'Archivo',sans-serif;font-stretch:118%;font-weight:640;",
     ".prin h3{font-family:var(--serif);font-weight:500;", 1, False),
    (".pr-card h3{font-family:'Archivo',sans-serif;font-stretch:118%;font-weight:640;",
     ".pr-card h3{font-family:var(--serif);font-weight:500;", 1, False),
    (".ct-row .v{overflow-wrap:anywhere;font-family:'Archivo',sans-serif;font-stretch:114%;font-weight:640;",
     ".ct-row .v{overflow-wrap:anywhere;font-family:var(--serif);font-weight:500;", 1, False),
    (".ft-mark{\n  font-family:'Archivo',sans-serif;font-stretch:125%;font-weight:800;letter-spacing:-.02em;",
     ".ft-mark{\n  font-family:var(--serif);font-weight:400;letter-spacing:.02em;", 1, False),

    # small numerals and labels stay in the sans — Didone hairlines vanish at this size
    (".pr-card .n{font-family:'Archivo',sans-serif;font-stretch:118%;font-weight:640;font-size:15px;color:var(--azure-ink);",
     ".pr-card .n{font-weight:600;font-size:12px;letter-spacing:.14em;color:var(--brass-ink);", 1, False),
    (".svc-num{transform:translateY(-2px);font-family:'Archivo',sans-serif;font-stretch:118%;font-weight:600;font-size:15px;",
     ".svc-num{transform:translateY(-2px);font-weight:600;font-size:12px;letter-spacing:.14em;", -1, False),
    (".prin h3 i{font-style:normal;color:var(--azure);font-size:14px;",
     ".prin h3 i{font-style:normal;font-family:Inter,sans-serif;color:var(--brass-ink);font-size:12px;letter-spacing:.12em;", 1, False),

    # ---- the wordmark ----
    (".brand img{width:46px;height:auto}",
     ".brand .wm{font-family:var(--serif);font-weight:400;font-size:31px;letter-spacing:.055em;"
     "line-height:1;color:var(--ink)}", 1, False),
    (".brand .bt{font-family:'Archivo',sans-serif;font-stretch:112%;font-weight:700;font-size:17px;letter-spacing:.01em;line-height:1.1}",
     ".brand .bs{margin-top:5px}", 1, False),
    (".ft-brand img{width:58px;height:auto}",
     ".ft-brand .wm{font-family:var(--serif);font-weight:400;font-size:34px;letter-spacing:.055em;"
     "line-height:1;color:var(--d-ink);display:block;margin-bottom:9px}", 1, False),
    (".ft-brand .t{font-family:'Archivo',sans-serif;font-stretch:112%;font-weight:700;font-size:17px}",
     ".ft-brand .t{font-size:11.5px;font-weight:600;letter-spacing:.15em;text-transform:uppercase;color:var(--d-ink-2)}", 1, False),

    # ---- buttons: solid charcoal, not a colour field ----
    (".btn-azure{background:var(--azure);color:var(--ink)}\n.btn-azure:hover{background:#45A9DF}",
     ".btn-solid{background:var(--ink);color:var(--bg)}\n.btn-solid:hover{background:#33322D}", 1, False),
    (".nav-cta .btn-azure{display:none}", ".nav-cta .btn-solid{display:none}", 1, False),
    ('class="btn btn-azure"', 'class="btn btn-solid"', 2, False),

    # ---- contact band: warm sand instead of a saturated colour block ----
    (".contact{background:var(--azure);color:var(--ink)}",
     ".contact{background:var(--bg-soft);color:var(--ink)}", 1, False),
    (".contact .eyebrow{color:var(--ink)}", ".contact .eyebrow{color:var(--brass-ink)}", 1, False),
    (".contact .eyebrow::before{background:var(--ink)}",
     ".contact .eyebrow::before{background:var(--brass)}", 1, False),
    (".contact .sec-intro{color:rgba(11,12,14,.72)}", ".contact .sec-intro{color:var(--ink-2)}", 1, False),
    (".ct-row{border-top:1px solid rgba(11,12,14,.18);padding:20px 0}",
     ".ct-row{border-top:1px solid var(--line);padding:20px 0}", 1, False),
    (".ct-row .k{font-size:12px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:rgba(11,12,14,.6)}",
     ".ct-row .k{font-size:12px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-2)}", 1, False),
    (".form-card{background:var(--bg);", ".form-card{background:var(--white);", 1, False),

    # ---- accent rename: azure -> brass (order matters, longest first) ----
    ("var(--azure-ink)", "var(--brass-ink)", None, False),
    ("var(--azure)", "var(--brass)", None, False),
    (".dark .eyebrow{color:var(--brass)}", ".dark .eyebrow{color:var(--d-brass)}", 1, False),
    (".stat .n em{font-style:normal;color:var(--brass)}",
     ".stat .n em{font-style:normal;color:var(--d-brass)}", 1, False),
    (".m-menu a:hover{color:var(--brass)}", ".m-menu a:hover{color:var(--d-brass)}", 1, False),
    (".ft-col a:hover{color:var(--brass)}", ".ft-col a:hover{color:var(--d-brass)}", 1, False),
    (".m-menu .mm-tel{margin-top:34px;font-family:Inter;font-stretch:100%;font-size:17px;font-weight:500;color:var(--brass)}",
     ".m-menu .mm-tel{margin-top:34px;font-size:17px;font-weight:500;color:var(--d-brass)}", 1, False),
    (".mm-lang:hover{color:var(--brass)!important}", ".mm-lang:hover{color:var(--d-brass)!important}", -1, False),
    ("::selection{background:var(--brass);color:var(--ink)}",
     "::selection{background:var(--brass);color:var(--white)}", 1, False),
    (".dock a.d-est{background:var(--brass);color:var(--ink)}",
     ".dock a.d-est{background:var(--d-brass);color:var(--d-bg)}", 1, False),

    # ---- selectors that live in only some of the files ----
    ("padding:24px 4px;font-family:'Archivo',sans-serif;font-stretch:114%;font-weight:640;",
     "padding:24px 4px;font-family:var(--serif);font-weight:500;", -1, False),
    ('.fq summary::after{content:"+";font-family:\'Archivo\',sans-serif;font-weight:400;',
     '.fq summary::after{content:"+";font-weight:300;', -1, False),
    (".svc-name{font-family:'Archivo',sans-serif;font-stretch:118%;font-weight:640;",
     ".svc-name{font-family:var(--serif);font-weight:500;", -1, False),
    ("/* ---------- contact (azure) ---------- */", "/* ---------- contact ---------- */", -1, False),

    # ---- section dividers pick up the accent hairline ----
    (".eyebrow::before{content:\"\";width:22px;height:2px;background:var(--brass);border-radius:2px;flex:none}",
     ".eyebrow::before{content:\"\";width:26px;height:1px;background:var(--brass);flex:none}", 1, False),
]

# regex replacements (markup varies between template and homepages)
RE_REPL = [
    # header mark -> wordmark
    (re.compile(r'<img src="(?:images/pgx-mark\.png|data:image/png;base64,[^"]+)" alt="PGX Builders Group mark"[^>]*>\s*'
                r'<span><span class="bt">PGX</span><br><span class="bs">([^<]*)</span></span>'),
     r'<span class="wm">PGX</span>\n      <span class="bs">\1</span>', 1),
    # footer mark -> wordmark
    (re.compile(r'<img src="(?:images/pgx-mark\.png|data:image/png;base64,[^"]+)" alt=""[^>]*>\s*<div>\s*'
                r'<div class="t">PGX Builders Group LLC</div>'),
     '<div>\n        <span class="wm">PGX</span>\n        <div class="t">Builders Group LLC</div>', 1),
]


def restyle(path: Path) -> tuple[bool, list[str]]:
    src = path.read_text()
    if "Bodoni+Moda" in src:
        return False, ["already restyled — skipped"]
    problems, log = [], []

    # whole :root block
    m = re.search(r":root\{.*?\n\}", src, re.S)
    if not m:
        return False, ["could not locate :root block"]
    src = src[:m.start()] + ROOT_VARS_NEW + src[m.end():]

    for old, new, n, _ in REPL:
        c = src.count(old)
        # n is None or -1 -> "replace however many are there"; a number -> must match exactly
        if n is not None and n >= 0 and c != n:
            problems.append(f"expected {n}x, found {c}x :: {old[:64]!r}")
            continue
        if c:
            src = src.replace(old, new)
    for rx, new, n in RE_REPL:
        src, c = rx.subn(new, src)
        if c != n:
            problems.append(f"regex expected {n}x, applied {c}x :: {rx.pattern[:60]!r}")

    for i, line in enumerate(src.splitlines(), 1):
        if any(t in line for t in ("Archivo", "azure", "font-stretch")):
            problems.append(f"leftover line {i}: {line.strip()[:90]}")
    if problems:
        return False, problems
    path.write_text(src)
    return True, log


ok = True
for p in TARGETS:
    changed, msgs = restyle(p)
    status = "restyled" if changed else "NOT WRITTEN"
    print(f"{status}: {p.name}")
    for m in msgs:
        print("   ", m)
    if not changed and msgs and msgs[0] != "already restyled — skipped":
        ok = False
sys.exit(0 if ok else 1)
