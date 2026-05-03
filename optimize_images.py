# -*- coding: utf-8 -*-
"""
optimize_images.py
==================
Image optimization script for the FUSSI / World Cup Shop project.

What it does:
  1. Scans the /images/ folder (recursively) for .jpg, .jpeg, .png files
  2. Converts each to WebP at quality=85
  3. Resizes any image wider than MAX_WIDTH=2000px (maintains aspect ratio)
  4. Creates output in images/webp/ (mirrors sub-folder structure)
  5. Renames Gemini_Generated_Image_* files to clean SEO slugs
  6. Saves a rename_map.json so patch_html_images.py can update HTML references

Requirements:  pip install Pillow
Usage:         python optimize_images.py
"""

import os
import sys
import json
import re
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
IMAGES_DIR    = Path("images")          # root images folder
WEBP_OUT_DIR  = IMAGES_DIR / "webp"    # output folder for WebP files
MAX_WIDTH     = 2000                    # max width in pixels (for Retina 2x)
WEBP_QUALITY  = 85                     # WebP quality (0-100)
RENAME_MAP_FILE = Path("rename_map.json")  # persisted slug rename map

SCAN_EXTENSIONS = {".jpg", ".jpeg", ".png"}

# Folders/files to skip
SKIP_DIRS = {"webp", "icons"}   # don't re-process our output or icon sprites

# ---------------------------------------------------------------------------
# PILLOW CHECK
# ---------------------------------------------------------------------------
try:
    from PIL import Image, UnidentifiedImageError
except ImportError:
    print("ERROR: Pillow is not installed.")
    print("Run:  pip install Pillow")
    sys.exit(1)

# ---------------------------------------------------------------------------
# SLUG GENERATOR
# ---------------------------------------------------------------------------
_slug_counters: dict[str, int] = {}

def make_slug(original_stem: str, parent_folder: str) -> str:
    """
    Turn 'Gemini_Generated_Image_3vkdv03vkdv03vkd' → 'product-krd-001'
    Numbered per parent folder so slugs are unique within their directory.
    Non-Gemini files keep their existing name.
    """
    if not original_stem.lower().startswith("gemini_generated_image"):
        return original_stem.lower().replace(" ", "-")

    # Use the parent folder name as the category (e.g., 'krd', 'general')
    folder_key = parent_folder.lower().replace(" ", "-") or "product"
    _slug_counters[folder_key] = _slug_counters.get(folder_key, 0) + 1
    return f"product-{folder_key}-{_slug_counters[folder_key]:03d}"


# ---------------------------------------------------------------------------
# MAIN CONVERSION
# ---------------------------------------------------------------------------
def collect_images(root: Path) -> list[Path]:
    results = []
    for p in root.rglob("*"):
        if p.suffix.lower() not in SCAN_EXTENSIONS:
            continue
        # Skip any path that already lives inside our output dir
        if WEBP_OUT_DIR in p.parents:
            continue
        # Skip icon/webp subdirs
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        results.append(p)
    return sorted(results)


def convert_image(src: Path, dst: Path, rename_map: dict) -> dict:
    """Convert one image → WebP. Returns a stats dict."""
    try:
        with Image.open(src) as img:
            # Convert palette / RGBA → RGB for JPEG compat, keep alpha for PNG
            if img.mode in ("P", "RGBA") and src.suffix.lower() == ".png":
                img = img.convert("RGBA")
            elif img.mode not in ("RGB", "RGBA", "L"):
                img = img.convert("RGB")

            original_size = (img.width, img.height)

            # Resize if too wide
            if img.width > MAX_WIDTH:
                ratio = MAX_WIDTH / img.width
                new_h = int(img.height * ratio)
                img = img.resize((MAX_WIDTH, new_h), Image.LANCZOS)

            dst.parent.mkdir(parents=True, exist_ok=True)
            img.save(dst, "WEBP", quality=WEBP_QUALITY, method=6)

        src_bytes = src.stat().st_size
        dst_bytes = dst.stat().st_size
        saving_pct = round((1 - dst_bytes / src_bytes) * 100, 1) if src_bytes else 0

        # Build rename map entry  (relative path from project root → webp relative path)
        rel_src = str(src).replace("\\", "/")
        rel_dst = str(dst).replace("\\", "/")
        rename_map[rel_src] = rel_dst

        return {
            "ok": True,
            "src": str(src),
            "dst": str(dst),
            "original_size": original_size,
            "final_size": (img.width if img.width <= MAX_WIDTH else MAX_WIDTH, img.height),
            "src_bytes": src_bytes,
            "dst_bytes": dst_bytes,
            "saving_pct": saving_pct,
        }

    except UnidentifiedImageError:
        return {"ok": False, "src": str(src), "error": "Cannot identify image file"}
    except Exception as exc:
        return {"ok": False, "src": str(src), "error": str(exc)}


def run():
    t0 = time.time()
    print("=" * 65)
    print("  FUSSI Image Optimizer")
    print(f"  Source : {IMAGES_DIR.resolve()}")
    print(f"  Output : {WEBP_OUT_DIR.resolve()}")
    print(f"  Quality: {WEBP_QUALITY}  |  Max width: {MAX_WIDTH}px")
    print("=" * 65)

    images = collect_images(IMAGES_DIR)
    if not images:
        print("No images found. Exiting.")
        return

    print(f"\nFound {len(images)} image(s) to process...\n")

    rename_map: dict[str, str] = {}
    ok_count = 0
    fail_count = 0
    total_src_bytes = 0
    total_dst_bytes = 0

    for src in images:
        # Compute destination path (mirror structure under webp/)
        rel = src.relative_to(IMAGES_DIR)
        parent_folder = rel.parent.name  # e.g. 'krd', 'general', ''

        # Determine slug / output stem
        new_stem = make_slug(src.stem, parent_folder)
        dst = WEBP_OUT_DIR / rel.parent / (new_stem + ".webp")

        result = convert_image(src, dst, rename_map)

        if result["ok"]:
            ok_count += 1
            total_src_bytes += result["src_bytes"]
            total_dst_bytes += result["dst_bytes"]
            saving_label = f"  {result['saving_pct']:+.1f}% size"
            if result["saving_pct"] < 0:
                saving_label = f"  {abs(result['saving_pct']):.1f}% LARGER (source was already small)"
            print(f"  [OK]  {src} -> {dst}{saving_label}")
        else:
            fail_count += 1
            print(f"  [ERR] {src}  ERROR: {result['error']}")

    # Save rename map
    with open(RENAME_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(rename_map, f, indent=2)

    elapsed = round(time.time() - t0, 1)
    total_saved = total_src_bytes - total_dst_bytes
    overall_pct = round((1 - total_dst_bytes / total_src_bytes) * 100, 1) if total_src_bytes else 0

    print("\n" + "=" * 65)
    print(f"  Done in {elapsed}s")
    print(f"  Converted : {ok_count} files  |  Failed: {fail_count}")
    print(f"  Original  : {total_src_bytes / 1024:.1f} KB")
    print(f"  Output    : {total_dst_bytes / 1024:.1f} KB")
    print(f"  Saved     : {total_saved / 1024:.1f} KB  ({overall_pct}% smaller)")
    print(f"  Rename map: {RENAME_MAP_FILE}")
    print("=" * 65)
    print("\nNext step: run  python patch_html_images.py")


if __name__ == "__main__":
    run()
