#!/usr/bin/env python3
"""Correct two classes of building-inspection claim in the content packs.

1. WESTON — factual error. Broward's Building Safety Inspection Program (BORA Policy 05-05)
   uses the earlier 25-year trigger for condominium/cooperative buildings within three miles
   of the coastline; inland buildings run on the later trigger. Weston is inland western
   Broward, so telling a Bonaventure owner the clock "starts at 25 years" states a deadline
   earlier than the one that governs them. Replaced with the qualitative form.

2. "three stories" -> "three habitable stories". Florida HB 913 (2025) narrowed the milestone
   threshold to three HABITABLE stories, which matters where a building's ground level is
   parking. The corpus was already inconsistent — some pages said habitable, most did not.

Per CLAUDE.md these thresholds have moved three times since 2022, so the fix removes the
dependence on numbers rather than swapping in today's ones.
"""
import json
import pathlib
import re
import sys

# (file, exact old, new, expected occurrences)
EDITS = [
    # --- Weston EN ---
    ("weston.json",
     "which the Board administers, starts at 25 years and repeats every ten,",
     "which the Board administers, starts once a building reaches the age county policy sets "
     "for its location and then repeats on a fixed cycle,", 1),
    ("weston.json",
     "Our building is due for its 25-year inspection. Does that stop our unit remodel?",
     "Our building is due for its safety inspection. Does that stop our unit remodel?", 1),
    ("weston.json",
     "administered by the county Board of Rules and Appeals, begins at 25 years and recurs "
     "every ten, and it produces",
     "administered by the county Board of Rules and Appeals, begins once a building reaches "
     "the age county policy sets — earlier for condominium buildings near the coast than for "
     "inland ones — and then repeats on a cycle, and it produces", 1),

    # --- Weston ES ---
    ("weston.es.json",
     "que el Board administra, arranca a los 25 años y se repite cada diez,",
     "que el Board administra, arranca cuando el edificio alcanza la edad que fija la política "
     "del condado para su ubicación y después se repite en un ciclo fijo,", 1),
    ("weston.es.json",
     "A nuestro edificio le toca la inspección de los 25 años. ¿Eso frena la remodelación de la unidad?",
     "A nuestro edificio le toca su inspección de seguridad. ¿Eso frena la remodelación de la unidad?", 1),
    ("weston.es.json",
     "administrado por el Board of Rules and Appeals del condado, empieza a los 25 años y se "
     "repite cada diez, y produce",
     "administrado por el Board of Rules and Appeals del condado, empieza cuando el edificio "
     "alcanza la edad que fija la política del condado para su ubicación —antes para los "
     "edificios en condominio cercanos a la costa que para los del interior— y después se "
     "repite en un ciclo, y produce", 1),

    # --- Aventura: the one page carrying the full numeric recital ---
    ("aventura.json",
     "Florida now requires milestone structural inspections for condo buildings three stories "
     "and up — generally at 30 years, and as early as 25 where local officials require it for "
     "coastal buildings — then every ten years, along with structural integrity reserve studies.",
     "Florida requires milestone structural inspections for condominium buildings of three "
     "habitable stories and up once they reach the age the statute sets, and then on a repeating "
     "cycle, along with structural integrity reserve studies. Those thresholds and deadlines "
     "have been revised several times since 2022, so we confirm what applies to your building "
     "with the association and the building department rather than assume it.", 1),
    ("aventura.es.json",
     "La Florida ahora exige inspecciones estructurales milestone para condominios de tres pisos "
     "o más — en general a los 30 años, y desde los 25 cuando las autoridades locales lo "
     "requieren para edificios costeros — y luego cada diez años, junto con estudios de reservas "
     "de integridad estructural.",
     "La Florida exige inspecciones estructurales milestone para edificios en condominio de tres "
     "pisos habitables o más cuando alcanzan la edad que fija la ley, y después en un ciclo que "
     "se repite, junto con los estudios de reservas de integridad estructural. Esos umbrales y "
     "plazos se han modificado varias veces desde 2022, así que confirmamos qué le aplica a su "
     "edificio con la asociación y el building department en vez de suponerlo.", 1),
]

# global, applied everywhere: HB 913 narrowed the threshold to habitable stories
SWEEPS = [
    (r'\bthree stories and up\b', 'three habitable stories and up'),
    (r'\bthree stories and taller\b', 'three habitable stories and taller'),
    (r'\bthree stories or more\b', 'three habitable stories or more'),
    (r'\bof three stories\b', 'of three habitable stories'),
    (r'\btres pisos o más\b', 'tres pisos habitables o más'),
    (r'\btres pisos en adelante\b', 'tres pisos habitables en adelante'),
    (r'\btres pisos y más\b', 'tres pisos habitables y más'),
]


def main() -> int:
    root = pathlib.Path(__file__).resolve().parent
    failures, changed = [], {}

    for fname, old, new, expect in EDITS:
        p = root / fname
        txt = p.read_text()
        n = txt.count(old)
        if n != expect:
            failures.append(f"{fname}: expected {expect} of {old[:60]!r}, found {n}")
            continue
        p.write_text(txt.replace(old, new))
        changed[fname] = changed.get(fname, 0) + n

    if failures:
        print("REFUSING TO WRITE — the corpus does not match what this script expects:")
        for f in failures:
            print("  -", f)
        return 1

    swept = 0
    for p in sorted(root.glob("*.json")):
        txt = orig = p.read_text()
        for pat, rep in SWEEPS:
            # don't double-apply to pages that already said habitable
            txt = re.sub(pat, rep, txt)
        txt = txt.replace("habitables habitables", "habitables").replace("habitable habitable", "habitable")
        if txt != orig:
            p.write_text(txt)
            k = sum(len(re.findall(pat, orig)) for pat, _ in SWEEPS)
            swept += k
            changed[p.name] = changed.get(p.name, 0) + k

    for p in sorted(root.glob("*.json")):          # every file must still parse
        try:
            json.loads(p.read_text())
        except json.JSONDecodeError as e:
            print(f"BROKE JSON: {p.name} — {e}")
            return 1

    print(f"corrected {len(EDITS)} exact claims + {swept} habitable-story references "
          f"across {len(changed)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
