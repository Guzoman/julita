import os
import re
import pandas as pd
import json


def _normalize_text_simple(s: str) -> str:
    """Minúsculas + sin acentos para comparar nombres de columnas."""
    if s is None:
        return ''
    s = str(s).lower()
    replacements = str.maketrans('áéíóúñüÁÉÍÓÚÑÜ', 'aeiounuAEIOUNU')
    return s.translate(replacements)


def _first_match(cols, candidates):
    """Devuelve el primer nombre real de columna cuyo normalizado contiene alguno de candidates."""
    norm_map = {c: _normalize_text_simple(c) for c in cols}
    for real, norm in norm_map.items():
        for cand in candidates:
            if cand in norm:
                return real
    return None


def _read_wc_csv(preferred_path=None):
    """Lee el CSV de WordPress/WooCommerce desde la ruta indicada o detecta automáticamente.
    Retorna (df, source_path). Intenta UTF-8 y cae a latin-1 si es necesario."""
    # 1) Si se entrega ruta y existe, usarla
    if preferred_path and os.path.exists(preferred_path):
        paths = [preferred_path]
    else:
        paths = []
        # 2) Intentar archivo clásico
        if os.path.exists('BBDD productos julia.csv'):
            paths.append('BBDD productos julia.csv')
        # 3) Buscar "export full.csv" en el árbol
        for root, _, files in os.walk('.'):
            for name in files:
                if name.lower() == 'export full.csv':
                    paths.append(os.path.join(root, name))
                    break
            if paths:
                break

    if not paths:
        raise FileNotFoundError('No se encontró un CSV de WordPress (BBDD productos julia.csv o export full.csv).')

    last_err = None
    for path in paths:
        for enc in ('utf-8', 'latin-1'):
            try:
                df = pd.read_csv(path, encoding=enc)
                return df, path
            except Exception as e:
                last_err = e
                continue
    raise last_err if last_err else RuntimeError('No se pudo leer el CSV de WordPress.')


def extract_images_from_wordpress(source_path=None):
    """Extraer URLs de imágenes desde un CSV de WordPress/WooCommerce.
    Soporta tanto el CSV antiguo (BBDD productos julia.csv) como el export oficial (export full.csv)."""

    print('Extrayendo URLs de imágenes de WordPress...')

    # Leer CSV (autodetección de ruta)
    df, used_path = _read_wc_csv(source_path)
    print(f'Fuente: {used_path}')

    # Detectar columnas relevantes (tolerante a acentos y variantes)
    cols = list(df.columns)
    sku_col = _first_match(cols, ['_sku', 'sku'])
    title_col = _first_match(cols, ['post_title', 'nombre', 'name'])
    image_col = _first_match(cols, ['image', 'imagen', 'imagenes'])
    gallery_col = _first_match(cols, ['image_gallery', 'galeria'])

    if not sku_col:
        raise KeyError('No se encontró columna de SKU en el CSV.')
    if not title_col:
        title_col = sku_col  # fallback

    # Mapeo de productos con imágenes
    product_images = {}

    url_regex = re.compile(r'https?://[^\s\|\"\<\>]+\.(?:jpg|jpeg|png|gif|webp)', re.IGNORECASE)

    def add_unique(seq, item, seen):
        if item not in seen:
            seq.append(item)
            seen.add(item)

    for _, row in df.iterrows():
        sku_val = row.get(sku_col)
        title_val = row.get(title_col)
        if pd.isna(sku_val) or pd.isna(title_val):
            continue

        sku = str(sku_val).strip()
        title = str(title_val).strip()

        seen = set()
        images = []

        # Columna principal de imagen (puede contener múltiples separadas por coma o '|')
        if image_col:
            main_val = row.get(image_col, '')
            if pd.notna(main_val):
                text = str(main_val)
                for part in re.split(r'[|,\n]', text):
                    part = part.strip()
                    if not part:
                        continue
                    if part.startswith('http') and url_regex.search(part):
                        add_unique(images, part, seen)
                for m in url_regex.findall(text):
                    add_unique(images, m, seen)

        # Galería (si existe)
        if gallery_col:
            gallery_val = row.get(gallery_col, '')
            if pd.notna(gallery_val):
                text = str(gallery_val)
                for part in re.split(r'[|,\n]', text):
                    part = part.strip()
                    if part and part.startswith('http') and url_regex.search(part):
                        add_unique(images, part, seen)
                for m in url_regex.findall(text):
                    add_unique(images, m, seen)

        if images:
            product_images[sku] = {
                'title': title,
                'images': images,
                'thumbnail': images[0] if images else None
            }

    print(f'Productos con imágenes encontrados: {len(product_images)}')

    # Mostrar algunos ejemplos
    print('\n=== EJEMPLOS DE IMÁGENES ===')
    for i, (sku, data) in enumerate(list(product_images.items())[:5]):
        print(f'\nSKU: {sku}')
        print(f'Título: {data["title"]}')
        print(f'Imágenes ({len(data["images"])}):')
        for img in data['images'][:3]:  # Solo primeras 3
            print(f'  - {img}')
        if len(data['images']) > 3:
            print(f'  ... y {len(data["images"]) - 3} más')

    # Guardar mapping
    with open('wordpress_images_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(product_images, f, indent=2, ensure_ascii=False)

    return product_images


def add_images_to_medusa_data():
    """Agregar imágenes a los datos procesados de Medusa"""

    # Cargar datos existentes
    with open('processed_products.json', 'r', encoding='utf-8') as f:
        products = json.load(f)

    # Cargar mapping de imágenes
    try:
        with open('wordpress_images_mapping.json', 'r', encoding='utf-8') as f:
            image_mapping = json.load(f)
    except FileNotFoundError:
        print('Ejecutando extracción de imágenes primero...')
        image_mapping = extract_images_from_wordpress()

    # Agregar imágenes a productos
    updated_count = 0

    for product in products:
        product['images'] = []
        product['thumbnail'] = None

        # Buscar imágenes por SKUs de variantes
        for variant in product['variants']:
            sku = variant['sku']

            if sku in image_mapping:
                img_data = image_mapping[sku]
                if img_data['images']:
                    product['images'].extend(img_data['images'])

                    # Usar primera imagen como thumbnail si no tiene
                    if not product['thumbnail']:
                        product['thumbnail'] = img_data['images'][0]

        # Remover duplicados
        if product['images']:
            product['images'] = list(set(product['images']))
            updated_count += 1

    # Guardar productos actualizados
    with open('processed_products_with_images.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    print(f'\nProductos actualizados con imágenes: {updated_count}/{len(products)}')

    # Estadísticas
    with_images = sum(1 for p in products if p['images'])
    without_images = len(products) - with_images

    print(f'Con imágenes: {with_images}')
    print(f'Sin imágenes: {without_images}')

    return products


if __name__ == '__main__':
    # Extraer imágenes y actualizar productos
    products_with_images = add_images_to_medusa_data()

    print('\nArchivos generados:')
    print('- wordpress_images_mapping.json')
    print('- processed_products_with_images.json')

