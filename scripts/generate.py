#!/usr/bin/env python3
"""
WORLD CUP SHOP – Produkt-Seiten-Generator
==========================================
Liest Produktdaten aus einem Google Sheet (CSV-Export) und erzeugt:
  - Produktdetailseiten  (product-[slug].html)  im Shop-Root
  - Aktualisiertes Produktgrid in product.html

Voraussetzungen:
  pip install requests

Verwendung:
  python scripts/generate.py                        # Alle aktiven Produkte generieren
  python scripts/generate.py --dry-run              # Vorschau ohne Dateien zu schreiben
  python scripts/generate.py --slug efrin-shirt     # Nur ein bestimmtes Produkt
  python scripts/generate.py --local data/products.csv  # Lokale CSV-Datei statt Sheets
"""

import os
import sys
import csv
import io
import re
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime

# ── Optional dependency ────────────────────────────────────────────────────────
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ── Pfade ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).resolve().parent
SHOP_DIR    = SCRIPT_DIR.parent
TEMPLATE_DIR = SHOP_DIR / "templates"
OUTPUT_DIR  = SHOP_DIR                # Produktseiten landen im Shop-Root
LISTING_PAGE = SHOP_DIR / "product.html"
BACKUP_DIR  = SHOP_DIR / "data" / "backups"
LOG_FILE    = SHOP_DIR / "data" / "generator.log"
CONFIG_FILE = SCRIPT_DIR / "config.json"

# ── Konfiguration laden ────────────────────────────────────────────────────────
import json

def load_config():
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        logging.error(f"Fehler beim Lesen von config.json: {e}")
        return {}

# ── Logging ────────────────────────────────────────────────────────────────────
def setup_logging(verbose=False):
    BACKUP_DIR.parent.mkdir(parents=True, exist_ok=True)
    level = logging.DEBUG if verbose else logging.INFO
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ]
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )

log = logging.getLogger(__name__)

# ── Template laden ─────────────────────────────────────────────────────────────
def load_template(filename):
    path = TEMPLATE_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Template nicht gefunden: {path}\n"
            f"Stelle sicher, dass das templates/-Verzeichnis vollständig ist."
        )
    return path.read_text(encoding="utf-8")

# ── Google Sheets / CSV lesen ──────────────────────────────────────────────────
def fetch_from_url(url: str) -> list[dict]:
    if not HAS_REQUESTS:
        log.error("'requests' Bibliothek fehlt. Bitte installieren: pip install requests")
        sys.exit(1)
    log.info(f"Lade Produktdaten von: {url}")
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return parse_csv(resp.text)
    except requests.RequestException as e:
        log.error(f"Netzwerkfehler beim Laden der Sheets-Daten: {e}")
        sys.exit(1)

def fetch_from_file(path: str) -> list[dict]:
    log.info(f"Lade Produktdaten aus Datei: {path}")
    try:
        content = Path(path).read_text(encoding="utf-8-sig")  # utf-8-sig entfernt BOM
        return parse_csv(content)
    except FileNotFoundError:
        log.error(f"CSV-Datei nicht gefunden: {path}")
        sys.exit(1)

def parse_csv(csv_text: str) -> list[dict]:
    # Zeilen einlesen
    all_rows = list(csv.reader(io.StringIO(csv_text)))

    # Header-Zeile auto-detektieren: erste Zeile, die "name" oder "slug" enthält
    # (nötig wenn Sheet Abschnittsüberschriften oder Hinweiszeilen vor dem Header hat)
    HEADER_KEYS = {"name", "slug", "price", "sku", "status"}
    header_idx = None
    for i, row in enumerate(all_rows):
        normalized = {c.strip().lower().split(" ")[0].rstrip("*").strip() for c in row}
        if len(HEADER_KEYS & normalized) >= 2:
            header_idx = i
            break

    if header_idx is None:
        log.error(
            "Keine gültige Header-Zeile im CSV gefunden.\n"
            "Stelle sicher, dass dein Google Sheet eine Zeile mit 'name', 'slug', 'price', 'sku', 'status' enthält."
        )
        sys.exit(1)

    log.debug(f"Header-Zeile gefunden in CSV-Zeile {header_idx + 1}")

    # Spaltenname normalisieren: "Name *" → "name", "Preis * (€)" → "preis"
    def norm_key(k: str) -> str:
        k = k.strip().lower()
        # Stern und Klammern entfernen, dann Leerzeichen → Unterstrich
        k = re.sub(r"[*\(\)]", "", k)
        k = k.strip().replace(" ", "_")
        # Bekannte deutsche Display-Namen auf interne Keys mappen
        mapping = {
            "name": "name",
            "slug": "slug",
            "preis": "price",
            "price": "price",
            "sku": "sku",
            "status": "status",
            "kurzbeschreibung": "short_desc",
            "short_desc": "short_desc",
            "lange_beschreibung": "long_desc",
            "long_desc": "long_desc",
            "bild_1_pfad": "image1",
            "bild_1": "image1",
            "image1": "image1",
            "bild_2_pfad": "image2",
            "bild_2": "image2",
            "image2": "image2",
            "bild_3_pfad": "image3",
            "bild_3": "image3",
            "image3": "image3",
            "stichpunkte_trennen": "bullets",
            "stichpunkte": "bullets",
            "bullets": "bullets",
            "pflege_trennen": "washing",
            "pflege": "washing",
            "washing": "washing",
            "farben_oder_trennen": "colors",
            "farben": "colors",
            "colors": "colors",
            "kategorie": "category",
            "category": "category",
            "reihenfolge": "sort_order",
            "sort_order": "sort_order",
            "im_grid_zeigen": "show_on_listing",
            "show_on_listing": "show_on_listing",
            "treuepunkte": "loyalty_points",
            "loyalty_points": "loyalty_points",
            "browser-titel": "title",
            "titel": "title",
            "title": "title",
            "meta_description": "meta_description",
            "og_image_pfad": "og_image",
            "og_image": "og_image",
        }
        # Ersten Token (vor erstem Leerzeichen/Unterstrich nach Bereinigung) suchen
        for candidate, internal in mapping.items():
            if k == candidate or k.startswith(candidate):
                return internal
        return k

    raw_headers = all_rows[header_idx]
    headers = [norm_key(h) for h in raw_headers]

    # Datenzeilen: alles nach dem Header, Hinweiszeile direkt nach Header überspringen
    data_start = header_idx + 1
    # Übliche Hinweiszeilen erkennen: Zeile direkt nach Header, die keine echten Produktdaten hat
    # (kein gültiger Slug, kein Preis)
    if data_start < len(all_rows):
        first_data = all_rows[data_start]
        row_dict = dict(zip(headers, first_data))
        slug_val = row_dict.get("slug", "").strip()
        # Wenn der Slug aus der Hinweiszeile stammt (z.B. "URL-Teil, nur a-z 0-9 -"), überspringen
        if slug_val and not re.match(r'^[a-z0-9][a-z0-9\-]*$', slug_val):
            log.debug(f"Hinweiszeile übersprungen (Zeile {data_start + 1})")
            data_start += 1

    rows = []
    for row in all_rows[data_start:]:
        if not any(v.strip() for v in row):  # Leere Zeile
            continue
        clean = {headers[i]: row[i].strip() if i < len(row) else "" for i in range(len(headers))}
        rows.append(clean)

    log.info(f"{len(rows)} Produktzeilen aus CSV geladen")
    return rows

# ── Validierung ────────────────────────────────────────────────────────────────
REQUIRED_FIELDS = ["name", "slug", "price", "sku", "status", "image1", "short_desc"]
VALID_SLUG_RE   = re.compile(r'^[a-z0-9][a-z0-9\-]*[a-z0-9]$')

def validate_product(row: dict, row_num: int) -> list[str]:
    errors = []
    for field in REQUIRED_FIELDS:
        if not row.get(field, "").strip():
            errors.append(f"Pflichtfeld fehlt: '{field}'")
    slug = row.get("slug", "").strip()
    if slug and not VALID_SLUG_RE.match(slug):
        errors.append(
            f"Ungültiger Slug '{slug}' – nur Kleinbuchstaben, Zahlen und Bindestriche erlaubt"
        )
    return errors

def check_slug_duplicates(products: list[dict]) -> list[str]:
    seen = {}
    errors = []
    for p in products:
        slug = p.get("slug", "")
        if slug in seen:
            errors.append(f"Doppelter Slug '{slug}' in Zeile {p['_row_num']} und {seen[slug]}")
        else:
            seen[slug] = p.get("_row_num", "?")
    return errors

# ── Hilfsfunktionen ────────────────────────────────────────────────────────────
COLOR_MAP = {
    "schwarz": "#111111",
    "weiß":    "#f0f0f0",
    "weiss":   "#f0f0f0",
    "rot":     "#e50914",
    "blau":    "#1a5fa8",
    "grün":    "#2e8c4a",
    "gruen":   "#2e8c4a",
    "gelb":    "#f5c518",
    "orange":  "#f5a623",
    "olive":   "#6b6b3a",
    "sand":    "#c4a882",
    "hellblau":"#7ecef4",
    "pink":    "#e8a0b0",
    "lila":    "#7b68ee",
    "grau":    "#888888",
}

def build_color_swatches(colors_raw: str) -> tuple[str, str]:
    """Gibt (farb_label, swatch_html) zurück."""
    if not colors_raw.strip():
        return ("Schwarz, Weiß, Rot, Blau", _default_swatches())
    colors = [c.strip() for c in colors_raw.replace(",", "|").split("|") if c.strip()]
    label = ", ".join(colors)
    swatches = []
    for i, c in enumerate(colors):
        hex_color = COLOR_MAP.get(c.lower(), "#888888")
        active = ' active' if i == 0 else ''
        swatches.append(
            f'<button type="button" class="color-swatch{active}" '
            f'data-color="{c}" style="--swatch-color:{hex_color};" title="{c}"></button>'
        )
    return (label, "\n\t\t\t\t\t\t\t".join(swatches))

def _default_swatches():
    return (
        '<button type="button" class="color-swatch active" data-color="Schwarz" style="--swatch-color:#111111;" title="Schwarz"></button>\n'
        '\t\t\t\t\t\t\t<button type="button" class="color-swatch" data-color="Weiß" style="--swatch-color:#f0f0f0;" title="Weiß"></button>\n'
        '\t\t\t\t\t\t\t<button type="button" class="color-swatch" data-color="Rot" style="--swatch-color:#e50914;" title="Rot"></button>\n'
        '\t\t\t\t\t\t\t<button type="button" class="color-swatch" data-color="Blau" style="--swatch-color:#1a5fa8;" title="Blau"></button>'
    )

def build_list_items(raw: str, indent="\t\t\t\t\t\t\t<li>") -> str:
    """Wandelt '|'-getrennten Text in <li>-Items um."""
    if not raw.strip():
        return ""
    items = [x.strip() for x in raw.split("|") if x.strip()]
    return "\n".join(f"{indent}{item}</li>" for item in items)

def calc_loyalty_points(price_str: str) -> str:
    try:
        return str(int(float(price_str.replace(",", ".")) * 6))
    except (ValueError, AttributeError):
        return "0"

def slugify_category(category: str) -> str:
    """Wandelt Kategorie-String in CSS-Klasse um."""
    return re.sub(r'[^a-z0-9]', '-', category.lower().strip()).strip('-') or "all"

# ── Produktseite generieren ────────────────────────────────────────────────────
def apply_template(template: str, replacements: dict) -> str:
    result = template
    for key, value in replacements.items():
        result = result.replace(f"%%{key}%%", str(value))
    return result

def generate_product_page(product: dict, detail_tmpl: str) -> str:
    slug    = product["slug"]
    name    = product["name"]
    price   = product["price"].replace(",", ".")
    image1  = product.get("image1", "images/product-01.jpg")
    image2  = product.get("image2", "").strip() or image1
    image3  = product.get("image3", "").strip() or image1
    og_img  = product.get("og_image", "").strip() or image1

    loyalty = product.get("loyalty_points", "").strip() or calc_loyalty_points(price)
    title   = product.get("title", "").strip() or product.get("meta_title", "").strip() or f"{name} | WORLD CUP SHOP"
    meta_d  = product.get("meta_description", "").strip() or product.get("short_desc", "")

    colors_label, swatches_html = build_color_swatches(product.get("colors", ""))
    bullets_html  = build_list_items(product.get("bullets",  ""))
    washing_html  = build_list_items(product.get("washing",  ""))

    # Related products: alle anderen aktiven Produkte (max 6)
    related = product.get("_all_active", [])
    related_html = _build_related_items(related, current_slug=slug)

    return apply_template(detail_tmpl, {
        "PRODUCT_TITLE":         title,
        "PRODUCT_META_DESC":     meta_d,
        "PRODUCT_OG_IMAGE":      og_img,
        "PRODUCT_NAME":          name,
        "PRODUCT_PRICE":         price,
        "PRODUCT_SKU":           product.get("sku", ""),
        "PRODUCT_CATEGORY":      product.get("category", ""),
        "PRODUCT_SHORT_DESC":    product.get("short_desc", ""),
        "PRODUCT_LONG_DESC":     product.get("long_desc", ""),
        "PRODUCT_IMAGE1":        image1,
        "PRODUCT_IMAGE2":        image2,
        "PRODUCT_IMAGE3":        image3,
        "PRODUCT_LOYALTY_POINTS": loyalty,
        "PRODUCT_COLORS":        colors_label,
        "PRODUCT_COLOR_SWATCHES": swatches_html,
        "PRODUCT_BULLETS":       bullets_html,
        "PRODUCT_WASHING":       washing_html,
        "RELATED_PRODUCTS":      related_html,
        "PRODUCT_SLUG":          slug,
    })

def _build_related_items(active_products: list, current_slug: str, max_items: int = 6) -> str:
    others = [p for p in active_products if p.get("slug") != current_slug][:max_items]
    if not others:
        return ""
    parts = []
    for p in others:
        img   = p.get("image1", "images/product-01.jpg")
        pname = p.get("name", "Produkt")
        price = p.get("price", "").replace(",", ".")
        url   = f"product-{p['slug']}.html"
        parts.append(
            f'\t\t\t\t\t\t<div class="item-slick2 p-l-15 p-r-15 p-t-15 p-b-15">\n'
            f'\t\t\t\t\t\t\t<div class="block2">\n'
            f'\t\t\t\t\t\t\t\t<div class="block2-pic hov-img0 pos-relative">\n'
            f'\t\t\t\t\t\t\t\t\t<img loading="lazy" src="{img}" alt="{pname}">\n'
            f'\t\t\t\t\t\t\t\t\t<a href="{url}" class="block2-btn flex-c-m stext-103 cl2 size-102 bg0 bor2 hov-btn1 p-lr-15 trans-04">Quick View</a>\n'
            f'\t\t\t\t\t\t\t\t</div>\n'
            f'\t\t\t\t\t\t\t\t<div class="block2-txt flex-w flex-t p-t-14">\n'
            f'\t\t\t\t\t\t\t\t\t<div class="block2-txt-child1 flex-col-l">\n'
            f'\t\t\t\t\t\t\t\t\t\t<a href="{url}" class="stext-104 cl4 hov-cl1 trans-04 p-b-6">{pname}</a>\n'
            f'\t\t\t\t\t\t\t\t\t\t<span class="stext-105 cl3">€{price}</span>\n'
            f'\t\t\t\t\t\t\t\t\t</div>\n'
            f'\t\t\t\t\t\t\t\t</div>\n'
            f'\t\t\t\t\t\t\t</div>\n'
            f'\t\t\t\t\t\t</div>'
        )
    return "\n".join(parts)

# ── Produktkarte für Listing generieren ────────────────────────────────────────
def generate_product_card(product: dict, card_tmpl: str) -> str:
    slug  = product["slug"]
    name  = product["name"]
    price = product["price"].replace(",", ".")
    image = product.get("image1", "images/product-01.jpg")
    url   = f"product-{slug}.html"
    cat_class = slugify_category(product.get("category", "all"))

    return apply_template(card_tmpl, {
        "CARD_CATEGORY_CLASS": cat_class,
        "CARD_URL":   url,
        "CARD_IMAGE": image,
        "CARD_NAME":  name,
        "CARD_PRICE": price,
    })

# ── Listing-Seite aktualisieren ────────────────────────────────────────────────
START_MARKER = "<!-- PRODUCT_GRID_START -->"
END_MARKER   = "<!-- PRODUCT_GRID_END -->"

def update_listing_page(products: list[dict], card_tmpl: str, dry_run=False):
    if not LISTING_PAGE.exists():
        log.error(f"Listing-Seite nicht gefunden: {LISTING_PAGE}")
        return False

    content = LISTING_PAGE.read_text(encoding="utf-8")
    if START_MARKER not in content or END_MARKER not in content:
        log.error(
            f"Marker {START_MARKER!r} oder {END_MARKER!r} nicht in {LISTING_PAGE.name} gefunden.\n"
            "Stelle sicher, dass product.html die Marker enthält."
        )
        return False

    visible = [
        p for p in products
        if p.get("status", "").lower() == "active"
        and p.get("show_on_listing", "yes").lower() in ("yes", "ja", "1", "true", "")
    ]
    # Sortierung: sort_order (numerisch) → name
    def sort_key(p):
        try:
            return (int(p.get("sort_order", "9999") or "9999"), p.get("name", ""))
        except ValueError:
            return (9999, p.get("name", ""))
    visible.sort(key=sort_key)

    log.info(f"Listing: {len(visible)} sichtbare Produkte")

    cards_html = "\n".join(generate_product_card(p, card_tmpl) for p in visible)
    if cards_html:
        cards_html = "\n" + cards_html + "\n\t\t\t\t"

    # Alten Grid-Inhalt ersetzen
    before = content[:content.index(START_MARKER) + len(START_MARKER)]
    after  = content[content.index(END_MARKER):]
    new_content = before + cards_html + after

    if dry_run:
        log.info(f"[DRY-RUN] product.html würde aktualisiert ({len(visible)} Karten)")
        return True

    _backup_file(LISTING_PAGE)
    LISTING_PAGE.write_text(new_content, encoding="utf-8")
    log.info(f"product.html aktualisiert mit {len(visible)} Produktkarten")
    return True

# ── Backup ─────────────────────────────────────────────────────────────────────
def _backup_file(path: Path):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"{path.stem}_{ts}{path.suffix}"
    shutil.copy2(path, dest)
    log.debug(f"Backup erstellt: {dest.name}")

# ── Hauptfunktion ──────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="WORLD CUP SHOP – Produktseiten-Generator"
    )
    parser.add_argument("--dry-run",  action="store_true",
                        help="Dateien nicht schreiben, nur Vorschau ausgeben")
    parser.add_argument("--slug",     type=str, default=None,
                        help="Nur diesen Slug generieren (z.B. --slug efrin-shirt)")
    parser.add_argument("--local",    type=str, default=None,
                        help="Lokale CSV-Datei verwenden statt Google Sheets")
    parser.add_argument("--verbose",  action="store_true",
                        help="Ausführliche Ausgabe")
    args = parser.parse_args()

    setup_logging(args.verbose)

    if args.dry_run:
        log.info("=" * 60)
        log.info("DRY-RUN MODUS – Es werden keine Dateien geschrieben")
        log.info("=" * 60)

    # ── Konfiguration ──────────────────────────────────────────────────────────
    config = load_config()
    csv_url = config.get("sheets_csv_url", "").strip()

    # ── Daten laden ────────────────────────────────────────────────────────────
    if args.local:
        rows = fetch_from_file(args.local)
    elif csv_url:
        rows = fetch_from_url(csv_url)
    else:
        log.error(
            "Keine Datenquelle konfiguriert.\n"
            "Bitte entweder:\n"
            "  a) scripts/config.json mit 'sheets_csv_url' befüllen\n"
            "  b) --local data/meine-produkte.csv angeben"
        )
        sys.exit(1)

    if not rows:
        log.warning("Keine Produktzeilen gefunden. Abbruch.")
        sys.exit(0)

    # ── Zeilennummern eintragen ────────────────────────────────────────────────
    for i, row in enumerate(rows, start=2):  # Start bei 2 (Zeile 1 = Header)
        row["_row_num"] = i

    # ── Validierung ────────────────────────────────────────────────────────────
    valid_products = []
    skipped = 0
    for row in rows:
        errors = validate_product(row, row["_row_num"])
        if errors:
            for e in errors:
                log.warning(f"Zeile {row['_row_num']} ({row.get('name','?')}): {e}")
            skipped += 1
        else:
            valid_products.append(row)

    dup_errors = check_slug_duplicates(valid_products)
    for e in dup_errors:
        log.error(e)
    if dup_errors:
        log.error("Doppelte Slugs gefunden – Abbruch.")
        sys.exit(1)

    # ── Filter: status ─────────────────────────────────────────────────────────
    if args.slug:
        active = [p for p in valid_products if p.get("slug") == args.slug]
        if not active:
            log.error(f"Kein Produkt mit slug='{args.slug}' gefunden.")
            sys.exit(1)
    else:
        active = [p for p in valid_products if p.get("status", "").lower() == "active"]

    draft_count = sum(1 for p in valid_products if p.get("status", "").lower() == "draft")
    log.info(f"Produkte: {len(active)} aktiv, {draft_count} draft, {skipped} übersprungen")

    if not active:
        log.warning("Keine aktiven Produkte. Nichts zu tun.")
        sys.exit(0)

    # ── Templates laden ────────────────────────────────────────────────────────
    try:
        detail_tmpl = load_template("product-detail-template.html")
        card_tmpl   = load_template("product-card-template.html")
    except FileNotFoundError as e:
        log.error(str(e))
        sys.exit(1)

    # ── Alle aktiven Produkte für "Related"-Sektion hinterlegen ───────────────
    all_active_list = [p for p in valid_products if p.get("status", "").lower() == "active"]
    for p in active:
        p["_all_active"] = all_active_list

    # ── Produktdetailseiten generieren ─────────────────────────────────────────
    generated = 0
    failed    = 0

    for product in active:
        slug     = product["slug"]
        filename = f"product-{slug}.html"
        out_path = OUTPUT_DIR / filename

        try:
            html = generate_product_page(product, detail_tmpl)
        except Exception as e:
            log.error(f"Fehler beim Generieren von '{filename}': {e}")
            failed += 1
            continue

        if dry_run := args.dry_run:
            log.info(f"[DRY-RUN] Würde schreiben: {filename}  ({len(html):,} Zeichen)")
        else:
            if out_path.exists():
                _backup_file(out_path)
            out_path.write_text(html, encoding="utf-8")
            log.info(f"Erstellt: {filename}")
        generated += 1

    # ── Listing-Seite aktualisieren ────────────────────────────────────────────
    if not args.slug:  # Nur beim Vollbuild
        update_listing_page(
            valid_products,
            card_tmpl,
            dry_run=args.dry_run,
        )

    # ── Zusammenfassung ────────────────────────────────────────────────────────
    log.info("─" * 60)
    log.info(f"Generiert: {generated}  |  Fehler: {failed}  |  Übersprungen: {skipped}")
    if args.dry_run:
        log.info("DRY-RUN: Keine Datei wurde tatsächlich geschrieben.")
    log.info("Fertig!")

if __name__ == "__main__":
    main()
