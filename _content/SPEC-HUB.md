# PGX — Service Hub Page Spec

You are writing ONE service hub page for PGX Builders Group LLC, in BOTH English and Spanish.

A hub is the parent page for a service across the whole market. It targets the head term
("kitchen remodeling Miami", "general contractor Miami-Dade"), and links out to all 42 area
pages for that service. It must NOT read as a generic version of an area page — it is the
company's definitive statement on that service across South Florida.

Read `_content/SPEC.md` first for voice, and `_content/SPEC-ES.md` for the Spanish rules
(usted register, terminology, what stays in English). Everything there applies.

## Output

Write TWO files:
- `_content/hub-<service-slug>.json`      (English)
- `_content/hub-<service-slug>.es.json`   (Spanish)

Each with this exact shape:

```json
{
  "service_slug": "<slug>",
  "title": "...",
  "meta_description": "...",
  "h1": "...",
  "hero_sub": "...",
  "local_heading": "...",
  "intro_paragraphs": ["...", "...", "...", "..."],
  "scope_heading": "...",
  "scope_intro": "...",
  "scope_items": [ {"name": "...", "desc": "..."}, ... 6 items ],
  "faqs": [ {"q": "...", "a": "..."}, ... 6 items ],
  "cta_heading": "...",
  "cta_sub": "..."
}
```

## Field rules

- **title** — EN 45–62 chars, ES 45–68. Lead with the service and the market:
  "Kitchen Remodeling in Miami-Dade & Broward | PGX". Spanish rewritten for Spanish search.
- **meta_description** — EN 130–162, ES 130–158 chars.
- **h1** — 4–9 words, sentence case, no trailing period.
- **hero_sub** — 25–45 words.
- **intro_paragraphs** — exactly **4**, 70–120 words each. This is the substance:
  - P1: what this service actually means at the high end in South Florida, and who buys it.
  - P2: what makes it different HERE — HVHZ product approvals, salt air, flood elevation,
    the permitting reality across two counties, condo associations where relevant.
  - P3: how the work is scoped, sequenced and priced — fixed written scope, daily supervision,
    inspections passed, permits closed.
  - P4: the range across the market — from historic Coral Gables and Miami Beach through the
    Broward waterfront to the western estate areas — and an invitation to the area pages.
- **scope_items** — exactly **6**, name 2–6 words, desc 18–34 words.
- **faqs** — exactly **6**, answers 45–100 words. Cover: what it costs (honest qualitative
  framing, no invented figures), how long it takes, whether a permit is needed, what could
  stop the job, who supervises, and one service-specific practical question.
- **cta_heading** 4–9 words, **cta_sub** 15–32 words.

## Hard rules

1. No invented statistics, fees, client names, awards or review counts. Permitted claims:
   20+ years in South Florida, 150+ remodels and additions delivered, 100% permitted and
   inspected work, licensed and insured, Lic. CGC1539072.
2. Sentence case headings. h1 must not end with a period.
3. The hub must not duplicate sentences from any area page, and EN/ES must not be literal
   translations of each other in the SEO fields.
4. Plain text only — no HTML, no markdown.
5. Validate both files parse: `python3 -c "import json;json.load(open('<file>'))"`
