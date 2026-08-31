#!/usr/bin/env python3
"""Render PGX landing pages (EN + ES) from _content JSON files + templates.

Usage:  python3 _content/build.py [--check-only]

Inputs:  _content/<area>.json (EN), _content/<area>.es.json (ES),
         _content/template.html, _content/template-es.html, _content/site_plan.json
Outputs (repo root): 100 EN pages, 100 ES pages, areas.html, zonas.html, sitemap.xml.
ES files are optional per-area during development; hreflang/toggles only emit for pairs
that exist. Exits non-zero with a report if validation fails.
"""
import html
import itertools
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "_content"
PLAN = json.loads((CONTENT / "site_plan.json").read_text())
TPL = {"en": (CONTENT / "template.html").read_text(),
       "es": (CONTENT / "template-es.html").read_text()}
DOMAIN = PLAN["domain"]
TODAY = "2026-08-19"

SERVICES = {s["slug"]: s for s in PLAN["services"]}
AREAS = {a["slug"]: a for a in PLAN["areas"]}
SERVICE_ORDER = [s["slug"] for s in PLAN["services"]]
# A property type (luxury condo, waterfront, historic) is NOT a service: it cuts across all
# six of them. Putting it in PLAN["services"] would push it into the service nav and the
# contact form on all 522 existing pages, so it gets its own page type instead.
TYPES = {t["slug"]: t for t in PLAN.get("property_types", [])}
TYPE_ORDER = [t["slug"] for t in PLAN.get("property_types", [])]

FIELD_LIMITS = {
    "en": {"title": (40, 70), "meta_description": (120, 162)},
    "es": {"title": (40, 75), "meta_description": (120, 160)},
}
COMMON_FIELDS = ["h1", "hero_sub", "local_heading", "scope_heading",
                 "scope_intro", "cta_heading", "cta_sub"]
EXTRA_FORM_OPTIONS = {"en": ["Something else"], "es": ["Otro"]}
OG_LOCALE = {"en": "en_US", "es": "es_US"}
# alt text is built per page so the same stock rendering isn't described identically on 200 pages
ALT_TMPL = {"en": "{base} — {service} in {area}, Florida. Architectural rendering.",
            "es": "{base} — {service} en {area}, Florida. Render arquitectónico."}
ALT_BASE_ES = {
    "home-remodeling": "Sala remodelada de planta abierta",
    "kitchen-remodeling": "Cocina renovada con isla de mármol y gabinetes a medida",
    "bathroom-remodeling": "Baño principal con tina independiente y ducha de mármol",
    "home-additions": "Ampliación trasera moderna con ventanales de piso a techo",
    "outdoor-living": "Terraza cubierta con cocina de verano y piscina",
    "permitting-compliance": "Planos arquitectónicos y documentos de permiso",
}

PROVIDER = {
    "@type": "GeneralContractor",
    "@id": DOMAIN + "/#business",
    "name": PLAN["business"]["name"],
    "url": DOMAIN + "/",
    "logo": DOMAIN + "/images/pgx-logo.png",
    "image": DOMAIN + "/og-image.jpg",
    "telephone": "+1-786-273-2524",
    "email": PLAN["business"]["email"],
    "address": {"@type": "PostalAddress", "addressLocality": "Miami",
                "addressRegion": "FL", "addressCountry": "US"},
    "areaServed": [{"@type": "AdministrativeArea", "name": "Miami-Dade County, Florida"},
                   {"@type": "AdministrativeArea", "name": "Broward County, Florida"}],
    "openingHoursSpecification": [{
        "@type": "OpeningHoursSpecification",
        "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "opens": "08:00", "closes": "18:00"}],
    "knowsLanguage": ["en", "es"],
}

errors: list[str] = []
warnings: list[str] = []


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def svc_slug(s_slug: str, lang: str) -> str:
    return SERVICES[s_slug]["slug_es"] if lang == "es" else s_slug


def svc_name(s_slug: str, lang: str) -> str:
    return SERVICES[s_slug]["name_es"] if lang == "es" else SERVICES[s_slug]["name"]


def url_for(s_slug: str, a_slug: str, lang: str) -> str:
    return f"/{svc_slug(s_slug, lang)}-{a_slug}"


def file_for(s_slug: str, a_slug: str, lang: str) -> str:
    return f"{svc_slug(s_slug, lang)}-{a_slug}.html"


COUNTY_ES = {"Miami-Dade": "Condado de Miami-Dade", "Broward": "Condado de Broward"}


def county_name(area: dict, lang: str) -> str:
    c = area.get("county", "Miami-Dade")
    return COUNTY_ES.get(c, c) if lang == "es" else f"{c} County"


def areas_url(lang: str) -> str:
    return "/zonas" if lang == "es" else "/areas"


def home_url(lang: str) -> str:
    return "/es" if lang == "es" else "/"


def load_content() -> dict:
    data = {"en": {}, "es": {}}
    for a in AREAS:
        for lang, name in (("en", f"{a}.json"), ("es", f"{a}.es.json")):
            p = CONTENT / name
            if not p.exists():
                # an area can sit in the plan before its copy is written (county rollout);
                # it simply isn't rendered until the file lands
                warnings.append(f"not yet written: {name}"
                                + ("" if lang == "en" else " (EN page will have no ES alternate)"))
                continue
            try:
                data[lang][a] = json.loads(p.read_text())
            except json.JSONDecodeError as e:
                errors.append(f"{name}: invalid JSON — {e}")
    data["hub"] = {"en": {}, "es": {}}
    for sl in SERVICE_ORDER:
        for lang, nm in (("en", f"hub-{sl}.json"), ("es", f"hub-{sl}.es.json")):
            p2 = CONTENT / nm
            if not p2.exists():
                warnings.append(f"not yet written: {nm}")
                continue
            try:
                data["hub"][lang][sl] = json.loads(p2.read_text())
            except json.JSONDecodeError as e:
                errors.append(f"{nm}: invalid JSON — {e}")
    data["type"] = {"en": {}, "es": {}}
    for tl in TYPE_ORDER:
        for lang, nm in (("en", f"type-{tl}.json"), ("es", f"type-{tl}.es.json")):
            p3 = CONTENT / nm
            if not p3.exists():
                warnings.append(f"not yet written: {nm}")
                continue
            try:
                data["type"][lang][tl] = json.loads(p3.read_text())
            except json.JSONDecodeError as e:
                errors.append(f"{nm}: invalid JSON — {e}")
    return data


def validate(data: dict) -> None:
    for lang, docs in data.items():
        if lang in ("hub", "type"):
            continue
        seen = {"title": {}, "h1": {}, "meta_description": {}}
        limits = FIELD_LIMITS[lang]
        for a_slug, doc in docs.items():
            nb = doc.get("neighborhoods", [])
            if not (8 <= len(nb) <= 14):
                errors.append(f"[{lang}] {a_slug}: neighborhoods count {len(nb)} (need 8-14)")
            pages = doc.get("pages", {})
            unknown = set(pages) - set(SERVICE_ORDER)
            if unknown:
                errors.append(f"[{lang}] {a_slug}: unknown page keys {sorted(unknown)}")
                continue
            # a service can be added to the plan before its copy exists (service rollout)
            for miss in set(SERVICE_ORDER) - set(pages):
                warnings.append(f"not yet written: [{lang}] {a_slug}/{miss}")
            for s_slug, pg in pages.items():
                tag = f"[{lang}] {a_slug}/{s_slug}"
                for f in list(limits) + COMMON_FIELDS:
                    v = pg.get(f, "")
                    if not isinstance(v, str) or not v.strip():
                        errors.append(f"{tag}: missing field {f}")
                for f, (lo, hi) in limits.items():
                    v = pg.get(f, "")
                    if v and not (lo <= len(v) <= hi):
                        warnings.append(f"{tag}: {f} length {len(v)} outside [{lo},{hi}]")
                if pg.get("h1", "").rstrip().endswith("."):
                    errors.append(f"{tag}: h1 ends with a period")
                ip = pg.get("intro_paragraphs", [])
                if len(ip) != 3:
                    errors.append(f"{tag}: intro_paragraphs count {len(ip)} != 3")
                si = pg.get("scope_items", [])
                if len(si) != 5:
                    errors.append(f"{tag}: scope_items count {len(si)} != 5")
                for it in si:
                    if not it.get("name") or not it.get("desc"):
                        errors.append(f"{tag}: scope_item missing name/desc")
                fq = pg.get("faqs", [])
                if len(fq) != 5:
                    errors.append(f"{tag}: faqs count {len(fq)} != 5")
                for it in fq:
                    if not it.get("q") or not it.get("a"):
                        errors.append(f"{tag}: faq missing q/a")
                for field, bucket in seen.items():
                    v = pg.get(field, "").strip().lower()
                    if v in bucket:
                        errors.append(f"{tag}: duplicate {field} with {bucket[v]}")
                    else:
                        bucket[v] = tag
        # near-duplicate intro check within this language (word 6-gram overlap)
        def grams(txt):
            ws = re.findall(r"[a-záéíóúüñ']+", txt.lower())
            return set(tuple(ws[i:i + 6]) for i in range(len(ws) - 5))
        sigs = {}
        for a_slug, doc in docs.items():
            for s_slug, pg in doc.get("pages", {}).items():
                sigs[f"{a_slug}/{s_slug}"] = grams(" ".join(pg.get("intro_paragraphs", [])))
        for (t1, g1), (t2, g2) in itertools.combinations(sigs.items(), 2):
            if not g1 or not g2:
                continue
            inter = len(g1 & g2)
            if inter and inter / min(len(g1), len(g2)) > 0.25:
                errors.append(f"[{lang}] near-duplicate intro copy: {t1} vs {t2} ({inter} shared 6-grams)")


def jsonld_service(s_slug, area, canonical, lang):
    d = {
        "@context": "https://schema.org", "@type": "Service",
        "serviceType": svc_name(s_slug, lang), "url": canonical,
        "areaServed": {"@type": "Place", "name": f"{area['name']}, FL"},
        "inLanguage": lang,
        "provider": PROVIDER,
        "isPartOf": {"@id": DOMAIN + "/#website"},
    }
    return d


def jsonld_breadcrumb(s_slug, area, canonical, lang):
    home_name = "Inicio" if lang == "es" else "Home"
    areas_name = "Zonas de servicio" if lang == "es" else "Service areas"
    joiner = "en" if lang == "es" else "in"
    items = [
        {"@type": "ListItem", "position": 1, "name": home_name, "item": DOMAIN + home_url(lang)},
        {"@type": "ListItem", "position": 2, "name": areas_name, "item": DOMAIN + areas_url(lang)},
    ]
    label = f"{svc_name(s_slug, lang)} {joiner} {area['name']}"
    if s_slug == "home-remodeling":
        items.append({"@type": "ListItem", "position": 3, "name": label, "item": canonical})
    else:
        items.append({"@type": "ListItem", "position": 3, "name": area["name"],
                      "item": DOMAIN + url_for("home-remodeling", area["slug"], lang)})
        items.append({"@type": "ListItem", "position": 4, "name": label, "item": canonical})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}


def jsonld_faq(faqs):
    return {
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": f["q"],
                        "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faqs],
    }


def lang_pair_urls(s_slug, a_slug, has_es):
    en = DOMAIN + url_for(s_slug, a_slug, "en")
    es = DOMAIN + url_for(s_slug, a_slug, "es") if has_es else None
    return en, es


DETAIL_ALT = {
    "en": {"remodel": ["Remodelled living space viewed from the seating area",
                       "Open-plan living and kitchen after a full renovation"],
           "kitchen": ["Marble backsplash and brass fittings in a renovated kitchen",
                       "Stone island and seating in a remodelled kitchen"],
           "bath": ["Frameless glass shower and marble detailing in a primary bath",
                    "Double vanity and mirrors in a renovated primary bathroom"],
           "addition": ["Covered terrace joining a modern rear addition",
                        "Glass sliders and roofline of a new rear addition"],
           "outdoor": ["Summer kitchen under a covered outdoor terrace",
                       "Pool terrace and seating beside a South Florida home"],
           "permit": ["Architectural floor plans laid out for a permit submittal",
                      "Elevation drawings and plan set for a building permit"]},
    "es": {"remodel": ["Sala remodelada vista desde la zona de estar",
                       "Sala y cocina de planta abierta tras una renovación integral"],
           "kitchen": ["Salpicadero de mármol y grifería de latón en una cocina renovada",
                       "Isla de piedra y asientos en una cocina remodelada"],
           "bath": ["Ducha de vidrio sin marco y detalles en mármol en un baño principal",
                    "Vanities dobles y espejos en un baño principal renovado"],
           "addition": ["Terraza cubierta unida a una ampliación trasera moderna",
                        "Ventanales corredizos y techo de una ampliación nueva"],
           "outdoor": ["Cocina de verano bajo una terraza exterior cubierta",
                       "Terraza de piscina y asientos junto a una casa del sur de la Florida"],
           "permit": ["Planos arquitectónicos preparados para un permiso",
                      "Planos de elevación y juego de planos para un permiso de construcción"]},
}


def detail_tokens(stem, lang):
    """Two supporting photographs per page — his standard is 2-4, never text-only."""
    out = {}
    for i in (1, 2):
        out[f"{{{{DETAIL{i}}}}}"] = f"images/detail/{stem}-{i}.webp"
        out[f"{{{{DETAIL{i}_SRCSET}}}}"] = ", ".join(
            f"images/detail/{stem}-{i}-{w}.webp {w}w" for w in (420, 640, 900)
        ) + f", images/detail/{stem}-{i}.webp 1200w"
        out[f"{{{{DETAIL{i}_ALT}}}}"] = esc(DETAIL_ALT[lang][stem][i - 1])
    return out


def render_page(a_slug, s_slug, doc, lang, has_pair, built=None):
    svc, area, pg = SERVICES[s_slug], AREAS[a_slug], doc["pages"][s_slug]
    canonical = DOMAIN + url_for(s_slug, a_slug, lang)
    en_abs = DOMAIN + url_for(s_slug, a_slug, "en")
    es_abs = DOMAIN + url_for(s_slug, a_slug, "es")
    name = svc_name(s_slug, lang)

    home_name = "Inicio" if lang == "es" else "Home"
    areas_name = "Zonas" if lang == "es" else "Areas"
    crumb0 = (f'<a href="{home_url(lang)}">{home_name}</a><span class="sep">/</span>'
              f'<a href="{areas_url(lang)}">{areas_name}</a>')
    if s_slug == "home-remodeling":
        crumb1 = f'<span>{esc(area["name"])}</span>'
    else:
        crumb1 = (f'<a href="{url_for("home-remodeling", a_slug, lang)}">{esc(area["name"])}</a>'
                  f'<span class="sep">/</span><span>{esc(name)}</span>')

    intro_html = "\n".join(f"      <p>{esc(p)}</p>" for p in pg["intro_paragraphs"])
    nb_html = "\n".join(f'      <span class="chip">{esc(n)}</span>' for n in doc["neighborhoods"])

    cards = []
    for i, it in enumerate(pg["scope_items"], 1):
        cards.append('      <div class="pr-card rv"><span class="n">%02d</span>'
                     '<h3 class="disp">%s</h3><p>%s</p></div>' % (i, esc(it["name"]), esc(it["desc"])))
    scope_html = "\n".join(cards)

    faq_html = "\n".join(
        f'      <details class="fq"{" open" if i == 0 else ""}><summary>{esc(f["q"])}</summary>'
        f'<div class="fa">{esc(f["a"])}</div></details>'
        for i, f in enumerate(pg["faqs"]))

    rel_svc = "\n".join(
        f'          <a class="chip" href="{url_for(s, a_slug, lang)}">{esc(svc_name(s, lang))}</a>'
        for s in SERVICE_ORDER if s != s_slug)
    # where a property type dominates this area, offer it alongside the services — a Brickell
    # reader is far more likely to want the condominium page than another Brickell service
    for tl in TYPE_ORDER:
        if a_slug in TYPES[tl].get("areas", []):
            rel_svc += (f'\n          <a class="chip" href="{type_url(tl, lang)}">'
                        f'{esc(type_name(tl, lang))}</a>')
    # only link neighbours that actually have a rendered page in this language
    nbrs = [n for n in area["neighbors"] if built is None or n in built]
    rel_areas = "\n".join(
        f'          <a class="chip" href="{url_for(s_slug, n, lang)}">{esc(AREAS[n]["name"])}</a>'
        for n in nbrs)

    opt_key = "form_option_es" if lang == "es" else "form_option"
    form_opts = "\n".join(
        '                <option%s>%s</option>' % (
            " selected" if s[opt_key] == svc[opt_key] else "", esc(s[opt_key]))
        for s in PLAN["services"])
    for extra in EXTRA_FORM_OPTIONS[lang]:
        form_opts += f'\n                <option>{esc(extra)}</option>'

    ft_svcs = "\n".join(
        f'        <li><a href="{url_for(s, a_slug, lang)}">{esc(svc_name(s, lang))}</a></li>'
        for s in SERVICE_ORDER)
    ft_areas = "\n".join(
        f'        <li><a href="{url_for("home-remodeling", n, lang)}">{esc(AREAS[n]["name"])}</a></li>'
        for n in nbrs)

    alt_url = (url_for(s_slug, a_slug, "es" if lang == "en" else "en")
               if has_pair else home_url("es" if lang == "en" else "en"))

    stem = Path(svc["image"]).stem
    hero_srcset = ", ".join(f"images/r/{stem}-{w}.webp {w}w" for w in (420, 640, 900, 1280))
    alt_base = (ALT_BASE_ES[s_slug] if lang == "es"
                else svc["img_alt_base"].split(" — ")[0])
    img_alt = ALT_TMPL[lang].format(base=alt_base, service=name.lower(), area=area["name"])
    og_img = f"{DOMAIN}/images/og/{Path(svc['image']).stem}-og.jpg"

    joiner = "·"
    out = TPL[lang]
    if not has_pair:
        # no translated counterpart yet — emit no hreflang block at all
        out = out.replace(
            '<link rel="alternate" hreflang="en" href="{{EN_ABS_URL}}">\n'
            '<link rel="alternate" hreflang="es" href="{{ES_ABS_URL}}">\n'
            '<link rel="alternate" hreflang="x-default" href="{{EN_ABS_URL}}">\n', '')
    repl = {
        "{{TITLE}}": esc(pg["title"]),
        "{{META_DESCRIPTION}}": esc(pg["meta_description"]),
        "{{CANONICAL_URL}}": canonical,
        "{{EN_ABS_URL}}": en_abs if has_pair or lang == "en" else canonical,
        "{{ES_ABS_URL}}": es_abs if has_pair or lang == "es" else canonical,
        "{{ALT_URL}}": alt_url,
        "{{OG_LOCALE}}": OG_LOCALE[lang],
        "{{OG_LOCALE_ALT}}": OG_LOCALE["es" if lang == "en" else "en"],
        "{{OG_IMAGE_URL}}": og_img,
        "{{JSONLD_SERVICE}}": json.dumps(jsonld_service(s_slug, area, canonical, lang), indent=2, ensure_ascii=False),
        "{{JSONLD_BREADCRUMB}}": json.dumps(jsonld_breadcrumb(s_slug, area, canonical, lang), indent=2, ensure_ascii=False),
        "{{JSONLD_FAQ}}": json.dumps(jsonld_faq(pg["faqs"]), indent=2, ensure_ascii=False),
        "{{BREADCRUMB_HTML}}": crumb0 + '<span class="sep">/</span>' + crumb1,
        "{{EYEBROW}}": esc(f"{name} {joiner} {area['name']}, FL"),
        "{{H1}}": esc(pg["h1"].rstrip(".")),
        "{{HERO_SUB}}": esc(pg["hero_sub"]),
        "{{HERO_IMAGE}}": svc["image"],
        "{{HERO_SRCSET}}": hero_srcset,
        **detail_tokens(stem, lang),
        "{{HERO_IMG_ALT}}": esc(img_alt),
        "{{AREA_NAME}}": esc(area["name"]),
        "{{COUNTY}}": esc(county_name(area, lang)),
        "{{SERVICE_NAME}}": esc(name),
        "{{LOCAL_HEADING}}": esc(pg["local_heading"].rstrip(".")),
        "{{INTRO_PARAGRAPHS_HTML}}": intro_html,
        "{{NEIGHBORHOOD_CHIPS_HTML}}": nb_html,
        "{{SCOPE_HEADING}}": esc(pg["scope_heading"].rstrip(".")),
        "{{SCOPE_INTRO}}": esc(pg["scope_intro"]),
        "{{SCOPE_CARDS_HTML}}": scope_html,
        "{{FAQ_ITEMS_HTML}}": faq_html,
        "{{RELATED_SERVICES_HTML}}": rel_svc,
        "{{RELATED_AREAS_HTML}}": rel_areas,
        "{{CTA_HEADING}}": esc(pg["cta_heading"]),
        "{{CTA_SUB}}": esc(pg["cta_sub"]),
        "{{FORM_OPTIONS_HTML}}": form_opts,
        "{{FOOTER_SERVICES_HTML}}": ft_svcs,
        "{{FOOTER_AREAS_HTML}}": ft_areas,
    }
    for k, v in repl.items():
        out = out.replace(k, v)
    leftovers = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if leftovers:
        errors.append(f"[{lang}] {a_slug}/{s_slug}: unreplaced tokens {leftovers}")
    return out


AREAS_PAGE_COPY = {
    "en": {
        "title": "Service Areas — Remodeling Contractor in Miami-Dade | PGX Builders",
        "meta": "Where PGX Builders Group builds: whole-home remodeling, additions, kitchens, baths and outdoor living across Coral Gables, Coconut Grove, Pinecrest, Miami Beach and more. Call (786) 273-2524.",
        "crumb_home": "Home", "crumb_here": "Service areas",
        "eyebrow": "Where we build",
        "h1": "High-end work, close to home",
        "sub": "Every remodeling, addition, kitchen, bath, and outdoor-living service PGX Builders Group offers, in every Miami-Dade community we serve. Pick your neighborhood.",
        "note": "Don't see your neighborhood? If it's in Miami-Dade or Broward, call (786) 273-2524 — we probably build there.",
        "collection_name": "PGX Builders Group — Service Areas",
        "cta_heading": "Tell us where you are building",
        "cta_sub": "Wherever you are on this list, the process is the same: a walk-through, a written scope and a real number \u2014 in English o en espa\u00f1ol.",
    },
    "es": {
        "title": "Zonas de servicio — Contratista en Miami-Dade | PGX Builders",
        "meta": "Dónde construye PGX Builders Group: remodelación integral, ampliaciones, cocinas, baños y exteriores en Coral Gables, Coconut Grove, Pinecrest, Miami Beach y más. Llame al (786) 273-2524.",
        "crumb_home": "Inicio", "crumb_here": "Zonas de servicio",
        "eyebrow": "Dónde construimos",
        "h1": "Obra de alto nivel, cerca de su casa",
        "sub": "Cada servicio de remodelación, ampliación, cocinas, baños y exteriores que ofrece PGX Builders Group, en cada comunidad de Miami-Dade que atendemos. Elija su zona.",
        "note": "¿No ve su zona? Si está en Miami-Dade o Broward, llame al (786) 273-2524 — probablemente construimos ahí.",
        "collection_name": "PGX Builders Group — Zonas de servicio",
        "cta_heading": "D\u00edganos d\u00f3nde va a construir",
        "cta_sub": "Est\u00e9 donde est\u00e9 en esta lista, el proceso es el mismo: un recorrido, un alcance por escrito y un n\u00famero real \u2014 en espa\u00f1ol o en ingl\u00e9s.",
    },
}


def render_areas_index(data, lang):
    c = AREAS_PAGE_COPY[lang]
    afig = esc(DETAIL_ALT[lang]["addition"][0])
    afig2 = esc(DETAIL_ALT[lang]["kitchen"][1])
    county_label = {"Miami-Dade": {"en": "Miami-Dade County", "es": "Condado de Miami-Dade"},
                    "Broward": {"en": "Broward County", "es": "Condado de Broward"}}
    groups = {}
    for a in PLAN["areas"]:
        if a["slug"] not in data[lang]:
            continue
        groups.setdefault(a.get("county", "Miami-Dade"), []).append(a)
    sections = []
    for county, areas in groups.items():
        blocks = []
        for a in areas:
            links = "".join(
                f'<a class="chip" href="{url_for(s, a["slug"], lang)}">{esc(svc_name(s, lang))}</a>\n        '
                for s in SERVICE_ORDER)
            blocks.append(f'''    <div class="ar-block rv">
      <h3 class="disp"><a href="{url_for('home-remodeling', a['slug'], lang)}">{esc(a['name'])}</a></h3>
      <div class="area-wrap">
        {links.rstrip()}
      </div>
    </div>''')
        label = county_label.get(county, {}).get(lang, county)
        sections.append(f'    <h2 class="disp ar-county rv">{esc(label)}<span class="dot">.</span></h2>\n'
                        + "\n".join(blocks))
    body = "\n".join(sections)
    head_extra = """<style>
.ar-county{font-size:clamp(28px,3.4vw,42px);margin:clamp(44px,5vw,72px) 0 4px}
.ar-county:first-of-type{margin-top:0}
.ar-block{border-top:1px solid var(--line);padding:30px 0 36px}
.ar-block h3{font-size:clamp(22px,2.6vw,30px)}
.ar-block h3 a{text-decoration:none;transition:color .25s}
.ar-block h3 a:hover{color:var(--brass-ink)}
.ar-block .area-wrap{margin-top:16px}
</style>"""
    tpl = TPL[lang]
    main_re = re.compile(r"<main id=\"top\">.*?</main>", re.S)
    listing = f'''<main id="top">
<section class="hero" style="padding-bottom:clamp(24px,3vw,40px)">
  <div class="wrap">
    <nav class="crumbs rv" aria-label="Breadcrumb"><a href="{home_url(lang)}">{c["crumb_home"]}</a><span class="sep">/</span><span>{c["crumb_here"]}</span></nav>
    <p class="eyebrow rv">{c["eyebrow"]}</p>
    <h1 class="disp h1 rv rv-d1">{c["h1"]}<span class="dot">.</span></h1>
    <p class="hero-sub rv rv-d2">{c["sub"]}</p>
  </div>
</section>
<section class="sec" style="padding-top:clamp(20px,3vw,40px)">
  <div class="wrap">
    <figure class="fig-wide rv" style="margin-top:0"><!--AREAS_FIG--><img src="images/detail/addition-1.webp" srcset="images/detail/addition-1-420.webp 420w, images/detail/addition-1-640.webp 640w, images/detail/addition-1-900.webp 900w, images/detail/addition-1.webp 1200w" sizes="(max-width:1300px) 92vw, 1190px" loading="lazy" decoding="async" alt="{afig}" width="1200" height="800"></figure>
{body}
    <figure class="fig-wide rv"><!--AREAS_FIG2--><img src="images/detail/kitchen-2.webp" srcset="images/detail/kitchen-2-420.webp 420w, images/detail/kitchen-2-640.webp 640w, images/detail/kitchen-2-900.webp 900w, images/detail/kitchen-2.webp 1200w" sizes="(max-width:1300px) 92vw, 1190px" loading="lazy" decoding="async" alt="{afig2}" width="1200" height="800"></figure>
    <p class="area-note rv" style="margin-top:26px">{c["note"]}</p>
  </div>
</section>
</main>'''
    # keep the contact section: without it the index pages have no conversion path,
    # the nav/dock #contact anchors dangle, and the form script throws on a null node
    cm = re.search(r'<!-- CONTACT -->.*?</section>', tpl, re.S)
    if cm:
        listing = listing.replace('</main>', cm.group(0) + '\n</main>')
    out = main_re.sub(lambda m: listing, tpl, count=1)
    # AREAS_INDEX_NO_HERO: this page has no hero photograph, so drop its LCP preload
    out = re.sub(r'<link rel="preload" as="image" href="\{\{HERO_IMAGE\}\}"[^>]*>\n', '', out, count=1)
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "CollectionPage",
        "@id": DOMAIN + areas_url(lang) + "#webpage",
        "name": c["collection_name"], "inLanguage": lang,
        "url": DOMAIN + areas_url(lang),
        "isPartOf": {"@id": DOMAIN + "/#website"},
        "about": {"@id": DOMAIN + "/#business"},
        "publisher": {"@id": DOMAIN + "/#business"},
    }, indent=2, ensure_ascii=False)
    repl = {
        "{{TITLE}}": c["title"],
        "{{META_DESCRIPTION}}": c["meta"],
        "{{CANONICAL_URL}}": DOMAIN + areas_url(lang),
        "{{EN_ABS_URL}}": DOMAIN + areas_url("en"),
        "{{ES_ABS_URL}}": DOMAIN + areas_url("es"),
        "{{ALT_URL}}": areas_url("es" if lang == "en" else "en"),
        "{{OG_LOCALE}}": OG_LOCALE[lang],
        "{{OG_LOCALE_ALT}}": OG_LOCALE["es" if lang == "en" else "en"],
        "{{OG_IMAGE_URL}}": DOMAIN + "/og-image.jpg",
        "{{HERO_IMG_ALT}}": esc(c["h1"]),
        "{{JSONLD_SERVICE}}": jsonld,
        "{{JSONLD_BREADCRUMB}}": json.dumps({
            "@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": c["crumb_home"], "item": DOMAIN + home_url(lang)},
                {"@type": "ListItem", "position": 2, "name": c["crumb_here"], "item": DOMAIN + areas_url(lang)},
            ]}, indent=2, ensure_ascii=False),
        "{{JSONLD_FAQ}}": json.dumps({"@context": "https://schema.org", "@type": "WebPage",
                                      "url": DOMAIN + areas_url(lang)}, indent=2),
        "{{AREA_NAME}}": "Miami-Dade",
        "{{SERVICE_NAME}}": "Service areas" if lang == "en" else "Zonas de servicio",
        "{{CTA_HEADING}}": esc(c["cta_heading"]),
        "{{CTA_SUB}}": esc(c["cta_sub"]),
    }
    for k, v in repl.items():
        out = out.replace(k, v)
    out = out.replace("{{FOOTER_SERVICES_HTML}}",
                      "\n".join(f'        <li><a href="{home_url(lang)}#services">{esc(svc_name(s, lang))}</a></li>'
                                for s in SERVICE_ORDER))
    out = out.replace("{{FOOTER_AREAS_HTML}}",
                      "\n".join(f'        <li><a href="{url_for("home-remodeling", a, lang)}">{esc(AREAS[a]["name"])}</a></li>'
                                for a in ["coral-gables", "coconut-grove", "pinecrest", "key-biscayne", "miami-beach", "bal-harbour"]))
    opt_key = "form_option_es" if lang == "es" else "form_option"
    opts = "\n".join(f'                <option>{esc(s[opt_key])}</option>' for s in PLAN["services"])
    for extra in EXTRA_FORM_OPTIONS[lang]:
        opts += f'\n                <option>{esc(extra)}</option>'
    out = out.replace("{{FORM_OPTIONS_HTML}}", opts)
    out = out.replace("</head>", head_extra + "\n</head>")
    leftovers = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if leftovers:
        errors.append(f"{areas_url(lang)}: unreplaced tokens {set(leftovers)}")
    return out


def sync_homepage_chips(data):
    """Rewrite the area chip cloud on both homepages so it always mirrors what was
    actually built. Hand-maintaining 40+ chips in two files guarantees drift."""
    for lang, page in (("en", ROOT / "index.html"), ("es", ROOT / "es.html")):
        if not page.exists():
            continue
        src = page.read_text()
        if "<!-- AREAS:START -->" not in src:
            warnings.append(f"{page.name}: no AREAS markers, chips not synced")
            continue
        chips = []
        for a in PLAN["areas"]:
            if a["slug"] not in data[lang]:
                continue
            chips.append(f'      <a class="chip" href="{url_for("home-remodeling", a["slug"], lang)}"'
                         f' style="text-decoration:none">{esc(a["name"])}</a>')
        block = "<!-- AREAS:START -->\n" + "\n".join(chips) + "\n<!-- AREAS:END -->"
        new = re.sub(r"<!-- AREAS:START -->.*?<!-- AREAS:END -->", lambda m: block, src, flags=re.S)
        if new != src:
            page.write_text(new)


def content_mtime(a_slug: str, lang: str) -> str:
    """lastmod should reflect when the page's copy actually changed."""
    import datetime
    p = CONTENT / (f"{a_slug}.json" if lang == "en" else f"{a_slug}.es.json")
    try:
        return datetime.date.fromtimestamp(p.stat().st_mtime).isoformat()
    except OSError:
        return TODAY



HUB_COPY = {
    "en": {"crumb_home": "Home", "crumb_here": "Services", "scope_all": "Miami-Dade &amp; Broward",
           "where": "Where we build", "note": "Every area we serve, for this service. Not listed? Call (786) 273-2524.",
           "others": "Other PGX services", "browse": "Browse by area"},
    "es": {"crumb_home": "Inicio", "crumb_here": "Servicios", "scope_all": "Miami-Dade y Broward",
           "where": "Dónde construimos", "note": "Todas las zonas que atendemos, para este servicio. ¿No aparece la suya? Llame al (786) 273-2524.",
           "others": "Otros servicios de PGX", "browse": "Ver por zona"},
}


def collapse_scope_line(out: str) -> str:
    """Hero meta reads "{{AREA_NAME}} · {{COUNTY}}".

    On an area page that is "Brickell · Miami-Dade County". On a hub or a property-type page
    both slots are the whole market, which rendered as "Miami-Dade & Broward · Miami-Dade &
    Broward". Collapse the halves when they are identical.
    """
    return re.sub(r'(<span><i></i>)([^<]+) · \2(</span>)', r'\1\2\3', out)


def hub_url(s_slug: str, lang: str) -> str:
    return f"/{svc_slug(s_slug, lang)}"


def render_hub(s_slug, doc, lang, built, has_pair):
    """Service hub: targets the head term and links out to every area page."""
    svc = SERVICES[s_slug]
    c = HUB_COPY[lang]
    name = svc_name(s_slug, lang)
    canonical = DOMAIN + hub_url(s_slug, lang)
    stem = Path(svc["image"]).stem
    srcset = ", ".join(f"images/r/{stem}-{w}.webp {w}w" for w in (420, 640, 900, 1280))
    alt_base = (ALT_BASE_ES[s_slug] if lang == "es" else svc["img_alt_base"].split(" — ")[0])
    img_alt = ALT_TMPL[lang].format(base=alt_base, service=name.lower(), area=c["scope_all"].replace("&amp;", "&"))

    # the payoff: a hub links to all 42 area pages for its service
    groups = {}
    for a in PLAN["areas"]:
        if a["slug"] in built:
            groups.setdefault(a.get("county", "Miami-Dade"), []).append(a)
    blocks = []
    for county, areas in groups.items():
        label = (f"{county} County" if lang == "en"
                 else ("Condado de Miami-Dade" if county == "Miami-Dade" else "Condado de Broward"))
        chips = "\n".join(
            f'      <a class="chip" href="{url_for(s_slug, a["slug"], lang)}">{esc(a["name"])}</a>'
            for a in areas)
        blocks.append(f'      <p class="nb-label" style="margin-top:22px">{esc(label)}</p>\n'
                      f'      <div class="area-wrap">\n{chips}\n      </div>')
    area_grid = "\n".join(blocks)

    intro_html = "\n".join(f"      <p>{esc(p)}</p>" for p in doc["intro_paragraphs"])
    scope_html = "\n".join(
        '      <div class="pr-card rv"><span class="n">%02d</span><h3 class="disp">%s</h3><p>%s</p></div>'
        % (i, esc(it["name"]), esc(it["desc"])) for i, it in enumerate(doc["scope_items"], 1))
    faq_html = "\n".join(
        f'      <details class="fq"{" open" if i == 0 else ""}><summary>{esc(f["q"])}</summary>'
        f'<div class="fa">{esc(f["a"])}</div></details>' for i, f in enumerate(doc["faqs"]))
    rel_svc = "\n".join(
        f'          <a class="chip" href="{hub_url(o, lang)}">{esc(svc_name(o, lang))}</a>'
        for o in SERVICE_ORDER if o != s_slug)

    opt_key = "form_option_es" if lang == "es" else "form_option"
    form_opts = "\n".join('                <option%s>%s</option>' % (
        " selected" if x[opt_key] == svc[opt_key] else "", esc(x[opt_key])) for x in PLAN["services"])
    for extra in EXTRA_FORM_OPTIONS[lang]:
        form_opts += f'\n                <option>{esc(extra)}</option>'

    ld_service = {"@context": "https://schema.org", "@type": "Service",
                  "@id": canonical + "#service", "serviceType": name, "url": canonical,
                  "inLanguage": lang, "provider": PROVIDER,
                  "isPartOf": {"@id": DOMAIN + "/#website"},
                  "areaServed": [{"@type": "AdministrativeArea", "name": "Miami-Dade County, Florida"},
                                 {"@type": "AdministrativeArea", "name": "Broward County, Florida"}]}
    ld_crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": c["crumb_home"], "item": DOMAIN + home_url(lang)},
        {"@type": "ListItem", "position": 2, "name": name, "item": canonical}]}
    ld_faq = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": f["q"],
                              "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in doc["faqs"]]}

    alt = hub_url(s_slug, "es" if lang == "en" else "en") if has_pair else home_url("es" if lang == "en" else "en")
    out = TPL[lang]
    repl = {
        "{{TITLE}}": esc(doc["title"]),
        "{{META_DESCRIPTION}}": esc(doc["meta_description"]),
        "{{CANONICAL_URL}}": canonical,
        "{{EN_ABS_URL}}": DOMAIN + hub_url(s_slug, "en"),
        "{{ES_ABS_URL}}": DOMAIN + hub_url(s_slug, "es"),
        "{{ALT_URL}}": alt,
        "{{OG_LOCALE}}": OG_LOCALE[lang],
        "{{OG_LOCALE_ALT}}": OG_LOCALE["es" if lang == "en" else "en"],
        "{{OG_IMAGE_URL}}": f"{DOMAIN}/images/og/{stem}-og.jpg",
        "{{JSONLD_SERVICE}}": json.dumps(ld_service, indent=2, ensure_ascii=False),
        "{{JSONLD_BREADCRUMB}}": json.dumps(ld_crumb, indent=2, ensure_ascii=False),
        "{{JSONLD_FAQ}}": json.dumps(ld_faq, indent=2, ensure_ascii=False),
        "{{BREADCRUMB_HTML}}": (f'<a href="{home_url(lang)}">{c["crumb_home"]}</a>'
                                f'<span class="sep">/</span><span>{esc(name)}</span>'),
        "{{EYEBROW}}": esc(f'{name} · {c["scope_all"].replace("&amp;", "&")}'),
        "{{H1}}": esc(doc["h1"].rstrip(".")),
        "{{HERO_SUB}}": esc(doc["hero_sub"]),
        "{{HERO_IMAGE}}": svc["image"],
        "{{HERO_SRCSET}}": srcset,
        **detail_tokens(stem, lang),
        "{{HERO_IMG_ALT}}": esc(img_alt),
        "{{AREA_NAME}}": c["scope_all"],
        "{{COUNTY}}": c["scope_all"],
        "{{SERVICE_NAME}}": esc(name),
        "{{LOCAL_HEADING}}": esc(doc["local_heading"].rstrip(".")),
        "{{INTRO_PARAGRAPHS_HTML}}": intro_html,
        "{{NEIGHBORHOOD_CHIPS_HTML}}": area_grid,
        "{{SCOPE_HEADING}}": esc(doc["scope_heading"].rstrip(".")),
        "{{SCOPE_INTRO}}": esc(doc["scope_intro"]),
        "{{SCOPE_CARDS_HTML}}": scope_html,
        "{{FAQ_ITEMS_HTML}}": faq_html,
        "{{RELATED_SERVICES_HTML}}": rel_svc,
        "{{RELATED_AREAS_HTML}}": f'          <a class="chip" href="{areas_url(lang)}">{c["browse"]} →</a>',
        "{{CTA_HEADING}}": esc(doc["cta_heading"]),
        "{{CTA_SUB}}": esc(doc["cta_sub"]),
        "{{FORM_OPTIONS_HTML}}": form_opts,
        "{{FOOTER_SERVICES_HTML}}": "\n".join(
            f'        <li><a href="{hub_url(o, lang)}">{esc(svc_name(o, lang))}</a></li>' for o in SERVICE_ORDER),
        # plan order, not set order: `built` is a set, so iterating it directly made the
        # footer links differ on every build (Python randomises string hashing per process).
        # That churned all 12 hub pages on each render and buried real diffs in the noise.
        "{{FOOTER_AREAS_HTML}}": "\n".join(
            f'        <li><a href="{url_for(s_slug, a["slug"], lang)}">{esc(a["name"])}</a></li>'
            for a in [x for x in PLAN["areas"] if x["slug"] in built][:6]),
    }
    for k, v in repl.items():
        out = out.replace(k, v)
    # the hub replaces the per-area helper line with a service-wide one
    out = out.replace(f'Where we work in {c["scope_all"]}', c["where"])
    out = re.sub(r'<p class="area-note rv rv-d2">.*?</p>',
                 f'<p class="area-note rv rv-d2">{esc(c["note"])}</p>', out, count=1, flags=re.S)
    out = out.replace(f'More PGX services in {c["scope_all"]}', c["others"])
    out = out.replace(f'{name} nearby', c["browse"])
    out = collapse_scope_line(out)
    leftovers = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if leftovers:
        errors.append(f"hub {s_slug}/{lang}: unreplaced {set(leftovers)}")
    return out



ABOUT_COPY = {
    "en": {"crumb_home": "Home", "eyebrow": "About PGX", "here": "About",
           "svc_head": "What we do", "svc_note": "Six services, and the paperwork that makes them legal.",
           "areas_head": "Where we build", "areas_note": "Forty-two communities across Miami-Dade and Broward.",
           "areas_link": "See every service area →"},
    "es": {"crumb_home": "Inicio", "eyebrow": "Sobre PGX", "here": "Nosotros",
           "svc_head": "Qué hacemos", "svc_note": "Seis servicios, y el papeleo que los hace legales.",
           "areas_head": "Dónde construimos", "areas_note": "Cuarenta y dos comunidades en Miami-Dade y Broward.",
           "areas_link": "Vea todas las zonas →"},
}


def about_url(lang):
    return "/nosotros" if lang == "es" else "/about"


def render_about(doc, lang, has_pair):
    c = ABOUT_COPY[lang]
    alt1 = esc(DETAIL_ALT[lang]["remodel"][0])
    alt2 = esc(DETAIL_ALT[lang]["outdoor"][0])
    canonical = DOMAIN + about_url(lang)
    stats = "\n".join(
        f'        <div class="stat"><div class="n">{esc(x["n"])}<em>{esc(x["em"])}</em></div>'
        f'<div class="l">{esc(x["l"])}</div></div>' for x in doc["stats"])
    prins = "\n".join(
        f'        <div class="prin"><h3 class="disp"><i>{esc(x["i"])}</i>{esc(x["h"])}</h3>'
        f'<p>{esc(x["p"])}</p></div>' for x in doc["principles"])
    creds = "\n".join(
        f'        <div class="ct-row"><div class="k">{esc(x["k"])}</div>'
        f'<div class="v">{esc(x["v"])}</div></div>' for x in doc["credentials"])
    intro = "\n".join(f"      <p>{esc(p)}</p>" for p in doc["intro_paragraphs"])
    svc = "\n".join(
        f'        <a class="chip" href="{hub_url(o, lang)}">{esc(svc_name(o, lang))}</a>'
        for o in SERVICE_ORDER)

    listing = f'''<main id="top">
<section class="hero" style="padding-bottom:clamp(24px,3vw,40px)">
  <div class="wrap">
    <nav class="crumbs rv" aria-label="Breadcrumb"><a href="{home_url(lang)}">{c["crumb_home"]}</a><span class="sep">/</span><span>{c["here"]}</span></nav>
    <p class="eyebrow rv">{c["eyebrow"]}</p>
    <h1 class="disp h1 rv rv-d1">{esc(doc["h1"])}<span class="dot">.</span></h1>
    <p class="hero-sub rv rv-d2">{esc(doc["hero_sub"])}</p>
  </div>
</section>
<section class="sec" style="padding-top:clamp(20px,3vw,40px)">
  <div class="wrap">
    <div class="sec-head"><h2 class="disp h2 rv">{esc(doc["local_heading"])}<span class="dot">.</span></h2></div>
    <div class="prose rv rv-d1">
{intro}
    </div>
    <div class="fig-pair rv rv-d1">
      <figure><img src="images/detail/remodel-1.webp" srcset="images/detail/remodel-1-420.webp 420w, images/detail/remodel-1-640.webp 640w, images/detail/remodel-1-900.webp 900w" sizes="(max-width:760px) 92vw, 580px" loading="lazy" decoding="async" alt="{alt1}" width="1200" height="800"></figure>
      <figure><img src="images/detail/outdoor-1.webp" srcset="images/detail/outdoor-1-420.webp 420w, images/detail/outdoor-1-640.webp 640w, images/detail/outdoor-1-900.webp 900w" sizes="(max-width:760px) 92vw, 580px" loading="lazy" decoding="async" alt="{alt2}" width="1200" height="800"></figure>
    </div>
    <p class="nb-label rv rv-d2">{c["svc_head"]}</p>
    <div class="area-wrap rv rv-d2">
{svc}
    </div>
    <p class="area-note rv rv-d2">{c["svc_note"]}</p>
    <p class="nb-label rv rv-d2" style="margin-top:clamp(30px,4vw,44px)">{c["areas_head"]}</p>
    <div class="area-wrap rv rv-d2">
        <a class="chip" href="{areas_url(lang)}">{c["areas_link"]}</a>
    </div>
    <p class="area-note rv rv-d2">{c["areas_note"]}</p>
  </div>
</section>
<section class="sec dark">
  <div class="wrap">
    <div class="sec-head"><p class="eyebrow rv">{"How we work" if lang == "en" else "Cómo trabajamos"}</p>
      <h2 class="disp h2 rv rv-d1">{"A remodel is a promise. We keep it in writing" if lang == "en" else "Una remodelación es una promesa. La dejamos por escrito"}<span class="dot">.</span></h2></div>
    <div class="ap-grid">
      <div class="rv">
{stats}
      </div>
      <div class="rv rv-d1">
{prins}
      </div>
    </div>
  </div>
</section>
<section class="sec" style="padding-bottom:0">
  <div class="wrap">
    <div class="sec-head"><h2 class="disp h2 rv">{esc(doc["credentials_heading"])}<span class="dot">.</span></h2></div>
    <div class="ct-info rv rv-d1" style="max-width:640px;margin-top:clamp(28px,3vw,40px)">
{creds}
    </div>
  </div>
</section>
</main>'''

    tpl = TPL[lang]
    cm = re.search(r'<!-- CONTACT -->.*?</section>', tpl, re.S)
    if cm:
        listing = listing.replace('</main>', cm.group(0) + '\n</main>')
    out = re.sub(r'<main id="top">.*?</main>', lambda m: listing, tpl, count=1, flags=re.S)
    out = re.sub(r'<link rel="preload" as="image" href="\{\{HERO_IMAGE\}\}"[^>]*>\n', '', out, count=1)

    ld = {"@context": "https://schema.org", "@type": "AboutPage",
          "@id": canonical + "#webpage", "url": canonical, "name": doc["title"],
          "inLanguage": lang, "isPartOf": {"@id": DOMAIN + "/#website"},
          "about": {"@id": DOMAIN + "/#business"}, "mainEntity": PROVIDER}
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": c["crumb_home"], "item": DOMAIN + home_url(lang)},
        {"@type": "ListItem", "position": 2, "name": c["here"], "item": canonical}]}
    opt_key = "form_option_es" if lang == "es" else "form_option"
    opts = "\n".join(f'                <option>{esc(x[opt_key])}</option>' for x in PLAN["services"])
    for extra in EXTRA_FORM_OPTIONS[lang]:
        opts += f'\n                <option>{esc(extra)}</option>'
    repl = {
        "{{TITLE}}": esc(doc["title"]), "{{META_DESCRIPTION}}": esc(doc["meta_description"]),
        "{{CANONICAL_URL}}": canonical,
        "{{EN_ABS_URL}}": DOMAIN + about_url("en"), "{{ES_ABS_URL}}": DOMAIN + about_url("es"),
        "{{ALT_URL}}": about_url("es" if lang == "en" else "en") if has_pair else home_url("es" if lang == "en" else "en"),
        "{{OG_LOCALE}}": OG_LOCALE[lang], "{{OG_LOCALE_ALT}}": OG_LOCALE["es" if lang == "en" else "en"],
        "{{OG_IMAGE_URL}}": DOMAIN + "/og-image.jpg", "{{HERO_IMG_ALT}}": esc(doc["h1"]),
        "{{JSONLD_SERVICE}}": json.dumps(ld, indent=2, ensure_ascii=False),
        "{{JSONLD_BREADCRUMB}}": json.dumps(crumb, indent=2, ensure_ascii=False),
        "{{JSONLD_FAQ}}": json.dumps({"@context": "https://schema.org", "@type": "WebPage", "url": canonical}, indent=2),
        "{{AREA_NAME}}": "Miami-Dade &amp; Broward" if lang == "en" else "Miami-Dade y Broward",
        "{{SERVICE_NAME}}": c["here"], "{{CTA_HEADING}}": esc(doc["cta_heading"]),
        "{{CTA_SUB}}": esc(doc["cta_sub"]), "{{FORM_OPTIONS_HTML}}": opts,
        "{{FOOTER_SERVICES_HTML}}": "\n".join(
            f'        <li><a href="{hub_url(o, lang)}">{esc(svc_name(o, lang))}</a></li>' for o in SERVICE_ORDER),
        "{{FOOTER_AREAS_HTML}}": f'        <li><a href="{areas_url(lang)}">{c["areas_link"]}</a></li>',
    }
    for k, v in repl.items():
        out = out.replace(k, v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if left:
        errors.append(f"about/{lang}: unreplaced {set(left)}")
    return out


TYPE_COPY = {
    "en": {"crumb_home": "Home", "here": "Property types", "scope": "Miami-Dade &amp; Broward",
           "where": "Where these homes are",
           "note": "The communities where we do this work most. Not listed? Call (786) 273-2524.",
           "others": "How we work on them", "browse": "Browse every area"},
    "es": {"crumb_home": "Inicio", "here": "Tipos de propiedad", "scope": "Miami-Dade y Broward",
           "where": "Dónde están estas propiedades",
           "note": "Las comunidades donde más hacemos este trabajo. ¿No aparece la suya? Llame al (786) 273-2524.",
           "others": "Cómo trabajamos en ellas", "browse": "Ver todas las zonas"},
}


def type_slug(t_slug: str, lang: str) -> str:
    return TYPES[t_slug]["slug_es"] if lang == "es" else t_slug


def type_name(t_slug: str, lang: str) -> str:
    return TYPES[t_slug]["name_es"] if lang == "es" else TYPES[t_slug]["name"]


def type_url(t_slug: str, lang: str) -> str:
    return f"/{type_slug(t_slug, lang)}"


def render_collection(t_slug, doc, lang, built, has_pair):
    """Property-type page: cuts across every service, for one kind of building."""
    t = TYPES[t_slug]
    c = TYPE_COPY[lang]
    name = type_name(t_slug, lang)
    canonical = DOMAIN + type_url(t_slug, lang)
    stem = Path(t["image"]).stem
    srcset = ", ".join(f"images/r/{stem}-{w}.webp {w}w" for w in (420, 640, 900, 1280))
    img_alt = esc(doc.get("hero_img_alt") or f"{name} — {c['scope']}".replace("&amp;", "&"))

    # only the areas where this property type actually dominates, grouped by county
    mine = [AREAS[a] for a in t.get("areas", []) if a in AREAS and a in built]
    groups = {}
    for a in mine:
        groups.setdefault(a.get("county", "Miami-Dade"), []).append(a)
    blocks = []
    for county, areas in groups.items():
        label = (f"{county} County" if lang == "en"
                 else ("Condado de Miami-Dade" if county == "Miami-Dade" else "Condado de Broward"))
        chips = "\n".join(
            f'      <a class="chip" href="{url_for("home-remodeling", a["slug"], lang)}">{esc(a["name"])}</a>'
            for a in areas)
        blocks.append(f'      <p class="nb-label" style="margin-top:22px">{esc(label)}</p>\n'
                      f'      <div class="area-wrap">\n{chips}\n      </div>')
    area_grid = "\n".join(blocks)

    intro_html = "\n".join(f"      <p>{esc(p)}</p>" for p in doc["intro_paragraphs"])
    scope_html = "\n".join(
        '      <div class="pr-card rv"><span class="n">%02d</span><h3 class="disp">%s</h3><p>%s</p></div>'
        % (i, esc(it["name"]), esc(it["desc"])) for i, it in enumerate(doc["scope_items"], 1))
    faq_html = "\n".join(
        f'      <details class="fq"{" open" if i == 0 else ""}><summary>{esc(f["q"])}</summary>'
        f'<div class="fa">{esc(f["a"])}</div></details>' for i, f in enumerate(doc["faqs"]))
    # the payoff of a cross-cutting page: it hands the reader off to every service
    rel_svc = "\n".join(
        f'          <a class="chip" href="{hub_url(o, lang)}">{esc(svc_name(o, lang))}</a>'
        for o in SERVICE_ORDER)
    # ...and sideways to the other property types
    rel_types = "\n".join(
        f'          <a class="chip" href="{type_url(o, lang)}">{esc(type_name(o, lang))}</a>'
        for o in TYPE_ORDER if o != t_slug)
    rel_areas = (rel_types + "\n" if rel_types else "") + \
        f'          <a class="chip" href="{areas_url(lang)}">{c["browse"]} →</a>'

    opt_key = "form_option_es" if lang == "es" else "form_option"
    form_opts = "\n".join(f'                <option>{esc(x[opt_key])}</option>' for x in PLAN["services"])
    for extra in EXTRA_FORM_OPTIONS[lang]:
        form_opts += f'\n                <option>{esc(extra)}</option>'

    ld_service = {"@context": "https://schema.org", "@type": "Service",
                  "@id": canonical + "#service", "serviceType": name, "url": canonical,
                  "inLanguage": lang, "provider": PROVIDER,
                  "isPartOf": {"@id": DOMAIN + "/#website"},
                  "areaServed": [{"@type": "AdministrativeArea", "name": "Miami-Dade County, Florida"},
                                 {"@type": "AdministrativeArea", "name": "Broward County, Florida"}]}
    ld_crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": c["crumb_home"], "item": DOMAIN + home_url(lang)},
        {"@type": "ListItem", "position": 2, "name": name, "item": canonical}]}
    ld_faq = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": f["q"],
                              "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in doc["faqs"]]}

    alt = type_url(t_slug, "es" if lang == "en" else "en") if has_pair else home_url("es" if lang == "en" else "en")
    out = TPL[lang]
    repl = {
        "{{TITLE}}": esc(doc["title"]),
        "{{META_DESCRIPTION}}": esc(doc["meta_description"]),
        "{{CANONICAL_URL}}": canonical,
        "{{EN_ABS_URL}}": DOMAIN + type_url(t_slug, "en"),
        "{{ES_ABS_URL}}": DOMAIN + type_url(t_slug, "es"),
        "{{ALT_URL}}": alt,
        "{{OG_LOCALE}}": OG_LOCALE[lang],
        "{{OG_LOCALE_ALT}}": OG_LOCALE["es" if lang == "en" else "en"],
        "{{OG_IMAGE_URL}}": f"{DOMAIN}/images/og/{stem}-og.jpg",
        "{{JSONLD_SERVICE}}": json.dumps(ld_service, indent=2, ensure_ascii=False),
        "{{JSONLD_BREADCRUMB}}": json.dumps(ld_crumb, indent=2, ensure_ascii=False),
        "{{JSONLD_FAQ}}": json.dumps(ld_faq, indent=2, ensure_ascii=False),
        "{{BREADCRUMB_HTML}}": (f'<a href="{home_url(lang)}">{c["crumb_home"]}</a>'
                                f'<span class="sep">/</span><span>{esc(name)}</span>'),
        "{{EYEBROW}}": esc(f'{name} · {c["scope"].replace("&amp;", "&")}'),
        "{{H1}}": esc(doc["h1"].rstrip(".")),
        "{{HERO_SUB}}": esc(doc["hero_sub"]),
        "{{HERO_IMAGE}}": t["image"],
        "{{HERO_SRCSET}}": srcset,
        **detail_tokens(stem, lang),
        "{{HERO_IMG_ALT}}": img_alt,
        "{{AREA_NAME}}": c["scope"],
        "{{COUNTY}}": c["scope"],
        "{{SERVICE_NAME}}": esc(name),
        "{{LOCAL_HEADING}}": esc(doc["local_heading"].rstrip(".")),
        "{{INTRO_PARAGRAPHS_HTML}}": intro_html,
        "{{NEIGHBORHOOD_CHIPS_HTML}}": area_grid,
        "{{SCOPE_HEADING}}": esc(doc["scope_heading"].rstrip(".")),
        "{{SCOPE_INTRO}}": esc(doc["scope_intro"]),
        "{{SCOPE_CARDS_HTML}}": scope_html,
        "{{FAQ_ITEMS_HTML}}": faq_html,
        "{{RELATED_SERVICES_HTML}}": rel_svc,
        "{{RELATED_AREAS_HTML}}": rel_areas,
        "{{CTA_HEADING}}": esc(doc["cta_heading"]),
        "{{CTA_SUB}}": esc(doc["cta_sub"]),
        "{{FORM_OPTIONS_HTML}}": form_opts,
        "{{FOOTER_SERVICES_HTML}}": "\n".join(
            f'        <li><a href="{hub_url(o, lang)}">{esc(svc_name(o, lang))}</a></li>' for o in SERVICE_ORDER),
        "{{FOOTER_AREAS_HTML}}": "\n".join(
            f'        <li><a href="{url_for("home-remodeling", a["slug"], lang)}">{esc(a["name"])}</a></li>'
            for a in mine[:6]),
    }
    for k, v in repl.items():
        out = out.replace(k, v)
    # the per-area helper lines become property-type ones
    out = out.replace(f'Where we work in {c["scope"]}', c["where"])
    out = re.sub(r'<p class="area-note rv rv-d2">.*?</p>',
                 f'<p class="area-note rv rv-d2">{esc(c["note"])}</p>', out, count=1, flags=re.S)
    out = out.replace(f'More PGX services in {c["scope"]}', c["others"])
    out = out.replace(f'{name} nearby', c["browse"])
    out = collapse_scope_line(out)
    leftovers = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if leftovers:
        errors.append(f"type {t_slug}/{lang}: unreplaced {set(leftovers)}")
    return out


def sitemap_entry(loc, en_url=None, es_url=None, lastmod=None):
    lines = [f"  <url>", f"    <loc>{loc}</loc>", f"    <lastmod>{lastmod or TODAY}</lastmod>"]
    if en_url and es_url:
        lines.append(f'    <xhtml:link rel="alternate" hreflang="en" href="{en_url}"/>')
        lines.append(f'    <xhtml:link rel="alternate" hreflang="es" href="{es_url}"/>')
        lines.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{en_url}"/>')
    lines.append("  </url>")
    return "\n".join(lines)


def main():
    check_only = "--check-only" in sys.argv
    # --force renders despite validation errors so the templates can be previewed while
    # content is still being written; it never bypasses the check for a real publish
    force = "--force" in sys.argv
    data = load_content()
    validate(data)
    if errors:
        print("VALIDATION ERRORS:")
        for e in errors:
            print("  -", e)
    if warnings:
        # "not yet written" is expected during a county rollout and would otherwise bury
        # the warnings that actually need attention, so report it as a count, not a list
        pending = [w for w in warnings if w.startswith("not yet written")]
        real = [w for w in warnings if not w.startswith("not yet written")]
        if pending:
            print(f"pending content: {len(pending)} area/language files not written yet")
        if real:
            print(f"warnings ({len(real)}):")
            for w in real:
                print("  -", w)
    if errors and not force:
        sys.exit(1)
    if errors:
        print(f"--force: rendering anyway despite {len(errors)} error(s) — preview only, do not publish")
    if check_only:
        print(f"OK: {len(data['en'])} EN + {len(data['es'])} ES areas validated, no errors")
        return

    entries = [sitemap_entry(DOMAIN + "/", DOMAIN + "/", DOMAIN + "/es"),
               sitemap_entry(DOMAIN + "/es", DOMAIN + "/", DOMAIN + "/es"),
               sitemap_entry(DOMAIN + "/areas", DOMAIN + "/areas", DOMAIN + "/zonas"),
               sitemap_entry(DOMAIN + "/zonas", DOMAIN + "/areas", DOMAIN + "/zonas")]
    counts = {"en": 0, "es": 0}
    for a_slug in AREAS:
        for s_slug in SERVICE_ORDER:
            in_en = s_slug in data["en"].get(a_slug, {}).get("pages", {})
            in_es = s_slug in data["es"].get(a_slug, {}).get("pages", {})
            if not (in_en or in_es):
                continue
            has_pair = in_en and in_es
            en_url, es_url = lang_pair_urls(s_slug, a_slug, has_pair)
            for lang in ("en", "es"):
                if a_slug not in data[lang] or s_slug not in data[lang][a_slug]["pages"]:
                    continue
                out = render_page(a_slug, s_slug, data[lang][a_slug], lang, has_pair,
                                  built=set(data[lang]))
                (ROOT / file_for(s_slug, a_slug, lang)).write_text(out)
                counts[lang] += 1
                loc = DOMAIN + url_for(s_slug, a_slug, lang)
                lm = content_mtime(a_slug, lang)
                entries.append(sitemap_entry(loc, en_url, es_url, lm) if has_pair
                               else sitemap_entry(loc, lastmod=lm))
    hubs = data.get("hub", {"en": {}, "es": {}})
    for sl in SERVICE_ORDER:
        pair = sl in hubs["en"] and sl in hubs["es"]
        for lang in ("en", "es"):
            if sl not in hubs[lang]:
                continue
            out = render_hub(sl, hubs[lang][sl], lang, set(data[lang]), pair)
            (ROOT / f"{svc_slug(sl, lang)}.html").write_text(out)
            counts[lang] += 1
            loc = DOMAIN + hub_url(sl, lang)
            entries.append(sitemap_entry(loc, DOMAIN + hub_url(sl, "en"), DOMAIN + hub_url(sl, "es"))
                           if pair else sitemap_entry(loc))

    types = data.get("type", {"en": {}, "es": {}})
    for tl in TYPE_ORDER:
        pair = tl in types["en"] and tl in types["es"]
        for lang in ("en", "es"):
            if tl not in types[lang]:
                continue
            out = render_collection(tl, types[lang][tl], lang, set(data[lang]), pair)
            (ROOT / f"{type_slug(tl, lang)}.html").write_text(out)
            counts[lang] += 1
            loc = DOMAIN + type_url(tl, lang)
            entries.append(sitemap_entry(loc, DOMAIN + type_url(tl, "en"), DOMAIN + type_url(tl, "es"))
                           if pair else sitemap_entry(loc))

    ab = {}
    for lang, nm in (("en", "page-about.json"), ("es", "page-about.es.json")):
        f2 = CONTENT / nm
        if f2.exists():
            ab[lang] = json.loads(f2.read_text())
    for lang, doc in ab.items():
        (ROOT / (about_url(lang).lstrip("/") + ".html")).write_text(
            render_about(doc, lang, len(ab) == 2))
        counts[lang] += 1
        loc = DOMAIN + about_url(lang)
        entries.append(sitemap_entry(loc, DOMAIN + about_url("en"), DOMAIN + about_url("es"))
                       if len(ab) == 2 else sitemap_entry(loc))

    sync_homepage_chips(data)
    (ROOT / "areas.html").write_text(render_areas_index(data, "en"))
    if data["es"]:
        (ROOT / "zonas.html").write_text(render_areas_index(data, "es"))
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(entries) + "\n</urlset>\n")
    if errors:
        print("POST-RENDER ERRORS:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print(f"rendered {counts['en']} EN + {counts['es']} ES pages, areas.html"
          + (", zonas.html" if data["es"] else "") + f", sitemap.xml ({len(entries)} URLs)")


if __name__ == "__main__":
    main()
