#!/usr/bin/env python3
"""Generate template-es.html from template.html by swapping boilerplate strings.

Every replacement must match exactly once (or the stated count) — errors otherwise,
so template drift is caught instead of silently shipping half-translated pages.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
src = (HERE / "template.html").read_text()

# (old, new, expected_count)
REPL = [
    ('<html lang="en">', '<html lang="es">', 1),
    ('aria-label="PGX Builders Group — home"', 'aria-label="PGX Builders Group — inicio"', 1),
    ('<a class="brand" href="/"', '<a class="brand" href="/es"', 1),
    ('<nav aria-label="Primary">', '<nav aria-label="Principal">', 1),
    ('<nav aria-label="Mobile">', '<nav aria-label="Móvil">', 1),
    ('>Local know-how</a>', '>Experiencia local</a>', 2),
    (">What's included</a>", '>Qué incluye</a>', 2),
    ('>Process</a>', '>Proceso</a>', 2),
    ('>FAQ</a>', '>Preguntas</a>', 2),
    ('>Contact</a>', '>Contacto</a>', 2),
    ('<a class="lang" href="{{ALT_URL}}" lang="es" hreflang="es">ES</a>',
     '<a class="lang" href="{{ALT_URL}}" lang="en" hreflang="en">EN</a>', 1),
    ('<br><a class="mm-lang" href="{{ALT_URL}}" lang="es" hreflang="es">Español</a>',
     '<br><a class="mm-lang" href="{{ALT_URL}}" lang="en" hreflang="en">English</a>', 1),
    ('>Get an estimate</a>', '>Pedir un estimado</a>', 1),
    ('aria-label="Menu"', 'aria-label="Menú"', 1),
    ('aria-label="Quick contact"', 'aria-label="Contacto rápido"', 1),
    ('>Call</a>', '>Llamar</a>', 1),
    ('<a class="d-est" href="#contact">Estimate</a>', '<a class="d-est" href="#contact">Estimado</a>', 1),
    ('aria-label="Breadcrumb"', 'aria-label="Ruta"', 1),
    ('Request an estimate <span class="arr">→</span>', 'Solicitar un estimado <span class="arr">→</span>', 1),
    ('<span><i></i>Licensed &amp; insured</span>', '<span><i></i>Licenciado y asegurado</span>', 1),
    ('<span lang="es"><i></i>Hablamos español</span>', '<span lang="en"><i></i>We speak English</span>', 1),
    ('<p class="eyebrow rv">{{SERVICE_NAME}} in {{AREA_NAME}}</p>',
     '<p class="eyebrow rv">{{SERVICE_NAME}} en {{AREA_NAME}}</p>', 1),
    ('Where we work in {{AREA_NAME}}', 'Dónde trabajamos en {{AREA_NAME}}', 1),
    ("Elsewhere in {{AREA_NAME}}? Call us — if it's in Miami-Dade or Broward, we probably build there.",
     '¿En otra parte de {{AREA_NAME}}? Llámenos — si está en Miami-Dade o Broward, probablemente construimos ahí.', 1),
    ('<p class="eyebrow rv">What\'s included</p>', '<p class="eyebrow rv">Qué incluye</p>', 1),
    ('<p class="eyebrow rv">How we work</p>', '<p class="eyebrow rv">Cómo trabajamos</p>', 1),
    ('A remodel is a promise. We keep it in writing<span class="dot">.</span>',
     'Una remodelación es una promesa. La dejamos por escrito<span class="dot">.</span>', 1),
    ('Years building in South Florida', 'Años construyendo en el sur de la Florida', 1),
    ('Remodels and additions delivered', 'Remodelaciones y ampliaciones entregadas', 1),
    ('Permitted and inspected work', 'Obra con permisos e inspecciones', 1),
    ('Team accountable from estimate to warranty', 'Un solo equipo responsable, del estimado a la garantía', 1),
    ('<i>A</i>Fixed scope, honest pricing', '<i>A</i>Alcance fijo, precios honestos', 1),
    ('A detailed written scope before we start — so the number you sign is the number you pay, and changes are decisions, not surprises.',
     'Un alcance detallado por escrito antes de empezar — para que el número que firma sea el número que paga, y los cambios sean decisiones, no sorpresas.', 1),
    ('<i>B</i>A superintendent on site, daily', '<i>B</i>Un superintendente en obra, todos los días', 1),
    ('Your project is run by someone whose name you know, who answers the phone, and who walks the site every working day.',
     'Su proyecto lo dirige alguien con nombre y apellido, que contesta el teléfono y recorre la obra cada día laboral.', 1),
    ('<i>C</i>Built to code, warrantied in writing', '<i>C</i>Según código y con garantía por escrito', 1),
    ('HVHZ-rated products, inspected phases, closed permits, and a written warranty when we hand back the keys.',
     'Productos con clasificación HVHZ, fases inspeccionadas, permisos cerrados y una garantía por escrito al entregar las llaves.', 1),
    ('<p class="eyebrow rv">How it goes</p>', '<p class="eyebrow rv">Cómo funciona</p>', 1),
    ('From first walk to final walk-through<span class="dot">.</span>',
     'Del primer recorrido a la entrega final<span class="dot">.</span>', 1),
    ('Walk-through &amp; estimate</h3><p>We visit, measure, listen, and come back with a real scope and a real number — not a teaser.</p><span class="t">1–2 weeks</span>',
     'Recorrido y estimado</h3><p>Visitamos, medimos, escuchamos y regresamos con un alcance real y un número real — no un gancho.</p><span class="t">1–2 semanas</span>', 1),
    ('Design &amp; permits</h3><p>Drawings, engineering where needed, product approvals, and the permit package — filed and tracked by us.</p><span class="t">4–10 weeks</span>',
     'Diseño y permisos</h3><p>Planos, ingeniería cuando se requiere, aprobaciones de producto y el paquete de permisos — presentado y gestionado por nosotros.</p><span class="t">4–10 semanas</span>', 1),
    ('Construction</h3><p>Scheduled trades, daily supervision, weekly updates with photos, and inspections passed on the first visit.</p><span class="t">Per scope</span>',
     'Construcción</h3><p>Oficios programados, supervisión diaria, reportes semanales con fotos e inspecciones aprobadas a la primera.</p><span class="t">Según alcance</span>', 1),
    ('Closeout &amp; warranty</h3><p>Punch list cleared, permits closed, documents handed over, warranty in writing. Then we leave it spotless.</p><span class="t">1–2 weeks</span>',
     'Cierre y garantía</h3><p>Lista de detalles resuelta, permisos cerrados, documentos entregados y garantía por escrito. Y dejamos todo impecable.</p><span class="t">1–2 semanas</span>', 1),
    ('<p class="eyebrow rv">FAQ</p>', '<p class="eyebrow rv">Preguntas frecuentes</p>', 1),
    ('Straight answers<span class="dot">.</span>', 'Respuestas claras<span class="dot">.</span>', 1),
    ('<h3>More PGX services in {{AREA_NAME}}</h3>', '<h3>Más servicios de PGX en {{AREA_NAME}}</h3>', 1),
    ('<h3>{{SERVICE_NAME}} nearby</h3>', '<h3>{{SERVICE_NAME}} en zonas cercanas</h3>', 1),
    ('<a class="chip" href="/areas">All service areas →</a>', '<a class="chip" href="/zonas">Todas las zonas →</a>', 1),
    ('<p class="eyebrow rv">Contact</p>', '<p class="eyebrow rv">Contacto</p>', 1),
    ('<div class="k">Phone</div>', '<div class="k">Teléfono</div>', 1),
    ('<div class="k">Email</div>', '<div class="k">Correo</div>', 1),
    ('<div class="k">Office</div>', '<div class="k">Oficina</div>', 1),
    ('<div class="k">Hours</div>', '<div class="k">Horario</div>', 1),
    ('<div class="v">Mon–Fri, 8:00–18:00</div>', '<div class="v">Lun–Vie, 8:00–18:00</div>', 1),
    ('<label for="fName">Name</label>', '<label for="fName">Nombre</label>', 1),
    ('<label for="fPhone">Phone</label>', '<label for="fPhone">Teléfono</label>', 1),
    ('<label for="fEmail">Email</label>', '<label for="fEmail">Correo electrónico</label>', 1),
    ('<label for="fType">Project type</label>', '<label for="fType">Tipo de proyecto</label>', 1),
    ('<label for="fMsg">Tell us about the project</label>', '<label for="fMsg">Cuéntenos sobre el proyecto</label>', 1),
    ('placeholder="Address in {{AREA_NAME}}, what you want to change, rough timeline…"',
     'placeholder="Dirección en {{AREA_NAME}}, qué desea cambiar, plazos aproximados…"', 1),
    ('Send request <span class="arr">→</span>', 'Enviar solicitud <span class="arr">→</span>', 1),
    ('Opens your email app — nothing is stored on this site.', 'Se abre su aplicación de correo — este sitio no guarda nada.', 1),
    ('General contractor · Remodeling, additions &amp; permitting across Miami-Dade and Broward.',
     'Contratista general · Remodelaciones, ampliaciones y permisos en Miami-Dade y Broward.', 1),
    ('<p class="ft-h">In {{AREA_NAME}}</p>', '<p class="ft-h">En {{AREA_NAME}}</p>', 1),
    ('<p class="ft-h">Nearby areas</p>', '<p class="ft-h">Zonas cercanas</p>', 1),
    ('<li><a href="/areas">All service areas</a></li>', '<li><a href="/zonas">Todas las zonas</a></li>', 1),
    ('<p class="ft-h">Contact</p>', '<p class="ft-h">Contacto</p>', 1),
    ('<li><a href="/about">About PGX</a></li>', '<li><a href="/nosotros">Sobre PGX</a></li>', 1),
    ('<li><a href="/#contact">Request an estimate</a></li>', '<li><a href="/es#contact">Solicitar un estimado</a></li>', 1),
    ('© 2026 PGX Builders Group LLC · Lic. CGC1539072 · Licensed &amp; insured',
     '© 2026 PGX Builders Group LLC · Lic. CGC1539072 · Licenciado y asegurado', 1),
    ('<a href="/" style="color:inherit;text-decoration:none">pgxusa.com</a>',
     '<a href="/es" style="color:inherit;text-decoration:none">pgxusa.com</a>', 1),
    ("'Estimate request — '", "'Solicitud de estimado — '", 1),
]

problems = []
for old, new, n in REPL:
    c = src.count(old)
    if c != n:
        problems.append(f"expected {n}x, found {c}x: {old[:70]!r}")
        continue
    src = src.replace(old, new)

if problems:
    raise SystemExit("template-es generation FAILED:\n  " + "\n  ".join(problems))

(HERE / "template-es.html").write_text(src)
print("template-es.html generated OK")
