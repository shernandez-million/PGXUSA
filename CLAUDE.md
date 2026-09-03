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

### Never guarantee a decision PGX does not make
Copy may promise what PGX **does** — files complete drawings, prepares for and attends
inspections, builds a package meant to clear review without a second round. It may not
promise what an inspector, a board or a building department will **decide**. "Inspections
that pass first", "drawings the city will approve", "finishes your association will
approve" were all live; they guarantee a third party's judgement PGX has no control over,
and one failed inspection makes the page a liar. Softened 2026-09-01 across 10 packs and
the shared template (520 pages carried "inspections passed on the first visit").

### Dated claims that must be re-verified, not trusted
Two live claims depend on law that can move. Re-check before relying on them:
- **HB 803** (signed 2026-05-07, effective 2026-07-01): exempts qualifying single-family
  work under $7,500 from permit, carving out electrical, plumbing, mechanical, gas and
  structural work and anything in a flood hazard area, and forbidding splitting a project
  to fit under it. Verified accurate 2026-09-01. It reaches **single-family dwellings
  only** — which is why Aventura's condo pages still state the city's own $500 threshold
  and now say explicitly that the state exemption does not reach condominium units.
- **Aventura's $500 permit threshold** — a municipal figure, unverified against the city
  code, correct in context but the kind of number that moves.
No page may state a permit **review time in days**. Miami Shores carried "15 business
days" until 2026-09-01; it now says the Village publishes a target turnaround.

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
python3 _content/audit.py                # duplicates, title case, and the forbidden-claim guard
python3 _content/make_og.py              # share images: site card + per-service (--force rebuilds)
```

### Three rules that will bite you
1. **`template-es.html` is generated.** Editing `template.html` silently
   desynchronizes it. `make_template_es.py` holds an exact-match replacement
   list with expected hit counts and **fails loudly on drift** — that is
   deliberate. When it fails, update its list; never delete the count check.
   It has already caught two real desyncs (an `h4`→`p` change and a footer
   domain change). It also compares both templates after generating and refuses
   to write when a sentence-length phrase survives untranslated — added after
   new English form errors passed straight through onto 262 Spanish pages.
2. **`index.html` and `es.html` are hand-maintained**, except the area chips
   between `<!-- AREAS:START -->` / `<!-- AREAS:END -->`, which `build.py`
   rewrites. Keep the markers.
3. **`--force` renders despite validation errors. It is preview-only.**
   Never publish a `--force` build.

### The audit guards the two claims that already shipped wrong
`audit.py` fails on the BORA false contrast and on any sentence saying an
inspection clock *starts* or *repeats* at a number. Naming the programme the way
owners say it ("the one everyone still calls the 40-year recertification") is
deliberately allowed — only asserted thresholds are defects. Both checks replaced
one-off correction scripts that nobody would have remembered to run.

### The Spanish was transcreated, then audited line by line
All 42 area packs were read by a native Miami reader against their English twins
in 2026-08, every proposal re-read by a second reviewer with authority to reject:
**640 corrections** applied. The defects were not stylistic — they were calques
that changed meaning ("subsuelo acústico" for underlayment, "pista de despegue"
for lead time, "marcapasos" for a schedule driver, "salir a flote" for surfacing
at resale, which means roughly the opposite), plus two invented facts: a street
number Davie's English never claims, and a written-warranty promise in Wilton
Manors that the English does not make.

Two lessons worth keeping:
- **A reviewer sees one pack and its twin, so it cannot know site policy.** One
  proposed deleting "habitables" from the milestone threshold because the English
  says plainly "three or more stories". The Spanish was right and the English
  lagged. `apply_es_fixes.py` vetoes that class of change regardless of what a
  reviewer proposes.
- **Regexes miss what reading catches.** A scan for peninsular vocabulary came
  back clean; the readers then found "manitas". Both passes are worth running.

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
  manifest, and OG share images — `make_favicons.py` for the icon set,
  `make_og.py` for the share cards. Both rasterise `images/pgx-wordmark.svg`.
  **Never draw the wordmark with a font.** The retired `make_brand_assets.py`
  set it in system Didot, which is a different mark (different G spur, different
  X terminals), and shipped it on the site-wide share card — the most-shared
  image on the site — until 2026-08-30. That script is deleted; do not
  reintroduce a font-drawn mark.

### Performance is at its floor — do not chase the LCP numbers
Investigated 2026-09-02 and found nothing worth shipping. Recorded so it is not
re-run:
- **The "area pages are slower than hubs" gap is measurement noise.** It looked
  like LCP 2.5s vs 1.5s. Both classes render from the same template, preload the
  same hero (`images/kitchen.webp`, same srcset), carry the same three preloads
  and three images — and the hub is the *heavier* page (59KB vs 54KB HTML, 3,671
  vs 3,040 words). Fetching each page class four times gave medians within 20ms of
  each other, and three consecutive Lighthouse runs on the *same* area page
  returned perf 98–99 / LCP 2.1–2.3s where an earlier run had said 96–97 /
  2.5–2.7s. Always re-measure before believing a gap between two single runs.
- **Do not "optimize" the wordmark SVGs.** Trimming coordinates from two decimals
  to one saves 15% raw / 21% gzipped — about 1.4KB per file — on two requests that
  do not gate LCP. But `pgx-wordmark-outline.svg` is a 1.4-unit hairline stroke
  whose centreline *is* those coordinates; rendered at the footer mark's ~1120px
  it moves antialiasing on up to 79% of its stroke pixels. Negligible gain,
  unprovable visual equivalence, on a brand asset. Tried and reverted.
- Do not add a preload for the nav wordmark either: it would compete for bandwidth
  with the hero preload, which is the actual LCP element.

### Keyboard access is part of done, and Lighthouse does not measure it
Lighthouse scores accessibility 100 on every page and still missed all three of
these, found by driving the pages by keyboard in 2026-09:
- **Every page carries a skip link** as its first focusable element, off-screen
  until focused, targeting `<main id="top">`. Without it a keyboard user tabs the
  whole header on all 524 pages.
- **`:focus-visible` must survive.** The site's ring is `2px solid var(--brass)`.
  A component rule that sets `outline:none` on plain `:focus` strips it for
  keyboard users too — that is what happened to the form fields, which were left
  with only a 1px border tint. Component styling goes on `:focus`; the ring is
  restored on `:focus-visible`.
- **Icon-only and abbreviation links need a name.** The language toggle read as a
  bare "ES" / "EN" to a screen reader until it got an `aria-label`.

The same trap bit twice more. Verified 2026-09-02 that the **mobile menu works**:
`aria-expanded` flips, `body.menu-open` is set, the closed menu is
`visibility:hidden` so its seven links are correctly out of the tab order, and a
probe element with the same class in the same open body computes
`visibility:visible; opacity:1`. It only *reads* hidden because a backgrounded
page does not run its 0.4s transition, so animated properties stay at their start
values. **Probe the cascade with a fresh element before concluding an animated
component is broken.**

Caution when testing focus: if the browser pane is backgrounded,
`document.hasFocus()` is false and `:focus` styles legitimately do not paint. That
looks exactly like a missing focus indicator and is not one — check
`document.hasFocus()` before believing it.

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

**This repository is not Andrés's own account.** The remote is
`github.com/shernandez-million/PGXUSA`. Anything committed here is visible to
whoever holds access to that account, and git history keeps it after a delete.
**No house skill is committed here** — not `working-with-andres`, and not
`apex` / `flagship` / `metaprompt` / `prompt-architect` either. Fleet rule ratified
2026-09-02 after the question was raised from this repo: house skills reach cloud
sessions through the owner's own private `apex-casa` repo, never through a project
or third-party one. `working-with-andres` is internal Claude material about Andrés
personally and never goes anywhere. `flagship` additionally would not even work
here: 32 absolute paths and 23 references to files outside any repo, so it fails on
first read in a sandbox.

What a cloud session needs from PGX is already in the repo and travels fine: this
file, and the eight project agents in `.claude/agents/`. Those are repo-owned and
stay.

Deploy is Vercel serving the repo directly — no build command, no output
directory. `_content/` is excluded via `.vercelignore` and disallowed in
`robots.txt`. **Andrés handles DNS and the registrar himself** — diagnose DNS
precisely and hand him the exact fix; never touch it.

### Launching a large agent sweep
When a pass needs many subagents on the same brief — the Spanish audit ran 100 —
put the shared brief first, **byte-identical** in every prompt, and launch the
instances inside the same few minutes. The identical prefix is then a cache read
instead of a cache write on every start after the first. Keep the structured
return small. (D-020 PGX-03, 2026-09-03.)

### §3 is the canonical home of the brand values — do not turn it into a pointer
An optimisation pass proposed replacing §3 with a pointer to
`~/.claude/skills/flagship/LEY.md` and `proyectos/pgx.md`, to save context. It was
checked and rejected 2026-09-03: none of the exact tokens (`#9A7B4F`, `#F2F1EE`,
`#1A1A18`, `#E8E4DA`, `#7A5F3A`, `#C9A86C`, `#6B6862`) appear in either
destination, nor does the `ch` ban as a rule. And `pgx.md` §3 is itself titled
"Marca (punteros; los valores se leen en el repo, nunca se retipean)" — the
Flagship dossier deliberately points *here*. Pointing back would be circular and
the values would live nowhere. If that direction is ever reversed, write the
values into LEY.md first.

### Messages to Andrés are a card, not a narrative
Standing order 2026-09-03: he does not read running commentary — "no me da valor
agregado… los canales quedan overwhelmed". Every message to him is this template
verbatim, properly formatted, identical across all chats, with nothing before or
after it:

    📌 **<Proyecto>** — <qué se está haciendo, una línea>

    | Etapa | Agentes | Progreso | Faltan |
    |---|---|---|---|
    | <análisis/plan/ejecución/revisión/deploy/QA> | <n> | <n> % | ~<h> h |

    **⚠️ Tus pendientes**
    1. <solo acciones SUYAS, con instrucción exacta y link>
    (o `ninguno`)

    **🌐 Subido** · <URL>
    **💻 Local** · <URL | apagado — di «preview»>

The pendientes list answers exactly one question — "what do I need to do?" — so it
carries **only actions that are his**, each with its exact instruction and link.
Claude's own to-do list never appears there.

Findings, decisions and reasoning go **here, in this file**, or into the batch
report — never into his chat. The only things that may break the format are a real
stopper and a question only he can answer. Percentage is measured against the
meta-prompt checklist; hours are honest estimates, corrected on each card.

### The two links that close every message
Standing order 2026-09-03: every message to Andrés ends with these two lines,
after the ⚠️ block, so he can click without hunting back through the thread.

```
🌐 Subido: https://www.pgxusa.com
💻 Local: http://localhost:8080   ← only when a preview is actually running
```

The first link is where the work you just built is deployed. **In this repo that
is the production domain**, because the publish policy is straight to `main` and
Vercel serves `main` at `https://www.pgxusa.com` with no build step — there is no
staging or preview-branch deploy to point at instead. The apex redirects there
with a 308, and it is the URL he opens. Never paste a link that is not live, and
never invent one. When no preview is running — the normal state, since dev servers live
only while he is watching — the second line reads
`💻 Local: apagado — di «preview» y lo levanto` instead. The local port is 8080
(`python3 _content/serve.py 8080`, or the `pgx` entry in `.claude/launch.json`).

### Definition of done
1. `build.py --check-only` clean, `audit.py` clean.
2. Language twin, hreflang pair, and sitemap alternates all exist.
3. Mobile verified at **390pt and 430pt** (iPhone Pro / Pro Max) by actually
   scrolling — no horizontal scroll, ever.
4. Lighthouse mobile: performance ≥95, a11y/best-practices/SEO 100.
5. **Do not bulk-crawl production with curl.** Sweeping all 524 URLs in parallel trips
   Vercel's bot mitigation: every request then returns `403` with
   `x-vercel-mitigated: challenge` and a "Vercel Security Checkpoint" body, which looks
   exactly like a site-wide outage and is not one. A real browser solves the JS challenge
   and loads normally. Verify deploys through the browser tools, or with a handful of
   spaced single requests — never a parallel sweep.
6. **Verified on the live URL the way he will load it** — fresh, at
   `https://www.pgxusa.com`. This is his #1 trust-breaker. Poll until the
   deploy is confirmed live *before* auditing; Lighthouse has already been run
   against a stale deploy here and reported fixed things as broken.

### The estimate form is a mailto, and that is a known ceiling
The form on every page builds a `mailto:` and hands off to the visitor's mail
app. It validates first (name, plus a phone or an email, plus a sane email
format), announces errors through `role="alert"`, and always reveals the email
address and WhatsApp link afterwards — because a machine with no mail client
handles `mailto:` silently and the visitor would otherwise think nothing
happened.

It still depends on the visitor pressing Send in their own mail app, and nothing
is recorded on PGX's side. Capturing every submission needs a form backend
(a serverless function plus an email service, or a hosted form provider), which
means an account and probably a subscription — **Andrés's call, not Claude's**.
Until he decides, do not silently swap in a third-party endpoint: it would send
prospect data to a service he never chose.

`index.html` and `es.html` carry their own copy of this form. Any change to the
template's form must be applied to those two by hand.

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
- **Real vector logo.** `images/pgx-wordmark.svg` originates from a bitmap trace
  (364 straight `L` segments, no curves). `smooth_logo.py` refit it to 348 cubic
  Béziers, keeping real corners sharp, so it no longer looks hand-drawn — but it
  is still a trace of a raster, not a drawn master. A true vector original from
  the designer would end the problem for good.
- **Portfolio photos** and **About details** (founder, founding year, team,
  certifications). The About page was written without inventing a founder story
  precisely because these are missing.

---

## 7. The expert team

The repo has a persisted expert roster in `.claude/agents/` — eight agents,
each one the owner of a section of this constitution (claims, brand, SEO,
Spanish, pipeline, performance, QA, positioning). **TEAM.md** mirrors the
directory 1:1 and says who reviews what and who vetoes what; consult the
relevant agents before touching their domain — a change that skips its owner
is how the incidents in this file happened in the first place.

Constituted 2026-09-01 by APEX on Andrés's direct order to apply APEX to every
running project (Método Muñoz §2 — the team is constituted before building and
persists across requirements). Universal experts (prompting, orchestration,
the critics' jury) are account-level and convened per pass, not duplicated
here.
