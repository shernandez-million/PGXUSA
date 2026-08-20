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

FIELD_LIMITS = {
    "en": {"title": (40, 70), "meta_description": (120, 162)},
    "es": {"title": (40, 75), "meta_description": (120, 160)},
}
COMMON_FIELDS = ["h1", "hero_sub", "local_heading", "scope_heading",
                 "scope_intro", "cta_heading", "cta_sub"]
EXTRA_FORM_OPTIONS = {"en": ["Permitting / compliance", "Something else"],
                      "es": ["Permisos / cumplimiento", "Otro"]}
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
    return data


def validate(data: dict) -> None:
    for lang, docs in data.items():
        seen = {"title": {}, "h1": {}, "meta_description": {}}
        limits = FIELD_LIMITS[lang]
        for a_slug, doc in docs.items():
            nb = doc.get("neighborhoods", [])
            if not (8 <= len(nb) <= 14):
                errors.append(f"[{lang}] {a_slug}: neighborhoods count {len(nb)} (need 8-14)")
            pages = doc.get("pages", {})
            if set(pages) != set(SERVICE_ORDER):
                errors.append(f"[{lang}] {a_slug}: page keys {sorted(pages)} != services")
                continue
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
    },
}


def render_areas_index(data, lang):
    c = AREAS_PAGE_COPY[lang]
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
{body}
    <p class="area-note rv">{c["note"]}</p>
  </div>
</section>
</main>'''
    out = main_re.sub(lambda m: listing, tpl, count=1)
    # AREAS_INDEX_NO_HERO: this page has no hero photograph, so drop its LCP preload
    out = re.sub(r'<link rel="preload" as="image" href="\{\{HERO_IMAGE\}\}"[^>]*>\n', '', out, count=1)
    jsonld = json.dumps({"@context": "https://schema.org", "@type": "CollectionPage",
                         "name": c["collection_name"], "inLanguage": lang,
                         "url": DOMAIN + areas_url(lang)}, indent=2, ensure_ascii=False)
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
            has_pair = a_slug in data["en"] and a_slug in data["es"]
            en_url, es_url = lang_pair_urls(s_slug, a_slug, has_pair)
            for lang in ("en", "es"):
                if a_slug not in data[lang]:
                    continue
                out = render_page(a_slug, s_slug, data[lang][a_slug], lang, has_pair,
                                  built=set(data[lang]))
                (ROOT / file_for(s_slug, a_slug, lang)).write_text(out)
                counts[lang] += 1
                loc = DOMAIN + url_for(s_slug, a_slug, lang)
                lm = content_mtime(a_slug, lang)
                entries.append(sitemap_entry(loc, en_url, es_url, lm) if has_pair
                               else sitemap_entry(loc, lastmod=lm))
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
