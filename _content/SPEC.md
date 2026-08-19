# PGX Builders Group — Landing Page Content Spec

You are writing SEO landing-page content for **PGX Builders Group LLC**, a licensed general contractor
(Lic. CGC1539072) in Miami, FL — phone (786) 273-2524, email pgxbuildersgroup@gmail.com.
Positioning: **high-end residential work only** — whole-home remodels, additions, kitchens, baths,
outdoor living — permitted, supervised daily, built to South Florida code. Tone of the existing site:
confident, concrete, a little dry-witted, zero fluff. Example lines from the live site:

- "Your home, remade."
- "We don't chase every kind of job. We remodel, extend, and upgrade existing homes — and we handle the paperwork that makes it legal."
- "…a home that works the way you live now — not the way it was drawn in 1975."
- "A remodel is a promise. We keep it in writing."
- "…with the waterproofing details that nobody sees but everybody regrets skipping."

## Your task

For ONE assigned area, produce a single JSON file at `_content/<area-slug>.json` containing unique
content for 5 pages (one per service). Research the area first (WebSearch) to verify: permitting
jurisdiction and any design-review boards, real neighborhood names, housing stock eras and styles,
and anything locally distinctive (historic districts, flood/FEMA context, HOA/association rules,
condo milestone-inspection context, logistics quirks). The `hints` field in `_content/site_plan.json`
gives leads — verify before asserting; drop anything you can't confirm.

## JSON file format (exact)

```json
{
  "area_slug": "<slug>",
  "neighborhoods": ["Name", "..."],
  "pages": {
    "home-remodeling":    { <page object> },
    "kitchen-remodeling": { <page object> },
    "bathroom-remodeling":{ <page object> },
    "home-additions":     { <page object> },
    "outdoor-living":     { <page object> }
  }
}
```

`neighborhoods`: 8–14 real neighborhood/street/community names inside the area (used as chips on all
5 pages). For condo-dominant areas, notable buildings/communities count.

Each `<page object>`:

```json
{
  "title": "...",
  "meta_description": "...",
  "h1": "...",
  "hero_sub": "...",
  "local_heading": "...",
  "intro_paragraphs": ["...", "...", "..."],
  "scope_heading": "...",
  "scope_intro": "...",
  "scope_items": [ {"name": "...", "desc": "..."}, ... 5 items ],
  "faqs": [ {"q": "...", "a": "..."}, ... 5 items ],
  "cta_heading": "...",
  "cta_sub": "..."
}
```

## Field rules

- **title** — 45–62 chars. Include service + area + "FL" or "Miami" naturally. End with `| PGX Builders`
  or `| PGX Builders Group` if it fits. Vary sentence shape across your 5 pages (don't use one formula).
- **meta_description** — 130–165 chars. Service + area + one concrete local hook + call to action or
  phone (786) 273-2524. No quote marks.
- **h1** — 4–9 words, NOT identical to title, no trailing period (the template appends a styled period).
  Must read like the existing site's display headlines: punchy, not keyword-stuffed.
- **hero_sub** — 20–40 words. What PGX does for this service in this specific area. Mention licensing/
  permits/supervision naturally.
- **local_heading** — 4–10 words, display headline for the local-expertise section, no trailing period.
- **intro_paragraphs** — exactly 3 paragraphs, 60–110 words each. This is the SEO core; it must be
  genuinely area-specific:
  - P1: the local housing stock and what owners of high-end homes there actually do for this service —
    name real neighborhoods, home eras, architectural styles.
  - P2: permitting and rules in THIS jurisdiction — name the building department, any design review
    board / historic board / HOA-association reality, HVHZ product approvals, flood elevation or FEMA
    substantial-improvement rules where genuinely relevant (waterfront/barrier islands), condo
    association + milestone-inspection context for condo areas.
  - P3: the high-end PGX angle — fixed written scope, daily site supervision, protection of finishes,
    discretion in gated/estate settings, one accountable team from estimate to warranty.
- **scope_heading** — 4–10 words, display headline, no trailing period. **scope_intro** — 15–35 words.
- **scope_items** — exactly 5. `name` 2–5 words; `desc` 15–30 words, rewritten fresh for this area
  (never reused verbatim across areas). Ground them in the service angle from site_plan.json.
- **faqs** — exactly 5. `q` is a real question a homeowner in this area would type; `a` is 40–90 words,
  specific and honest. At least 2 of 5 must be area-specific (jurisdiction timelines, design review,
  flood/FEMA, association rules, island logistics…). Never invent statistics, named clients, or exact
  permit fees. Cost questions: answer with honest qualitative framing or wide ranges, positioning PGX
  as a high-end contractor (not the cheap bid).
- **cta_heading** — 4–9 words. **cta_sub** — 15–30 words, invite a walk-through/estimate, mention
  English/Spanish ("in English o en español" is on-brand).

## Hard rules

1. **English only.** (Spanish versions come later.)
2. **Uniqueness**: across your 5 pages, no sentence may repeat. Titles/h1s/metas must all differ.
3. **No fabrication**: no invented project counts, client names, awards, exact fees, or fake reviews.
   PGX's real claims you may reuse: 20+ years building in South Florida, 150+ remodels and additions
   delivered, 100% permitted and inspected work, licensed & insured, Lic. CGC1539072.
4. **High-end positioning without snobbery**: never disparage other areas or "cheap" clients. Signal
   caliber through specifics (custom cabinetry, stone, engineering, design review fluency), not price talk.
5. **No superlative spam**: at most one "best/finest/premier" per page; prefer concrete claims.
6. **Local accuracy beats color**: if unsure a neighborhood or rule is real, leave it out.
7. Plain text only in all fields — no HTML, no markdown, no em-dash overuse. Use "—" sparingly.
8. Write for humans first; the keyword appears naturally in title, h1 or hero_sub, and 1–2 times in
   body copy. Do not stuff.

## Self-check before finishing

- Valid JSON (no trailing commas), exactly 5 pages keyed by the 5 service slugs.
- Counts: 3 intro paragraphs, 5 scope items, 5 FAQs per page; 8–14 neighborhoods.
- Title/meta lengths within range; h1 has no trailing period.
- Every page mentions the area by name in intro_paragraphs; jurisdiction named in P2.
- Return (as your final output) a short summary: area, any facts you could NOT verify and therefore
  omitted or softened.
