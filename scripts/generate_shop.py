import os
import csv
import json
import re
import urllib.request
from pathlib import Path

# Paths relative to the project root (where this script should be run from)
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent
CSV_PATH = BASE_DIR / 'data' / 'products_export.csv'
CONFIG_PATH = BASE_DIR / 'data' / 'config.json'
JS_PATH = BASE_DIR / 'data' / 'products.js'
TEMPLATE_DIR = BASE_DIR / 'templates'
TEMPLATE_HTML = TEMPLATE_DIR / 'product-detail-template.html'
GENERATED_DIR = BASE_DIR / 'generated'
IMAGES_NATIONS_DIR = BASE_DIR / 'images'
# Ensure directories exist
TEMPLATE_DIR.mkdir(exist_ok=True)
GENERATED_DIR.mkdir(exist_ok=True)

JSON_PATH = BASE_DIR / 'data' / 'database.json'

def read_products():
    """Reads the products from the JSON database exported by the Admin Dashboard."""
    if not JSON_PATH.exists():
        print(f"Error: Could not find {JSON_PATH}. Please add products via the Admin Dashboard.")
        return []

    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            raw_products = json.load(f)
    except Exception as e:
        print(f"Fehler beim Lesen der database.json: {e}")
        return []
        
    products = []
    for row in raw_products:
        status_val = row.get('status', '').strip()
        
        if status_val.lower() != 'active':
            continue # Skip non-active products
            
        product_dict = {
            'id': row.get('id', '').strip(),
            'name': row.get('name', '').strip(),
            'price': float(row.get('price', 0)) if row.get('price') else 0.0,
            'priority': int(row.get('priority', 0)) if row.get('priority') else 0,
            'type': row.get('type', '').strip(),
            'nation': row.get('nation', '').strip(),
            'image': row.get('image', '').strip(),
            'category': row.get('category', '').strip(),
            'shortDescription': row.get('shortDescription', '').strip(),
            'description': row.get('description', '').strip(),
            'sizeNote': row.get('sizeNote', '').strip(),
            'keywords': row.get('keywords', '').strip(),
            'related_products': row.get('related_products', '').strip()
        }
        
        # Optional images
        for opt_img in ['image2', 'image3', 'image4', 'image5']:
            val = row.get(opt_img)
            if val and isinstance(val, str) and val.strip():
                product_dict[opt_img] = val.strip()
        
        # Arrays
        if row.get('bullets'): product_dict['bullets'] = row['bullets']
        if row.get('washingInstructions'): product_dict['washingInstructions'] = row['washingInstructions']
        if row.get('colors'): product_dict['colors'] = row['colors']
        
        # This is the url we will inject into products.js so index/nation pages link to the generated static page!
        # This is the url we will inject into products.js so index/nation pages link to the generated static page!
        product_dict['url'] = f"product-{product_dict['id']}.html"
        
        # Ensure images dir for nation exists
        if product_dict['nation']:
            (IMAGES_NATIONS_DIR / str(product_dict['nation'])).mkdir(exist_ok=True)
        
        products.append(product_dict)
    
    # Sort by priority (descending), then by name (ascending)
    products.sort(key=lambda x: (-x.get('priority', 0), x.get('name', '')))
    
    return products

import random

def get_related_products_html(current_product, all_products):
    """Generates the HTML for up to 4 related products. Prioritizes explicit IDs."""
    related_ids_str = current_product.get('related_products', '')
    explicit_ids = [rid.strip() for rid in related_ids_str.split(',') if rid.strip()]
    
    related_list = []
    seen_ids = {current_product.get('id', '')}
    
    # 1. First, try to find the explicitly requested IDs
    for rid in explicit_ids:
        found = next((p for p in all_products if p.get('id') == rid), None)
        if found and found.get('id') not in seen_ids:
            related_list.append(found)
            seen_ids.add(found.get('id'))
    
    # 2. Fill up to 4 using products from same nation
    if len(related_list) < 4:
        current_nation = current_product.get('nation', '')
        nation_mates = [p for p in all_products if p.get('nation') == current_nation and p.get('id') not in seen_ids]
        random.shuffle(nation_mates)
        
        needed = 4 - len(related_list)
        batch = nation_mates[:needed]
        related_list.extend(batch)
        for p in batch:
            seen_ids.add(p.get('id'))

    # 3. If still not 4, fill up with any other products
    if len(related_list) < 4:
        others = [p for p in all_products if p.get('id') not in seen_ids]
        random.shuffle(others)
        needed = 4 - len(related_list)
        batch = others[:needed]
        related_list.extend(batch)

    if not related_list:
        return ""
        
    html = ""
    for p in related_list:
        name = p.get('name', '')
        price = f"{p.get('price', 0.0):.2f}"
        
        image = p.get('image', '')
        image = image.replace('\\', '/')
        if 'cozastore-master/' in image:
            image = image.split('cozastore-master/')[-1]
        elif 'images/' in image and not image.startswith('images/'):
            image = image[image.find('images/'):]
        if image.startswith('/'):
            image = image[1:]
            
        url = f"generated/product-{p.get('id', '')}.html"
        
        html += f"""
        <!-- item -->
        <div class="item-slick2 p-l-15 p-r-15 p-t-15 p-b-15">
            <div class="block2">
                <div class="block2-pic hov-img0 p-b-15" style="border-radius:15px;overflow:hidden;background:#f8f8f8;">
                    <img src="{image}" alt="{name}">
                    <a href="{url}" class="block2-btn flex-c-m stext-103 cl2 size-102 bg0 bor2 hov-btn1 p-lr-15 trans-04">Ansehen</a>
                </div>
                <div class="block2-txt flex-w flex-t p-t-14">
                    <div class="block2-txt-child1 flex-col-l">
                        <a href="{url}" class="stext-104 cl4 hov-cl1 trans-04 js-name-b2 p-b-6" style="font-family:Poppins-Bold;font-size:16px;">
                            {name}
                        </a>
                        <span class="stext-105 cl3" style="color:#e50914;font-family:Poppins-Bold;">
                            €{price}
                        </span>
                    </div>
                </div>
            </div>
        </div>
        """
    return html

def generate_static_html(product, all_products, template_content):
    """Generates the static HTML string for the product."""
    content = template_content
    

    # Simple text replacements
    content = content.replace('%%PRODUCT_TITLE%%', f"{product.get('name', '')} | WORLD CUP SHOP")
    content = content.replace('%%PRODUCT_NAME%%', product.get('name', ''))
    content = content.replace('%%PRODUCT_META_DESC%%', product.get('shortDescription', ''))
    
    # Clean up image paths if the user copy-pasted absolute Windows paths
    def clean_img_path(p):
        if not p:
            return ''
        p = p.replace('\\', '/')
        if 'cozastore-master/' in p:
            p = p.split('cozastore-master/')[-1]
        elif 'images/' in p and not p.startswith('images/'):
             p = p[p.find('images/'):]
        if p.startswith('/'):
            p = p[1:]
        return p

    image1 = clean_img_path(product.get('image', ''))
    image2 = clean_img_path(product.get('image2', image1))
    image3 = clean_img_path(product.get('image3', image2))
    
    # Save the cleaned paths back onto the product object so they export correctly to products.js!
    product['image'] = image1
    product['image2'] = image2
    product['image3'] = image3
    
    content = content.replace('%%PRODUCT_OG_IMAGE%%', image1)
    content = content.replace('%%PRODUCT_IMAGE1%%', image1)
    content = content.replace('%%PRODUCT_IMAGE2%%', image2)
    content = content.replace('%%PRODUCT_IMAGE3%%', image3)
    
    content = content.replace('%%PRODUCT_PRICE%%', f"{product.get('price', 0.0):.2f}")
    content = content.replace('%%PRODUCT_SKU%%', product.get('id', '').upper())
    content = content.replace('%%PRODUCT_CATEGORY%%', product.get('category', ''))
    content = content.replace('%%PRODUCT_SHORT_DESC%%', product.get('shortDescription', ''))
    content = content.replace('%%PRODUCT_LONG_DESC%%', product.get('description', ''))
    
    loyalty_pts = str(int(product.get('price', 0.0) * 10))
    content = content.replace('%%PRODUCT_LOYALTY_POINTS%%', loyalty_pts)
    
    # Colors
    colors = product.get('colors', [])
    content = content.replace('%%PRODUCT_COLORS%%', ', '.join(colors))
    
    color_map = { 'Schwarz': '#111111', 'Weiß': '#f5f5f5', 'Rot': '#e50914', 'Blau': '#1a5fa8', 'Olive': '#556b2f', 'Sand': '#c2b280', 'Hellblau': '#87ceeb', 'Pink': '#ffc0cb', 'Gelb': '#ffdf00', 'Grün': '#009b3a' }
    swatches_html = ""
    for idx, c in enumerate(colors):
        bg = color_map.get(c, '#666666')
        active = 'active' if idx == 0 else ''
        swatches_html += f'<button type="button" class="color-swatch {active}" data-color="{c}" style="--swatch-color:{bg};" title="{c}"></button>\n'
    content = content.replace('%%PRODUCT_COLOR_SWATCHES%%', swatches_html)
    
    # Bullets
    bullets = product.get('bullets', [])
    bullets_html = "\n".join([f"<li>{b}</li>" for b in bullets])
    content = content.replace('%%PRODUCT_BULLETS%%', bullets_html)
    
    # Washing
    washing = product.get('washingInstructions', [])
    wash_html = "\n".join([f"<li>{w}</li>" for w in washing])
    content = content.replace('%%PRODUCT_WASHING%%', wash_html)
    
    # Stock
    stock = product.get('stock', {"S": 10, "M": 10, "L": 10, "XL": 10, "XXL": 10})
    content = content.replace('%%PRODUCT_STOCK_JSON%%', json.dumps(stock))
    
    related_html = get_related_products_html(product, all_products)
    content = content.replace('%%RELATED_PRODUCTS%%', related_html)
    
    return content

def update_products_js(products):
    """Appends/updates the dynamically loaded products.js file with new products."""
    if not JS_PATH.exists():
        print(f"Error: Could not find {JS_PATH}")
        return

    with open(JS_PATH, 'r', encoding='utf-8') as f:
        js_content = f.read()

    start_marker = '// --- AUTO GENERATED FROM CSV START ---'
    end_marker = '// --- AUTO GENERATED FROM CSV END ---'
    
    json_array = json.dumps(products, indent=4, ensure_ascii=False)
    injection_block = f"{start_marker}\nconst csvProducts = {json_array};\ncsvProducts.forEach(p => products.push(p));\n{end_marker}\n"

    if start_marker in js_content and end_marker in js_content:
        parts = js_content.split(start_marker)
        before = parts[0]
        after = parts[1].split(end_marker, 1)[1]
        new_js = before + injection_block + after
    else:
        new_js = js_content.rstrip() + "\n\n" + injection_block
        
    with open(JS_PATH, 'w', encoding='utf-8') as f:
        f.write(new_js)
    print(f"Updated {JS_PATH.name} automatically with {len(products)} products.")


def main():
    print("=== Static Shop Generator ===")
    
    if not TEMPLATE_HTML.exists():
        print(f"Error: Cannot find template {TEMPLATE_HTML}")
        return
        
    with open(TEMPLATE_HTML, 'r', encoding='utf-8') as f:
        template_content = f.read()
        
    products = read_products()
    if not products:
        print("No active products found in CSV.")
        return
        
    generated_count = 0
    for product in products:
        if not product.get('id'):
            print("Skipping product with missing id/slug.")
            continue
        html_output = generate_static_html(product, products, template_content)
        outfile = BASE_DIR / f"product-{product['id']}.html"
        with open(outfile, 'w', encoding='utf-8') as f:
            f.write(html_output)
        print(f"Generated: {outfile.name}")
        generated_count += 1
        
    print(f"Successfully generated {generated_count} HTML files in /generated/")
    update_products_js(products)
    print("Done! You can verify changes by opening the shop locally.")

if __name__ == '__main__':
    main()

