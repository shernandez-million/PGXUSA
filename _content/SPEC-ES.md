# PGX Builders Group — Spanish Landing Page Spec (traducción y adaptación)

You are adapting existing ENGLISH landing-page content into SPANISH for PGX Builders Group LLC,
a high-end general contractor in Miami (Lic. CGC1539072, tel. (786) 273-2524). The audience is
affluent Spanish-speaking homeowners in Miami-Dade — Latin American buyers, second-home owners,
and long-time residents. This is a TRANSCREATION, not a literal translation: it must read like it
was written by a native Spanish-language copywriter in Miami.

## Register and voice (match the existing Spanish site)

- **Usted**, always. Never tuteo, never vosotros.
- Neutral Latin American Spanish with natural Miami usage: "estimado" (not "presupuesto" alone —
  though "presupuesto" may appear as a synonym), "remodelación", "ampliación", "permisos",
  "contratista general", "obra", "alcance", "garantía por escrito".
- Existing brand lines to stay consistent with: "Pedir un estimado", "Solicitar un estimado",
  "Remodelación integral", "Ampliaciones y extensiones", "Cocinas", "Baños", "Exteriores",
  "Un solo equipo responsable, del estimado a la garantía", "Obra con permisos e inspecciones",
  "Años construyendo en el sur de la Florida".
- Tone: confident, concrete, lightly wry — same personality as the English, in idiomatic Spanish.
  Do NOT translate English idioms word-for-word; find the Spanish way to say it.

## What stays in English

- Proper nouns: neighborhood/community/building names, "Board of Architects", "Historic
  Preservation Board", department names — keep official English names, optionally with a short
  Spanish gloss on first mention (e.g. "el Board of Architects — la junta de revisión de diseño de
  la ciudad").
- "HVHZ", "FEMA", licencia "CGC1539072", brand name "PGX Builders Group".
- Terms Miami Spanish speakers use in English routinely may stay: "impact windows" can be
  "ventanas de impacto" (preferred) — use the Spanish where a natural Spanish term exists.

## Task

Given one EN content file `_content/<area>.json`, write `_content/<area>.es.json` with the SAME
structure: top-level `area_slug` (unchanged), `neighborhoods` (same names, same order — do not
translate proper nouns), and `pages` keyed by the SAME ENGLISH service slugs (home-remodeling,
kitchen-remodeling, bathroom-remodeling, home-additions, outdoor-living). Every page object has the
same fields, now in Spanish:

- **title** — 45–68 chars. Rewritten for Spanish SEARCH QUERIES, not translated: e.g.
  "Remodelación de cocinas en Coral Gables | PGX Builders". Include the Spanish service keyword +
  area. Vary the pattern across the 5 pages.
- **meta_description** — 130–158 chars, Spanish, with area + a concrete hook + call to action or the
  phone number. This ceiling is strict: Google truncates around 160 characters and the phone number
  sits at the end, so an over-long description loses exactly the call to action. Spanish runs roughly
  15% longer than English, so tighten rather than translate loosely.
- **h1** — 4–10 words, punchy display headline in Spanish, no trailing period, not identical to title.
- **hero_sub**, **local_heading**, **scope_heading**, **scope_intro**, **cta_heading**, **cta_sub** —
  same length disciplines as the English equivalents.
- **intro_paragraphs** — exactly 3, each a faithful transcreation of the English paragraph: same
  facts, same local specifics, natural Spanish prose. Do not add or drop factual claims.
- **scope_items** — exactly 5, names 2–5 words, descs 15–35 words.
- **faqs** — exactly 5. Questions phrased the way a Spanish-speaking Miami homeowner would actually
  ask. Answers carry the same substance as the English.

## Hard rules

1. Same facts as the English file — nothing invented, nothing dropped that is factual. The English
   file already passed fact-checking; your job is language, not research.
2. Correct Spanish: accents/tildes required (remodelación, baño, garantía, código, inspección).
   JSON must be UTF-8 with real accented characters (not escaped entities).
3. Counts identical to English: 3 paragraphs, 5 scope items, 5 FAQs, same neighborhoods list.
4. Plain text only. No HTML, no markdown.
5. Numbers/claims allowed: 20+ años, 150+ remodelaciones y ampliaciones, 100% con permisos e
   inspecciones, Lic. CGC1539072.
6. Do not machine-translate awkwardly: if a sentence sounds like Google Translate, rewrite it.
7. Validate the file parses: python3 -c "import json;json.load(open('<file>'))"
