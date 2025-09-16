import os
import pandas as pd
import json
import re
from difflib import SequenceMatcher
from collections import defaultdict


def normalize_text(text):
    """Normalizar texto para matching"""
    if pd.isna(text):
        return ""

    # Convertir a string y minúsculas
    text = str(text).lower().strip()

    # Remover acentos (compatibles con exportaciones con caracteres raros)
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'ü': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'Ñ': 'N', 'Ü': 'U',
        'ǭ': 'a', 'Ǹ': 'e', '��': 'i', '��': 'o', 'ǧ': 'u',
        '��': 'n', 'Ǭ': 'u'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remover tallas
    text = re.sub(r"\btalla\s+\w+", '', text)
    text = re.sub(r"\bt\.?\s*\w+", '', text)
    text = re.sub(r"\s+(xs|s|m|l|xl|xxl)\s*$", '', text)
    text = re.sub(r"\s+\d{1,2}\s*$", '', text)

    # Limpiar espacios extras
    text = re.sub(r"\s+", ' ', text).strip()

    return text


def similarity_score(text1, text2):
    """Calcular similitud entre dos textos"""
    return SequenceMatcher(None, text1, text2).ratio()


def _normalize_text_simple(s):
    if s is None:
        return ""
    s = str(s).lower()
    replacements = str.maketrans('áéíóúñüÁÉÍÓÚÑÜ', 'aeiounuAEIOUNU')
    return s.translate(replacements)


def _first_match(cols, candidates):
    norm_map = {c: _normalize_text_simple(c) for c in cols}
    for real, norm in norm_map.items():
        for cand in candidates:
            if cand in norm:
                return real
    return None


def _read_wp_any_csv(preferred_path=None):
    paths = []
    if preferred_path and os.path.exists(preferred_path):
        paths.append(preferred_path)
    if os.path.exists('BBDD productos julia.csv'):
        paths.append('BBDD productos julia.csv')
    # Buscar "export full.csv"
    for root, _, files in os.walk('.'):
        for name in files:
            if name.lower() == 'export full.csv':
                paths.append(os.path.join(root, name))
                break
        if paths:
            break

    if not paths:
        raise FileNotFoundError('No se encontró CSV de WordPress (BBDD productos julia.csv o export full.csv).')

    last_err = None
    for p in paths:
        for enc in ('utf-8', 'latin-1'):
            try:
                df = pd.read_csv(p, encoding=enc)
                return df, p
            except Exception as e:
                last_err = e
                continue
    raise last_err if last_err else RuntimeError('No se pudo leer CSV de WordPress.')


def smart_image_matching():
    """Matching inteligente entre Access y WordPress por similitud de nombres"""

    print("Iniciando matching inteligente Access <-> WordPress...")

    # Cargar datos
    access_products = pd.read_csv('access_export_productos.csv')
    wordpress_products, wp_source = _read_wp_any_csv()

    print(f"Access: {len(access_products)} productos")
    print(f"WordPress: {len(wordpress_products)} productos")
    print(f"Fuente WP: {wp_source}")

    # Procesar WordPress products con imágenes (tolerante a exportaciones)
    cols = list(wordpress_products.columns)
    sku_col = _first_match(cols, ['_sku', 'sku'])
    title_col = _first_match(cols, ['post_title', 'nombre', 'name'])
    image_col = _first_match(cols, ['image', 'imagen', 'imagenes'])
    gallery_col = _first_match(cols, ['image_gallery', 'galeria'])

    wp_with_images = []
    url_regex = re.compile(r'https?://[^\s\|\"\<\>]+\.(?:jpg|jpeg|png|gif|webp)', re.IGNORECASE)
    for _, row in wordpress_products.iterrows():
        images = []
        text_title = row.get(title_col, '') if title_col else ''

        # Columna principal
        if image_col:
            val = row.get(image_col, '')
            if pd.notna(val):
                txt = str(val)
                for part in re.split(r'[|,\n]', txt):
                    part = part.strip()
                    if part and part.startswith('http') and url_regex.search(part):
                        images.append(part)
                for m in url_regex.findall(txt):
                    images.append(m)

        # Galería
        if gallery_col:
            val = row.get(gallery_col, '')
            if pd.notna(val):
                txt = str(val)
                for part in re.split(r'[|,\n]', txt):
                    part = part.strip()
                    if part and part.startswith('http') and url_regex.search(part):
                        images.append(part)
                for m in url_regex.findall(txt):
                    images.append(m)

        if images:
            # quitar duplicados preservando orden
            seen = set()
            images_unique = []
            for im in images:
                if im not in seen:
                    images_unique.append(im)
                    seen.add(im)

            wp_with_images.append({
                'wp_title': str(text_title),
                'wp_sku': str(row.get(sku_col, '') or ''),
                'wp_category': row.get('product_cat', ''),
                'normalized_title': normalize_text(text_title),
                'images': images_unique,
                'thumbnail': images_unique[0]
            })

    print(f"WordPress con imágenes: {len(wp_with_images)} productos")

    # Matching process
    matches = []

    for _, access_row in access_products.iterrows():
        access_desc = normalize_text(access_row.get('descripcion', ''))
        access_article = normalize_text(access_row.get('articulo', ''))

        if not access_desc and not access_article:
            continue

        best_match = None
        best_score = 0

        for wp_item in wp_with_images:
            wp_title = wp_item['normalized_title']

            if not wp_title:
                continue

            # Calcular similitud con descripción
            score1 = similarity_score(access_desc, wp_title)
            # Calcular similitud con artículo
            score2 = similarity_score(access_article, wp_title)

            # Usar el mejor score
            current_score = max(score1, score2)

            # Bonificaciones por palabras clave coincidentes
            access_words = set((access_desc or '').split() + (access_article or '').split())
            wp_words = set((wp_title or '').split())
            common_words = access_words & wp_words

            if common_words:
                bonus = len(common_words) * 0.1
                current_score = min(1.0, current_score + bonus)

            if current_score > best_score and current_score > 0.3:  # Threshold mínimo
                best_score = current_score
                best_match = wp_item

        if best_match:
            matches.append({
                'access_sku': str(int(access_row['codigo'])) if pd.notna(access_row['codigo']) else '',
                'access_desc': access_row.get('descripcion', ''),
                'access_article': access_row.get('articulo', ''),
                'wp_title': best_match['wp_title'],
                'wp_sku': best_match['wp_sku'],
                'similarity_score': best_score,
                'images': best_match['images'],
                'thumbnail': best_match['thumbnail']
            })

    # Ordenar por score descendente
    matches.sort(key=lambda x: x['similarity_score'], reverse=True)

    print(f"\n=== MATCHING RESULTS ===")
    print(f"Matches encontrados: {len(matches)}")

    # Mostrar mejores matches
    print(f"\n=== TOP 10 MATCHES ===")
    for i, match in enumerate(matches[:10]):
        print(f"\n{i+1}. Score: {match['similarity_score']:.3f}")
        print(f"   Access: {match['access_desc']} (SKU: {match['access_sku']})")
        print(f"   WordPress: {match['wp_title']} (SKU: {match['wp_sku']})")
        print(f"   Images: {len(match['images'])} found")

    # Distribución de scores
    score_ranges = {
        'Excelente (>0.8)': len([m for m in matches if m['similarity_score'] > 0.8]),
        'Bueno (0.6-0.8)': len([m for m in matches if 0.6 < m['similarity_score'] <= 0.8]),
        'Regular (0.4-0.6)': len([m for m in matches if 0.4 < m['similarity_score'] <= 0.6]),
        'Bajo (<0.4)': len([m for m in matches if m['similarity_score'] <= 0.4])
    }

    print(f"\n=== DISTRIBUCIÓN DE CALIDAD ===")
    for range_name, count in score_ranges.items():
        print(f"{range_name}: {count} matches")

    # Guardar matches
    with open('image_matches.json', 'w', encoding='utf-8') as f:
        json.dump(matches, f, indent=2, ensure_ascii=False)

    return matches


def apply_matches_to_products():
    """Aplicar matches encontrados a los productos procesados"""

    # Cargar matches
    try:
        with open('image_matches.json', 'r', encoding='utf-8') as f:
            matches = json.load(f)
    except FileNotFoundError:
        print("Ejecutando matching primero...")
        matches = smart_image_matching()

    # Cargar productos procesados
    with open('processed_products.json', 'r', encoding='utf-8') as f:
        products = json.load(f)

    # Crear mapping de Access SKU -> imágenes
    sku_to_images = {}
    for match in matches:
        if match['similarity_score'] > 0.5:  # Solo matches confiables
            sku_to_images[match['access_sku']] = {
                'images': match['images'],
                'thumbnail': match['thumbnail'],
                'wp_title': match['wp_title'],
                'score': match['similarity_score']
            }

    # Aplicar imágenes a productos
    updated_count = 0

    for product in products:
        product['images'] = []
        product['thumbnail'] = None
        product['image_sources'] = []

        for variant in product['variants']:
            sku = variant['sku']

            if sku in sku_to_images:
                img_data = sku_to_images[sku]

                # Agregar imágenes
                product['images'].extend(img_data['images'])

                # Thumbnail si no tiene
                if not product['thumbnail']:
                    product['thumbnail'] = img_data['thumbnail']

                # Metadata del match
                product['image_sources'].append({
                    'sku': sku,
                    'wp_source': img_data['wp_title'],
                    'similarity': img_data['score'],
                    'image_count': len(img_data['images'])
                })

        # Limpiar duplicados
        if product['images']:
            product['images'] = list(set(product['images']))
            updated_count += 1

    # Guardar productos actualizados
    with open('processed_products_with_matched_images.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    # Estadísticas finales
    with_images = sum(1 for p in products if p['images'])
    without_images = len(products) - with_images

    print(f"\n=== RESULTADO FINAL ===")
    print(f"Productos actualizados: {updated_count}/{len(products)}")
    print(f"Con imágenes: {with_images}")
    print(f"Sin imágenes: {without_images}")

    # Top productos con más imágenes
    products_by_images = sorted(products, key=lambda x: len(x.get('images', [])), reverse=True)

    print(f"\n=== TOP PRODUCTOS CON IMÁGENES ===")
    for product in products_by_images[:5]:
        if product.get('images'):
            print(f"{product['title']}: {len(product['images'])} imágenes")

    return products


if __name__ == "__main__":
    # Ejecutar matching y aplicar a productos
    products_with_images = apply_matches_to_products()

    print("\nArchivos generados:")
    print("- image_matches.json")
    print("- processed_products_with_matched_images.json")

