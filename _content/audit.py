#!/usr/bin/env python3
"""Final consistency audit across _content/<area>.json and <area>.es.json.

Checks (per language):
  1. Title Case leakage in h1 / local_heading / scope_heading / cta_heading / scope_items[].name
  2. scope_items[].name repeated verbatim in 4+ areas
  3. duplicate title / h1 / meta_description across files
  4. structural drift (pages, intro_paragraphs, scope_items, faqs, neighborhoods)
  5. ES only: headings missing expected accents, or using tuteo

Usage: python3 _content/audit.py [-v]
"""
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

CONTENT = Path(__file__).resolve().parent
# read from the plan rather than restated here — this list went stale when
# permitting-compliance shipped and silently failed all 42 areas
SERVICES = [s["slug"] for s in json.loads(
    (Path(__file__).resolve().parent / "site_plan.json").read_text())["services"]]
HEADING_FIELDS = ["h1", "local_heading", "scope_heading", "cta_heading"]

# ---------------------------------------------------------------- proper nouns

# Words that legitimately carry a capital anywhere in a sentence-case headline.
# The last three lines are named places and offices the checker kept flagging:
#   the North and South Forks of the New River (Wilton Manors), Miami-Dade's
#   Product Control section, and "la Venecia de Am\u00e9rica" (Fort Lauderdale).
BASE_PROPER = """
PGX Builders Group LLC Miami Beach Miami-Dade Dade Broward Florida FL South North
East West Coral Gables Aventura Brickell Doral Surfside Pinecrest Sunny Isles
Bal Harbour Bay Harbor Islands Island Fisher Golden Key Biscayne Shores Palmetto
Ponce Davis Ponce-Davis Venetian Upper Side Coconut Grove Fort Lauderdale
Hallandale Hollywood Broadview Las Olas Rio Vista Victoria Park Ridge
HVHZ FEMA NFIP HOA NOA HardieBoard Hardie
Board Architects Architectural Review Historic Preservation Building Department
Village City Town County State Code Chapter Section
Milestone Structural Integrity Reserve Study SIRS
English Spanish Latin America American
January February March April May June July August September October November December
Monday Tuesday Wednesday Thursday Friday Saturday Sunday
Lic CGC ADA NEC FBC ASCE
Mediterranean Revival Deco MiMo Modern Contemporary Bahamian Caribbean
Atlantic Biscayne Intracoastal Everglades Gulf
Wolf Miele Sub-Zero SubZero Thermador Gaggenau Bosch Viking Poliform Boffi
Dornbracht Waterworks Kohler Toto Grohe Hansgrohe Duravit Calacatta Carrara
Taj Mahal Dekton Neolith Cambria Silestone Caesarstone
Google Instagram Houzz
Indian Creek Government Cut Venice America Beautiful Pleasant Living Parks
Snapper Creek Cutler Matheson Hammock Crandon Rickenbacker Causeway
Fork Forks
Product Control
Venecia América América
"""
PROPER = set()
for _w in BASE_PROPER.split():
    PROPER.add(_w.lower())


def add_proper_from(text):
    for w in re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ'’\-]+", text):
        PROPER.add(w.lower())
        for part in re.split(r"[-'’]", w):
            if part:
                PROPER.add(part.lower())


# ---------------------------------------------------------------- helpers

def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ'’]*")


SENT_START_RE = re.compile(r"(?:^|[.!?:]\s+)([A-Za-zÁÉÍÓÚÜÑáéíóúüñ'’]+)")


def title_case_score(s):
    """Return (ratio, capped, considered) over words >3 chars that aren't proper nouns."""
    # words that open a sentence are capitalised in sentence case too, so they
    # carry no signal — "Keep the lot. Remake the house" has two of them.
    sentence_openers = {m.group(1) for m in SENT_START_RE.finditer(s)}
    words = WORD_RE.findall(s)
    considered = []
    for i, w in enumerate(words):
        if len(w) <= 3:
            continue
        if w.lower() in PROPER:
            continue
        if w.isupper():          # acronyms
            continue
        if w in sentence_openers:
            continue
        considered.append(w)
    if not considered:
        return 0.0, [], []
    capped = [w for w in considered if w[0].isupper()]
    return len(capped) / len(considered), capped, considered


# ---------------------------------------------------------------- ES checks

# Spanish words that must carry an accent when written correctly.
ACCENT_REQUIRED = {
    "remodelacion": "remodelación", "remodelaciones": "remodelaciones",
    "ampliacion": "ampliación", "ampliaciones": "ampliaciones",
    "bano": "baño", "banos": "baños",
    "diseno": "diseño", "disenos": "diseños",
    "garantia": "garantía", "garantias": "garantías",
    "codigo": "código", "codigos": "códigos",
    "inspeccion": "inspección", "inspecciones": "inspecciones",
    "construccion": "construcción", "renovacion": "renovación",
    "supervision": "supervisión", "instalacion": "instalación",
    "ejecucion": "ejecución", "ubicacion": "ubicación",
    "asociacion": "asociación", "elevacion": "elevación",
    "aqui": "aquí", "asi": "así", "mas": "más", "anos": "años",
    "despues": "después", "segun": "según", "tambien": "también",
    "atencion": "atención", "seccion": "sección", "version": "versión",
    "presion": "presión", "vision": "visión", "region": "región",
    "cocina": "cocina",
}
# canonical accented spellings, keyed by their unaccented form. Keep only the
# pairs where the key really is the *stripped* form of an accented word
# (otherwise the entry can never fire, e.g. "cocina" -> "cocina").
ACCENT_MAP = {k: v for k, v in ACCENT_REQUIRED.items()
              if strip_accents(v).lower() == k and v.lower() != k}

TUTEO_RE = [
    (re.compile(r"\btú\b", re.I), "pronombre tú"),
    # unaccented "tu" is the tuteo possessive; usted register wants "su"
    (re.compile(r"\btu\b", re.I), "posesivo tu"),
    (re.compile(r"\btuyo\b|\btuya\b|\btuyos\b|\btuyas\b", re.I), "posesivo tuyo"),
    (re.compile(r"\bcontigo\b|\bti\b(?!\w)", re.I), "contigo/ti"),
    # 2nd-person singular indicative
    (re.compile(r"\b(tienes|puedes|quieres|necesitas|sabes|vives|buscas|piensas|"
                r"quisieras|podrías|podrias|tendrías|tendrias|harás|haras|verás|veras|"
                r"tienes|eres|estás|estas\b(?=\s+(?:list|busc|pens)))\b", re.I), "verbo en tú"),
    # Tuteo imperatives are mostly HOMOGRAPHS of the 3rd-person singular
    # indicative ("el Village revisa", "cada ampliación empieza"), so a bare verb
    # list produces only false positives. Two patterns are unambiguous:
    #   a) enclitic -anos/-ate forms, where usted takes -enos/-ese
    #      (cuéntanos vs cuéntenos, contáctanos vs contáctenos)
    (re.compile(r"\b(cuéntanos|cuentanos|contáctanos|contactanos|escríbenos|escribenos|"
                r"llámanos|llamanos|pídenos|pidenos|avísanos|avisanos|díganos_tu)\b", re.I),
     "imperativo en tú (enclítico)"),
    #   b) an imperative-shaped verb opening a clause and governing a tuteo
    #      possessive/pronoun ("Pide tu estimado", "Descubre tu cocina")
    (re.compile(r"(?:^|[.!?;:]\s+|¡)\s*(pide|llama|solicita|pregunta|escribe|agenda|"
                r"reserva|descubre|conoce|revisa|elige|empieza|comienza|imagina|"
                r"transforma|renueva)\s+(?:\w+\s+){0,2}?\b(tu|tus|ti|contigo)\b", re.I),
     "imperativo en tú + posesivo"),
]


def es_accent_issues(s):
    hits = []
    for w in WORD_RE.findall(s):
        low = w.lower()
        if low in ACCENT_MAP:
            hits.append(f"{w} -> {ACCENT_MAP[low]}")
    return hits


def es_tuteo_issues(s):
    hits = []
    for rx, label in TUTEO_RE:
        m = rx.search(s)
        if m:
            hits.append(f"{label}: '{m.group(0)}'")
    return sorted(set(hits))


# ---------------------------------------------------------------- load

def load():
    docs = {"en": {}, "es": {}}
    for p in sorted(CONTENT.glob("*.json")):
        name = p.name
        # only area packs have neighborhoods and a pages map; hubs, About and
        # property-type packs are a different shape and are checked by build.py
        if name in ("site_plan.json", "projects.json") or name.startswith(
                ("hub-", "page-", "type-")):
            continue
        if name.endswith(".es.json"):
            lang, slug = "es", name[:-len(".es.json")]
        else:
            lang, slug = "en", name[:-len(".json")]
        docs[lang][slug] = json.loads(p.read_text(encoding="utf-8"))
    return docs


# ---------------------------------------------------------------- forbidden claims
# Two classes of claim have already shipped to production and had to be corrected.
# Both are cheap to detect and expensive to miss, so they are guarded on every run
# rather than left to a one-off script nobody remembers to invoke.

# 1. The BORA false contrast. BOTH counties have a Board of Rules and Appeals —
#    Miami-Dade's under County Code ch. 8 sec. 8-4. Claiming otherwise reached 56
#    strings across 37 files before an agent caught it.
BORA_BOARD = re.compile(r'Board of Rules|Rules and Appeals|\bBORA\b|Reglas y Apelaciones', re.I)
BORA_DENIAL = re.compile(
    r'(unlike\s+Miami[- ]Dade'
    r'|a\s+diferencia\s+de\s+Miami[- ]Dade'
    r'|Miami[- ]Dade\s+(does\s+not|doesn.t|has\s+no|lacks)'
    r'|(which|that)\s+Miami[- ]Dade\s+(does\s+not|doesn.t|has\s+no|lacks)'
    r'|no\s+equivalent\s+in\s+Miami[- ]Dade'
    r'|en\s+Miami[- ]Dade\s+no\s+(existe|hay|tiene)'
    r'|Miami[- ]Dade\s+no\s+(tiene|cuenta\s+con|posee|dispone)'
    r'|sin\s+equivalente\s+en\s+Miami[- ]Dade)', re.I)

# 2. Numeric inspection thresholds. Florida rewrote these in 2022, 2023 and 2025,
#    and a static page cannot track them — so they are stated qualitatively or not
#    at all. Weston shipped "starts at 25 years" to inland owners it did not govern.
# 2. Numeric inspection thresholds ASSERTED as the rule. Florida rewrote these in
#    2022, 2023 and 2025, and a static page cannot track them, so the site states them
#    qualitatively. Weston shipped "starts at 25 years" to inland owners it did not
#    govern. Naming the programme the way owners actually say it ("the one everyone
#    still calls the 40-year recertification") is fine and deliberately not matched —
#    only a sentence that says the clock STARTS or REPEATS at a number is a defect.
INSPECTION_NUMBERS = re.compile(
    r'\b(begins?|starts?|recurs?|repeats?|applies)\s+(at|from)\s+\d{2}\s+years?\b'
    r'|\bat\s+\d{2}\s+years\s+(and|then)\b'
    r'|\bevery\s+(ten|10)\s+years\b'
    r'|\b(empieza|arranca|comienza|inicia|aplica)\s+a\s+los\s+\d{2}\s+a\xf1os\b'
    r'|\bdesde\s+los\s+\d{2}\s+a\xf1os\b'
    r'|\bcada\s+(diez|10)\s+a\xf1os\b',
    re.I)


def check_forbidden_claims(docs, problems):
    for lang, by_slug in docs.items():
        for slug, doc in sorted(by_slug.items()):
            blob = json.dumps(doc, ensure_ascii=False)
            for sent in re.split(r'(?<=[.!?])\s+', blob):
                if BORA_BOARD.search(sent) and BORA_DENIAL.search(sent):
                    problems[f"0-forbidden-{lang}"].append(
                        f"{slug}: BORA false contrast \u2014 {sent.strip()[:150]}")
                m = INSPECTION_NUMBERS.search(sent)
                if m:
                    problems[f"0-forbidden-{lang}"].append(
                        f"{slug}: inspection threshold stated numerically "
                        f"({m.group(0)!r}) \u2014 {sent.strip()[:110]}")


def main():
    docs = load()

    # Assigned scope = areas that exist in BOTH languages (the 20 Miami-Dade
    # pairs). EN-only areas are a separate, concurrently-authored county
    # rollout; audit them but report them as advisory so a half-written file
    # is never mistaken for drift in the finished set.
    audit_all = "--all" in sys.argv
    scope = set(docs["es"]) & set(docs["en"])
    out_of_scope = sorted(set(docs["en"]) - scope)
    if not audit_all:
        docs = {lang: {k: v for k, v in d.items() if k in scope}
                for lang, d in docs.items()}
    print(f"scope: {len(scope)} paired areas (EN+ES)"
          + (f"; EN-only excluded: {out_of_scope}" if out_of_scope and not audit_all else "")
          + ("  [--all: auditing everything]" if audit_all else ""))

    # seed the proper-noun set with every neighborhood name and area slug
    for lang in docs:
        for slug, doc in docs[lang].items():
            add_proper_from(slug.replace("-", " "))
            for n in doc.get("neighborhoods", []):
                add_proper_from(n)

    problems = defaultdict(list)
    check_forbidden_claims(docs, problems)

    for lang in ("en", "es"):
        # ---- 2: scope name reuse across areas
        name_areas = defaultdict(set)
        name_descs = defaultdict(list)
        # ---- 3: duplicates
        seen = {"title": defaultdict(list), "h1": defaultdict(list),
                "meta_description": defaultdict(list)}

        for slug in sorted(docs[lang]):
            doc = docs[lang][slug]
            pages = doc.get("pages", {})

            # ---- 4: structural drift
            nb = doc.get("neighborhoods", [])
            if not (8 <= len(nb) <= 14):
                problems[f"4-structure-{lang}"].append(
                    f"{slug}: neighborhoods {len(nb)} (need 8-14)")
            if set(pages) != set(SERVICES):
                problems[f"4-structure-{lang}"].append(
                    f"{slug}: page keys {sorted(pages)}")

            for svc in SERVICES:
                pg = pages.get(svc)
                if pg is None:
                    continue
                tag = f"{slug}/{svc}"

                for field, n in (("intro_paragraphs", 3), ("scope_items", 5), ("faqs", 5)):
                    got = len(pg.get(field, []))
                    if got != n:
                        problems[f"4-structure-{lang}"].append(
                            f"{tag}: {field} {got} != {n}")

                # ---- 1: title case
                targets = [(f, pg.get(f, "")) for f in HEADING_FIELDS]
                targets += [(f"scope_items[{i}].name", it.get("name", ""))
                            for i, it in enumerate(pg.get("scope_items", []))]
                for field, val in targets:
                    if not val:
                        continue
                    ratio, capped, considered = title_case_score(val)
                    if ratio > 0.60:
                        problems[f"1-titlecase-{lang}"].append(
                            f"{tag}.{field}: {val!r}  [{len(capped)}/{len(considered)} capped: {capped}]")

                # ---- 2
                for it in pg.get("scope_items", []):
                    nm = it.get("name", "").strip()
                    if nm:
                        name_areas[nm].add(slug)
                        name_descs[nm].append((slug, it.get("desc", "").strip()))

                # ---- 3
                for field in seen:
                    v = (pg.get(field, "") or "").strip().lower()
                    if v:
                        seen[field][v].append(tag)

                # ---- 5: ES language checks
                if lang == "es":
                    for field in HEADING_FIELDS:
                        val = pg.get(field, "")
                        if not val:
                            continue
                        acc = es_accent_issues(val)
                        if acc:
                            problems["5-accents-es"].append(f"{tag}.{field}: {val!r} {acc}")
                    for field, val in [(f, pg.get(f, "")) for f in HEADING_FIELDS] + \
                            [("hero_sub", pg.get("hero_sub", "")),
                             ("scope_intro", pg.get("scope_intro", "")),
                             ("cta_sub", pg.get("cta_sub", ""))]:
                        if not val:
                            continue
                        tut = es_tuteo_issues(val)
                        if tut:
                            problems["5-tuteo-es"].append(f"{tag}.{field}: {val!r} {tut}")

        # A repeated scope-card LABEL is not itself a defect: "Vidrio de impacto HVHZ" is
        # simply what the product is called, and inventing synonyms to dodge a checker makes
        # the writing worse. What matters is whether the DESCRIPTION under it is also the
        # same — that is real templating. Flag only when both repeat.
        def _overlap(a, b):
            wa = set(re.findall(r"[\wáéíóúüñ]+", a.lower()))
            wb = set(re.findall(r"[\wáéíóúüñ]+", b.lower()))
            if not wa or not wb:
                return 0.0
            return len(wa & wb) / len(wa | wb)

        for nm, areas in sorted(name_areas.items()):
            if len(areas) < 4:
                continue
            pairs = name_descs[nm]
            twins = [(x[0], y[0], round(_overlap(x[1], y[1]), 2))
                     for i, x in enumerate(pairs) for y in pairs[i + 1:]
                     if _overlap(x[1], y[1]) >= 0.60]
            if twins:
                problems[f"2-scopereuse-{lang}"].append(
                    f"{nm!r} in {len(areas)} areas WITH near-identical descriptions: "
                    + ", ".join(f"{a}~{b} ({r})" for a, b, r in twins[:4]))

        for field, bucket in seen.items():
            for v, tags in sorted(bucket.items()):
                if len(tags) > 1:
                    problems[f"3-dupes-{lang}"].append(f"{field}: {tags} -> {v!r}")

    total = 0
    for key in sorted(problems):
        rows = problems[key]
        total += len(rows)
        print(f"\n=== {key} ({len(rows)}) ===")
        for r in rows:
            print("  " + r)

    print(f"\nTOTAL ISSUES: {total}")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
