import pandas as pd
import re

df = pd.read_csv('BBDD productos julia.csv', encoding='utf-8')

print('=== BÚSQUEDA DE IMÁGENES REALES ===')

# Buscar una fila específica primero
parka = df[df['post_title'].str.contains('Parka Los Reyes', na=False)].iloc[0]

print(f'ANÁLISIS: {parka.get("post_title", "N/A")} (SKU: {parka.get("_sku", "N/A")})')
print()

# Revisar cada columna de esta fila
for col in df.columns:
    value = str(parka.get(col, ''))
    # Buscar extensiones de imagen
    if any(ext in value.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
        print(f'COLUMNA: {col}')
        # Extraer URLs completas
        image_urls = re.findall(r'https://[^\s\|\"\<\>]+\.(jpg|jpeg|png|gif|webp)', value, re.IGNORECASE)
        if image_urls:
            print('URLs ENCONTRADAS:')
            for url in image_urls[:5]:  # Primeras 5
                print(f'  - {url}')
        else:
            # Mostrar contenido que contiene extensiones
            lines = value.split('\n')
            for line in lines[:3]:
                if any(ext in line.lower() for ext in ['.jpg', '.jpeg', '.png']):
                    print(f'  CONTENIDO: {line[:100]}...')
        print()

# Ahora búsqueda global más simple
print('\n=== PRODUCTOS CON IMÁGENES REALES (GLOBAL) ===')
products_with_images = []

for i, row in df.iterrows():
    for col in df.columns:
        value = str(row.get(col, ''))
        # Buscar URLs completas de imágenes
        image_urls = re.findall(r'https://[^\s\|\"\<\>]+\.(jpg|jpeg|png|gif|webp)', value, re.IGNORECASE)
        if image_urls:
            products_with_images.append({
                'title': row.get('post_title', 'N/A'),
                'sku': row.get('_sku', 'N/A'),
                'column': col,
                'images': image_urls
            })
            break  # Solo contar una vez por producto

print(f'PRODUCTOS CON IMÁGENES ENCONTRADOS: {len(products_with_images)}')

for product in products_with_images[:10]:
    print(f'\n{product["title"]} (SKU: {product["sku"]})')
    print(f'  Columna: {product["column"]}')
    print(f'  Imágenes: {len(product["images"])}')
    for img in product["images"][:2]:
        print(f'    - {img}')