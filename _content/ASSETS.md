# Asset provenance

House rule **P-11 (procedencia de activos)**: no third-party photograph, text or
editorial datum enters the product without a license or an owned source, and no
agent downloads media from a publisher's site or copies its text.

This is the register for pgxusa.com — what each asset is, its SHA-256, and how
far its origin can actually be attested, **including where it cannot**.

    python3 _content/verify_assets.py          # registration + hashes + width variants
    python3 _content/verify_assets.py --deep   # also re-matches every crop to its base (~10 min)

The check that matters is the first one: it fails on any media file the site
carries that this register does not list. That is the shape the rule exists to
catch — a downloaded photograph quietly added to `images/`.

---

## 1. The seven base images — origin NOT attested

| File | SHA-256 | Entered the repo |
|---|---|---|
| `images/hero.webp` | `4c78d38aee794cdde4ca91673006cd5b…` | 5e2b581 2026-08-04 shernandez-million |
| `images/kitchen.webp` | `ee82db3a163f0bfe3a6d593c7ffbec85…` | 5e2b581 2026-08-04 shernandez-million |
| `images/bath.webp` | `01859d06f4f1822c144d55678b2ff2d4…` | 5e2b581 2026-08-04 shernandez-million |
| `images/addition.webp` | `aa34ea0d416d55a66fd164a9a65c7144…` | 5e2b581 2026-08-04 shernandez-million |
| `images/outdoor.webp` | `8f8e6d713bb95d0f33adf298440dcfab…` | 5e2b581 2026-08-04 shernandez-million |
| `images/permit.webp` | `ff677354cccc38a9cf696edb98825601…` | 5e2b581 2026-08-04 shernandez-million |
| `images/remodel.webp` | `5986c81c1738acaa2379b3f40fb83ca1…` | 5e2b581 2026-08-04 shernandez-million |

They arrived in the repository's first commit, with the site itself, from the
account that originally published it. **Nothing in this repository establishes
who made them or under what license.** No agent working here downloaded them:
the build scripts contain no fetch of any kind, and no page references any
external host (§5). Six of the seven are exactly 1600×1066 — the uniformity of a
batch download, not of a photographer's delivery.

Two consequences, both already in force:

- **Nothing claims they are PGX's work.** All 524 pages describe their images in
  the alt text as an *architectural rendering* / *render arquitectónico*. Until
  2026-09-06 only the hero carried that disclosure and the two supporting images
  did not, so a reader could have taken those for photographs of finished jobs;
  `RENDER_NOTE` in `build.py` now appends it to every image on the site.
- **The portfolio stays unpublished** (CLAUDE.md §5). Photographs of real
  projects, with the client's permission, are the only thing that closes this.

Until Andrés attests their origin, treat them as unlicensed: do not reuse them
in another product, and never present them as photographs.

### Superseded originals, kept for reference

| File | SHA-256 | Entered the repo |
|---|---|---|
| `_content/remodel-original-oldlogo.webp` | `65299327acfaab53fb1ee9db64c63954…` | 43e3de0 2026-08-20 andres56789 |
| `_content/pgx-wordmark-traced-original.svg` | `47d25c0c484d4abc0b9da13f478fabe9…` | ee38e44 2026-08-20 andres56789 |

`_content/images-original/` holds the pre-crop copies of the same seven images
and inherits this section exactly. It is not published.

## 2. Derived images — 82 files, mechanically verified

Generated from §1 and §3; they inherit that provenance.

| Family | Verified as |
|---|---|
| `images/r/*.webp` (28) | width variants — each differs from a LANCZOS downscale of the base it names by ≤ 8/255 |
| `images/detail/*.webp` (48) | two crop regions per base, four widths each. A crop search across all seven bases returns *its own* base as the best match for all 48, so no page shows another service's image |
| `images/og/*.jpg` (6) | share cards built by `make_og.py` from the base of the same name plus the wordmark plate |

## 3. Brand marks — PGX's own

| File | SHA-256 | Entered the repo |
|---|---|---|
| `images/pgx-mark.png` | `d0acfdf16ddbfd1b7302d723f80f371c…` | 5e2b581 2026-08-04 shernandez-million |
| `images/pgx-logo.png` | `9eb119162537b11b404f86b8030ec968…` | 01040db 2026-08-20 andres56789 |
| `images/pgx-wordmark.svg` | `18aecfe74451a76f25ea691ef30eaaea…` | 6c6e9bd 2026-08-20 andres56789 |
| `images/pgx-wordmark-outline.svg` | `59a28b9d8ce0b791971a3151fc34a8dd…` | 050c0b1 2026-08-20 andres56789 |
| `favicon.svg` | `04a72748aac371abe1d4411e80ee5951…` | 7e3f6a2 2026-08-21 andres56789 |
| `favicon.png` | `4f9cf50f3fd9ee6d5a9d8ee1146a2c76…` | 5e2b581 2026-08-04 shernandez-million |
| `favicon-32.png` | `e9f2e289a0b06d106f9fa82ac4d1efa8…` | 5e2b581 2026-08-04 shernandez-million |
| `favicon-96.png` | `166a21c43a7953f3ca964bedf399c82f…` | 7e3f6a2 2026-08-21 andres56789 |
| `icon-512.png` | `568d64a003b2d3e759b8b8b16c3603e6…` | 7e3f6a2 2026-08-21 andres56789 |
| `apple-touch-icon.png` | `c7cfe3b3cbad098334f2464615bf533f…` | 5e2b581 2026-08-04 shernandez-million |
| `og-image.jpg` | `1e2c62859065bb1f713519ae0e9f7520…` | 5e2b581 2026-08-04 shernandez-million |

`pgx-wordmark.svg` is a trace of a raster logo, refit to Béziers by
`smooth_logo.py`; the icon set and `og-image.jpg` are rasterised from it by
`make_favicons.py` and `make_og.py`. A true vector original from the designer
is still an open item (CLAUDE.md §6).

## 4. Fonts — SIL Open Font License 1.1

| File | SHA-256 | Entered the repo |
|---|---|---|
| `fonts/inter-var-latin.woff2` | `c940764593d0fe5d596be327ca755885…` | 30e9bc0 2026-08-20 andres56789 |
| `fonts/inter-var-latinext.woff2` | `a28eb6d3ccb534ae0c94ca999371df02…` | 30e9bc0 2026-08-20 andres56789 |
| `fonts/marcellus-400-latin.woff2` | `be9d4883e7f45ed729a83c255d68ea73…` | 72d7112 2026-08-20 andres56789 |
| `fonts/marcellus-400-latinext.woff2` | `75505cecfbcb401d3c012ccaca95b7ef…` | 72d7112 2026-08-20 andres56789 |

Inter © 2016 The Inter Project Authors; Marcellus © 2012 Brian J. Bonislawsky
(Astigmatic), reserved font name "Marcellus". Both carry that copyright and the
license URL inside the file itself, and `fonts/LICENSE.md` restates them. They
are self-hosted — the site loads no font from Google or anywhere else.

## 5. Text and data — no third-party editorial content

Checked 2026-09-06 across all 524 pages and the 122 content packs:

- **No external host is referenced by any page.** The only absolute URLs are
  `https://www.pgxusa.com` (canonicals, hreflang, schema) and `https://wa.me`
  (the WhatsApp link). No third-party image, script, stylesheet or font.
- **No quoted third-party text.** The prose was written for PGX. Statutory
  references — HB 803, the Florida Building Code, milestone inspections, BORA
  Policy 05-05 — are paraphrased facts about public law, not reproduced text.
- **No third-party brands.** No Houzz, Yelp, Angi, BBB, Google-review or
  publisher name appears in the visible content, and there are no testimonials,
  awards, ratings or client names to attribute (CLAUDE.md §2).
