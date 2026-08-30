# PGX Builders Group — repo constitution

Law for this repository. Extends Andrés's cross-project standards; on any direct
conflict with them, this file wins here. Every rule below exists because it was
decided or corrected in a real session — none are preferences invented by Claude.
When Andrés hands down a new durable decision, append it here **the same session**.

---

## 1. The business (never invent, never soften)

| Fact | Value |
|---|---|
| Legal name | PGX Builders Group LLC |
| Brand shown to users | **PGX** (the wordmark is the "PGX" mark alone) |
| Canonical domain | **https://www.pgxusa.com** |
| Email | connect@pgxusa.com |
| Phone | (786) 273-2524 · `+17862732524` |
| License | CGC1539072 |
| Counties served | Miami-Dade & Broward |

`_content/site_plan.json` is the single source of truth for all of the above.
Never hardcode a business fact into a template or a page — read it from the plan.

### Positioning is a hard filter
High-end only. Andrés's words: *"I don't wanna build homes in Hialeah… I wanna
sell high ticket transactions. I don't wanna do, like, cheap and affordable jobs."*
The 42 areas in the plan were selected against that filter. **Do not add an area
because it would rank** — adding a low-value municipality is a positioning
violation, not a growth tactic. New areas need his sign-off.

### The only claims that may appear in copy
20+ years · 150+ remodels and additions · 100% permitted and inspected ·
licensed & insured · Lic. CGC1539072.

Everything else is forbidden. Specifically **never** write: permit fees, review
times in days, statutory deadlines, client names, project addresses, awards,
testimonials, star ratings, employee counts, or revenue. Milestone/SIRS
thresholds have moved three times since 2022 — describe obligations
qualitatively, never with numbers or dates.

> **The BORA incident (why this rule is absolute).** Claude briefed content
> agents that Broward has a county Board of Rules and Appeals that Miami-Dade
> lacks. That is false — Miami-Dade has one under Code ch. 8 §8-4. The invented
> contrast reached **56 strings across 37 files in both languages** before an
> agent flagged it, and took a 7-agent correction pass to remove. A single
> unverified "fact" in a briefing multiplies by the number of pages. Verify
> against a primary source before it enters a prompt, not after.

### Building-inspection claims carry no numbers
Milestone inspections, structural integrity reserve studies and county
recertification are **described qualitatively, never with numbers**. No trigger
age, no cycle length, no deadline, no dollar threshold. The statute has been
rewritten three times since 2022 (SB 4-D 2022, SB 154 2023, HB 913 2025) and a
static page cannot track it. HB 913 also narrowed the threshold to three
**habitable** stories, which is why the corpus says "habitable" everywhere.

One real error this rule would have prevented: Weston's pages told Bonaventure
owners their safety-inspection clock "starts at 25 years". Broward's BORA Policy
05-05 applies the earlier trigger to condominium buildings within three miles of
the coastline; **Weston is inland**, so the page stated a deadline earlier than
the one that governs those owners. Corrected 2026-08-30 by removing the numbers,
not by substituting today's.

---

## 2. Architecture

```
_content/site_plan.json     domain, business, 6 services, 42 areas   ← source of truth
_content/<area>.json        EN content pack   (6 services per file)
_content/<area>.es.json     ES content pack   (transcreated, not translated)
_content/hub-<service>.json service hub packs (+ .es.json)
_content/page-about.json    About page pack   (+ .es.json)
_content/type-<slug>.json   property-type pack (+ .es.json)  ← cross-cutting pages
_content/template.html      EN landing template  ({{TOKEN}} placeholders)
_content/template-es.html   ES landing template  ← GENERATED, never hand-edit
_content/build.py           renderer + validator + sitemap
```

**524 URLs** = 42 areas × 6 services × 2 languages (504) + 12 hubs + 2 About
+ 2 area indexes + 2 homepages + 2 property-type pages.

### Property types are not services
A property type (condominium) cuts across all six services. It lives in
`site_plan.json` under `property_types`, **never** under `services` — putting it
there would push it into the service navigation, the footer and the contact-form
dropdown on all 522 existing pages. `render_collection()` renders it, and area
pages listed in a type's `areas` automatically gain a chip linking to it. An
expert panel rejected two further types in 2026-08: **waterfront** (a
jurisdictional condition already written into 25 area files, not a property
type) and **historic** (designation is parcel-by-parcel, so a market-wide page
would be wrong for most readers). Do not revive them without new evidence.

### Commands
```bash
python3 _content/build.py --check-only   # validate without writing
python3 _content/build.py                # render everything + sitemap
python3 _content/make_template_es.py     # regenerate the ES template
python3 _content/audit.py                # links, schema, duplicate-title sweep
python3 _content/make_og.py              # per-service social thumbnails (add --force to rebuild)
```

### Three rules that will bite you
1. **`template-es.html` is generated.** Editing `template.html` silently
   desynchronizes it. `make_template_es.py` holds an exact-match replacement
   list with expected hit counts and **fails loudly on drift** — that is
   deliberate. When it fails, update its list; never delete the count check.
   It has already caught two real desyncs (an `h4`→`p` change and a footer
   domain change).
2. **`index.html` and `es.html` are hand-maintained**, except the area chips
   between `<!-- AREAS:START -->` / `<!-- AREAS:END -->`, which `build.py`
   rewrites. Keep the markers.
3. **`--force` renders despite validation errors. It is preview-only.**
   Never publish a `--force` build.

### Bilingual is atomic
A page does not exist until its twin exists. Every EN page needs its ES page,
reciprocal `hreflang` (plus `x-default`), and both sitemap entries with
`<xhtml:link>` alternates. Spanish uses **Spanish URL slugs**
(`/remodelacion-de-cocinas-weston`), Miami/Latin-American register, **usted**,
never Spain Spanish. Transcreate — a literal translation of English marketing
copy reads wrong and Andrés will catch it.

### Schema
One entity, referenced everywhere: `https://www.pgxusa.com/#business`
(`GeneralContractor`). All 520 landing pages `@id`-reference that node rather
than redeclaring the business — that is what makes it an entity graph instead
of 520 unrelated blobs. Do not let a page invent a second business node.

---

## 3. Brand and design law

Tokens live in `:root`. Use the variables; never a raw hex.

```
--bg #F2F1EE   --bg-soft #E8E4DA   --ink #1A1A18   --ink-2 #6B6862
--brass #9A7B4F   --brass-ink #7A5F3A   --d-brass #C9A86C
--serif 'Marcellus', Georgia, serif        body: Inter
```

**Two typefaces only: Marcellus (display) and Inter (body).**

- **Marcellus ships a single weight.** Every serif rule must be
  `font-weight:400`. Any higher value produces synthetic faux-bold and looks
  cheap. Rejected before Marcellus: Bodoni Moda (*"I don't like it at all"*).
- **Scrims are neutral black and light.** Current hero:
  `.52 → .37 → .16 → .03 → 0` horizontally, plus light top/bottom passes.
  Andrés corrected this **four times** — *"it should be black right now. It's
  like brownish, and it's too dark."* Never use a warm/tinted black
  (`rgba(14,13,11,…)` was the offence). When tuning, **err light**; expect
  "a little bit more" nudges. The image must never look dark.
- **Hero is full-bleed, edge to edge**, image uncropped enough to read the whole
  house — not a right-side card. The value proposition sits above the fold and
  no panel covers the image.
- **The logo is the "PGX" wordmark alone** — no "Builders Group LLC". It renders
  through a CSS mask (`-webkit-mask:url(images/pgx-wordmark.svg)` +
  `background-color`) so it inherits its context color instead of shipping one
  PNG per background. Size it prominently; a small logo is a defect.
- **Every page carries 2–4 photographs.** Text-only pages read as unfinished.
  Supporting images are additional framings of the *same* room, drawn from
  different regions of the source photo — never another page's photo.
- **A logo change propagates in the same pass**: site styling, favicon, icons,
  manifest, and OG share images. (`make_favicons.py`, `make_brand_assets.py`.)

### Never size text containers in `ch`
`ch` is the width of the font's `0` glyph, so a `ch` box changes size when the
webfont swaps in. Marcellus's `0` is **24% wider than Georgia's**, so every
headline box was a quarter narrower during fallback, rewrapped on swap, and
jumped the page: **CLS 0 → 0.077**. Lighthouse blamed the images; the images
were innocent. All widths are now `em`, which scales with font-size but not
with font metrics. **CLS 0.001.** Do not reintroduce `ch`.

---

## 4. Shipping

**Publishing after each finished batch is pre-authorized by Andrés for this
project.** Never publish a `--force` build, a build with validation errors, or a
page whose language twin is missing.

Deploy is Vercel serving the repo directly — no build command, no output
directory. `_content/` is excluded via `.vercelignore` and disallowed in
`robots.txt`. **Andrés handles DNS and the registrar himself** — diagnose DNS
precisely and hand him the exact fix; never touch it.

### Definition of done
1. `build.py --check-only` clean, `audit.py` clean.
2. Language twin, hreflang pair, and sitemap alternates all exist.
3. Mobile verified at **390pt and 430pt** (iPhone Pro / Pro Max) by actually
   scrolling — no horizontal scroll, ever.
4. Lighthouse mobile: performance ≥95, a11y/best-practices/SEO 100.
5. **Verified on the live URL the way he will load it** — fresh, at
   `https://www.pgxusa.com`. This is his #1 trust-breaker. Poll until the
   deploy is confirmed live *before* auditing; Lighthouse has already been run
   against a stale deploy here and reported fixed things as broken.

---

## 5. Portfolio — deliberately unpublished

`_content/projects.json` is empty except a `_TEMPLATE`. The portfolio page is
**not built below 3 real projects**. This is intentional: a portfolio with
placeholder or stock projects is worse than no portfolio for a contractor whose
entire pitch is proof of work. Publishing it needs real photos, real details,
and confirmed client permission — all of which only Andrés can supply.

---

## 6. Open items only Andrés can close

- **Google Business Profile does not exist.** The business has essentially no
  web footprint outside this site. The map pack outranks organic results for
  "contractor near me", so 522 pages cannot reach that traffic. Highest-return
  action available. When it exists, wire it into the schema `sameAs`.
- **Sitemap resubmission** in Search Console: `https://www.pgxusa.com/sitemap.xml`.
- **Real vector logo.** The current SVG is a bitmap trace — 364 `L` commands and
  zero curves, refit by `smooth_logo.py` to remove the hand-drawn wobble. A true
  vector master would end the problem. (Check: real vectors show `C` commands
  with decimals; traces show `L` with whole numbers.)
- **Portfolio photos** and **About details** (founder, founding year, team,
  certifications). The About page was written without inventing a founder story
  precisely because these are missing.
