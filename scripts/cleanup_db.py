import json
import os

db_path = 'data/database.json'

with open(db_path, 'r', encoding='utf-8') as f:
    products = json.load(f)

def clean_path(p):
    if not p: return ""
    p = p.replace('\\', '/')
    if 'cozastore-master/' in p:
        p = p.split('cozastore-master/')[-1]
    if p.startswith('/'):
        p = p[1:]
    return p

for p in products:
    p['image'] = clean_path(p.get('image', ''))
    p['image2'] = clean_path(p.get('image2', ''))
    p['image3'] = clean_path(p.get('image3', ''))
    p['image4'] = clean_path(p.get('image4', ''))
    p['image5'] = clean_path(p.get('image5', ''))

with open(db_path, 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=4, ensure_ascii=False)

print("Database cleaned and normalized.")

# Rename Brasilien folder to br if it exists
if os.path.exists('images/Brasilien') and not os.path.exists('images/br'):
    os.rename('images/Brasilien', 'images/br')
    print("Renamed images/Brasilien to images/br")
elif os.path.exists('images/Brasilien') and os.path.exists('images/br'):
    print("Warning: Both images/Brasilien and images/br exist. Please merge manually.")
