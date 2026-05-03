# -*- coding: utf-8 -*-
"""
patch_html_images.py
====================
Bulk-patches every HTML file in the project to:

  1. Add  loading="lazy"   to every <img> tag that lacks it
  2. Add  decoding="async" to every <img> tag that lacks it
  3. Add  srcset="<webp-path> 1x, <orig-path> 2x"  for product images
     (detected by checking if a WebP version exists in images/webp/)

Usage:
    python patch_html_images.py [--dry-run]

Options:
    --dry-run   Print what would change without modifying files

Run AFTER optimize_images.py so that images/webp/ already exists.
"""

import os
import re
import sys
import json
import glob
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(".")
IMAGES_DIR   = Path("images")
WEBP_DIR     = IMAGES_DIR / "webp"
RENAME_MAP_FILE = Path("rename_map.json")

# HTML files to patch (all .html in project root and sub-dirs, excluding node_modules / vendor)
SKIP_DIRS = {"node_modules", ".git", "vendor", "recovery", "recovery_backup_20260317_2221", "safe_restore"}

DRY_RUN = "--dry-run" in sys.argv

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def should_skip(path: Path) -> bool:
    for part in path.parts:
        if part in SKIP_DIRS:
            return True
    return False


def collect_html_files() -> list[Path]:
    files = []
    for p in PROJECT_ROOT.rglob("*.html"):
        if not should_skip(p):
            files.append(p)
    return sorted(files)


def load_rename_map() -> dict[str, str]:
    if RENAME_MAP_FILE.exists():
        with open(RENAME_MAP_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def find_webp_path(src_attr: str) -> str | None:
    """
    Given an img src like 'images/krd/1.png', return the webp path
    'images/webp/krd/1.webp' if the file actually exists on disk.
    Also handles renamed Gemini files by checking rename_map.
    """
    if not src_attr:
        return None
    # Normalise slashes
    src_norm = src_attr.replace("\\", "/").lstrip("/")

    src_path = Path(src_norm)
    # Only handle images that live under images/
    if src_path.parts and src_path.parts[0] != "images":
        return None

    # Compute expected webp path (same relative sub-path but under images/webp/)
    rel = src_path.relative_to("images")
    webp_path = WEBP_DIR / rel.parent / (rel.stem + ".webp")

    if webp_path.exists():
        return str(webp_path).replace("\\", "/")

    # Also check if a slug-renamed version exists
    for p in (WEBP_DIR / rel.parent).glob("*.webp"):
        # crude match: if the original stem is contained in the slug
        if rel.stem.lower()[:8] in p.stem.lower():
            return str(p).replace("\\", "/")

    return None


# ---------------------------------------------------------------------------
# IMG TAG PATCHER
# ---------------------------------------------------------------------------

# Matches a complete <img ...> tag (non-greedy, handles multi-line)
IMG_TAG_RE = re.compile(r'<img\b([^>]*?)(/?>)', re.DOTALL | re.IGNORECASE)

def patch_img_tag(tag_attrs: str, close: str) -> str:
    """Given the attribute string of one <img> tag, add missing attrs."""
    attrs = tag_attrs  # we'll modify this string

    # 1. Extract existing src value
    src_match = re.search(r'\bsrc\s*=\s*["\']([^"\']*)["\']', attrs, re.IGNORECASE)
    src_val = src_match.group(1) if src_match else ""

    # 2. Add loading="lazy" if missing
    if not re.search(r'\bloading\s*=', attrs, re.IGNORECASE):
        attrs = attrs.rstrip() + ' loading="lazy"'

    # 3. Add decoding="async" if missing
    if not re.search(r'\bdecoding\s*=', attrs, re.IGNORECASE):
        attrs = attrs.rstrip() + ' decoding="async"'

    # 4. Add srcset if:
    #    - src points inside images/
    #    - no srcset already present
    #    - a WebP version exists
    if src_val and not re.search(r'\bsrcset\s*=', attrs, re.IGNORECASE):
        webp_path = find_webp_path(src_val)
        if webp_path:
            srcset_val = f'{webp_path} 1x, {src_val} 2x'
            attrs = attrs.rstrip() + f' srcset="{srcset_val}"'

    return f'<img{attrs}{close}'


def patch_html(content: str) -> tuple[str, int]:
    """Patch all img tags in an HTML string. Returns (new_content, change_count)."""
    changes = 0

    def replacer(m: re.Match) -> str:
        nonlocal changes
        original = m.group(0)
        patched  = patch_img_tag(m.group(1), m.group(2))
        if patched != original:
            changes += 1
        return patched

    new_content = IMG_TAG_RE.sub(replacer, content)
    return new_content, changes


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def run():
    print("=" * 65)
    print("  FUSSI HTML Image Patcher")
    print(f"  Mode: {'DRY RUN (no files written)' if DRY_RUN else 'LIVE (files will be modified)'}")
    print("=" * 65)

    html_files = collect_html_files()
    print(f"\nFound {len(html_files)} HTML file(s) to patch...\n")

    total_files_changed = 0
    total_tags_changed  = 0

    for html_path in html_files:
        try:
            original = html_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"  SKIP (read error): {html_path}  — {e}")
            continue

        patched, n_changes = patch_html(original)

        if n_changes == 0:
            continue  # nothing to do

        total_files_changed += 1
        total_tags_changed  += n_changes

        print(f"  [OK]  {html_path}  ({n_changes} img tag(s) updated)")

        if not DRY_RUN:
            try:
                html_path.write_text(patched, encoding="utf-8")
            except Exception as e:
                print(f"     ERROR writing: {e}")

    print("\n" + "=" * 65)
    if DRY_RUN:
        print(f"  DRY RUN complete.")
    else:
        print(f"  Patching complete.")
    print(f"  Files changed : {total_files_changed}")
    print(f"  <img> tags updated: {total_tags_changed}")
    print("=" * 65)


if __name__ == "__main__":
    run()
