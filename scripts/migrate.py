import os
import csv
import json
from pathlib import Path

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent
CSV_PATH = BASE_DIR / 'data' / 'products_export.csv'
JSON_PATH = BASE_DIR / 'data' / 'database.json'

def migrate():
    if not CSV_PATH.exists():
        print(f"Keine Datei {CSV_PATH} gefunden.")
        return
        
    products = []
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            status_val = row.get('status', row.get('status,', '')).strip()
            
            # Arrays
            bullets = [b.strip() for b in row.get('bullets', '').split('|') if b.strip()]
            washing = [w.strip() for w in row.get('washingInstructions', '').split('|') if w.strip()]
            colors = [c.strip() for c in row.get('colors', '').split('|') if c.strip()]
            
            p = {
                'id': row.get('id', '').strip(),
                'name': row.get('name', '').strip(),
                'price': float(row.get('price', 0)) if row.get('price') else 0.0,
                'type': row.get('type', '').strip(),
                'nation': row.get('nation', '').strip(),
                'image': row.get('image', '').strip(),
                'image2': row.get('image2', '').strip(),
                'image3': row.get('image3', '').strip(),
                'image4': row.get('image4', '').strip(),
                'image5': row.get('image5', '').strip(),
                'shortDescription': row.get('shortDescription', '').strip(),
                'description': row.get('description', '').strip(),
                'bullets': bullets,
                'washingInstructions': washing,
                'colors': colors,
                'sizeNote': row.get('sizeNote', '').strip(),
                'category': row.get('category', '').strip(),
                'keywords': row.get('keywords', '').strip(),
                'status': status_val
            }
            products.append(p)

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=4, ensure_ascii=False)
    print(f"Erfolgreich {len(products)} Produkte nach {JSON_PATH} migriert!")

if __name__ == '__main__':
    migrate()
