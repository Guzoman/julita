import pandas as pd
import numpy as np

# Leer CSV
df = pd.read_csv('BBDD productos julia.csv', encoding='utf-8')

# Buscar productos CON galería
with_gallery = df[df['image_gallery'].notna()]
with_gallery = with_gallery[with_gallery['image_gallery'].str.strip() != '']

print(f'=== PRODUCTOS CON GALERÍA ({len(with_gallery)}) ===')

for i, (idx, row) in enumerate(with_gallery.iterrows()):
    if i >= 5: break
    print(f'\n{i+1}. Título: {row.get("post_title", "N/A")}')
    print(f'   SKU: {row.get("_sku", "N/A")}')
    print(f'   Categoría: {row.get("product_cat", "N/A")}')
    
    gallery = str(row.get('image_gallery', ''))
    if gallery and gallery != 'nan':
        images = gallery.split('|')
        print(f'   GALLERY ({len(images)} imágenes):')
        for j, img in enumerate(images[:3]):
            if img.strip():
                print(f'     - {img.strip()}')
        if len(images) > 3:
            print(f'     ... y {len(images)-3} más')

# Buscar productos canónicos con imágenes (no legacy)
print(f'\n=== PRODUCTOS CANÓNICOS CON IMÁGENES ===')
canonical_cats = ['Delantales Escolares', 'Delantales', 'Los Reyes', 'JUAN XXIII', 'CIECC', 'Solríe', 'Nahuel']

for cat in canonical_cats:
    cat_products = df[df['product_cat'].str.contains(cat, na=False)]
    cat_with_images = cat_products[cat_products['image_gallery'].notna()]
    cat_with_images = cat_with_images[cat_with_images['image_gallery'].str.strip() != '']
    
    if len(cat_with_images) > 0:
        print(f'\n{cat}: {len(cat_with_images)} productos con imágenes')
        for i, (idx, row) in enumerate(cat_with_images.iterrows()):
            if i >= 2: break
            print(f'  - {row.get("post_title", "N/A")} (SKU: {row.get("_sku", "N/A")})')