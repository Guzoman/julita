import pandas as pd
import json
import re
from collections import defaultdict

def process_access_data():
    """Transformar datos de Access a estructura moderna para Supabase/Medusa"""
    
    print("Procesando datos de Access...")
    
    # Leer datos de Access
    colegios = pd.read_csv('access_export_Colegios.csv')
    productos = pd.read_csv('access_export_productos.csv')
    articulos = pd.read_csv('access_export_Articulos.csv')
    
    print(f"Colegios: {len(colegios)} registros")
    print(f"Productos: {len(productos)} registros") 
    print(f"Articulos: {len(articulos)} registros")
    
    # 1. PROCESAR COLEGIOS
    colegios_clean = []
    for _, colegio in colegios.iterrows():
        if pd.notna(colegio['codigo']):
            colegios_clean.append({
                'id': int(colegio['codigo']),
                'name': colegio['descripcion'].strip(),
                'slug': create_slug(colegio['descripcion'])
            })
    
    # 2. PROCESAR PRODUCTOS → AGRUPAR POR ARTICULO BASE
    productos_grouped = defaultdict(list)
    
    for _, producto in productos.iterrows():
        if pd.notna(producto['codigo']):
            # Extraer talla del nombre
            talla = extract_size_from_name(producto['descripcion'])
            
            # Crear key de agrupamiento
            group_key = f"{producto.get('cod_cole', 0)}_{producto.get('articulo', 'unknown')}"
            
            variant = {
                'sku': str(int(producto['codigo'])),
                'size': talla,
                'price': int(producto['Precio_venta']) if pd.notna(producto['Precio_venta']) else 0,
                'cost_price': int(producto['precio_costo']) if pd.notna(producto['precio_costo']) else 0
            }
            
            productos_grouped[group_key].append(variant)
    
    # 3. CREAR PRODUCTOS BASE
    products_final = []
    
    for group_key, variants in productos_grouped.items():
        cod_cole, articulo = group_key.split('_', 1)
        try:
            cod_cole = int(float(cod_cole)) if cod_cole != '0' else None
        except (ValueError, TypeError):
            cod_cole = None
        
        # Buscar colegio
        colegio_name = "Genérico"
        if cod_cole:
            colegio_match = next((c for c in colegios_clean if c['id'] == cod_cole), None)
            if colegio_match:
                colegio_name = colegio_match['name']
        
        # Crear producto base
        base_name = clean_product_name(articulo)
        
        product = {
            'title': f"{base_name} - {colegio_name}" if cod_cole else base_name,
            'slug': create_slug(f"{base_name}-{colegio_name}" if cod_cole else base_name),
            'college_id': cod_cole,
            'college_name': colegio_name,
            'base_article': articulo,
            'variants': variants,
            'price_range': {
                'min': min(v['price'] for v in variants if v['price'] > 0),
                'max': max(v['price'] for v in variants if v['price'] > 0)
            } if any(v['price'] > 0 for v in variants) else {'min': 0, 'max': 0}
        }
        
        products_final.append(product)
    
    # 4. ESTADÍSTICAS
    print(f"\n=== RESUMEN PROCESAMIENTO ===")
    print(f"Colegios procesados: {len(colegios_clean)}")
    print(f"Productos base creados: {len(products_final)}")
    print(f"Total variantes: {sum(len(p['variants']) for p in products_final)}")
    
    # Por colegio
    by_college = defaultdict(int)
    for product in products_final:
        by_college[product['college_name']] += 1
    
    print("\n=== PRODUCTOS POR COLEGIO ===")
    for college, count in sorted(by_college.items()):
        print(f"{college}: {count} productos")
    
    # 5. GUARDAR RESULTADOS
    with open('processed_colegios.json', 'w', encoding='utf-8') as f:
        json.dump(colegios_clean, f, indent=2, ensure_ascii=False)
    
    with open('processed_products.json', 'w', encoding='utf-8') as f:
        json.dump(products_final, f, indent=2, ensure_ascii=False)
    
    # 6. CREAR CSVs PARA MEDUSA
    create_medusa_csvs(colegios_clean, products_final)
    
    print(f"\nPROCESAMIENTO COMPLETADO!")
    print("Archivos generados:")
    print("- processed_colegios.json")  
    print("- processed_products.json")
    print("- medusa_categories.csv")
    print("- medusa_products.csv")
    print("- medusa_variants.csv")

def extract_size_from_name(name):
    """Extraer talla del nombre del producto"""
    if pd.isna(name):
        return None
        
    # Patrones comunes de tallas
    size_patterns = [
        r'Talla\s+(\w+)',
        r'T\.?\s*(\w+)',
        r'\s+(\d{1,2})\s*$',
        r'\s+(XS|S|M|L|XL|XXL)\s*$'
    ]
    
    for pattern in size_patterns:
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    
    return None

def clean_product_name(name):
    """Limpiar nombre de producto eliminando tallas y sufijos"""
    if pd.isna(name):
        return "Producto"
        
    # Remover referencias a tallas
    name = re.sub(r'Talla\s+\w+', '', name, flags=re.IGNORECASE)
    name = re.sub(r'T\.?\s*\w+', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+\d{1,2}\s*$', '', name)
    name = re.sub(r'\s+(XS|S|M|L|XL|XXL)\s*$', '', name, flags=re.IGNORECASE)
    
    return name.strip()

def create_slug(text):
    """Crear slug URL-friendly"""
    if pd.isna(text):
        return "producto"
        
    # Convertir a minúsculas y reemplazar espacios
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')

def create_medusa_csvs(colegios, products):
    """Crear CSVs compatibles con Medusa"""
    
    # Categories (Colegios)
    categories_data = []
    for colegio in colegios:
        categories_data.append({
            'id': f"college_{colegio['id']}",
            'name': colegio['name'],
            'handle': colegio['slug'],
            'description': f"Uniformes para {colegio['name']}",
            'is_active': True,
            'is_internal': False
        })
    
    # Agregar categoría genérica
    categories_data.append({
        'id': 'generic',
        'name': 'Productos Genéricos', 
        'handle': 'genericos',
        'description': 'Productos disponibles para múltiples colegios',
        'is_active': True,
        'is_internal': False
    })
    
    pd.DataFrame(categories_data).to_csv('medusa_categories.csv', index=False)
    
    # Products
    products_data = []
    variants_data = []
    
    for i, product in enumerate(products):
        product_id = f"prod_{i+1}"
        
        # Producto base
        products_data.append({
            'id': product_id,
            'title': product['title'],
            'handle': product['slug'],
            'description': f"Uniforme escolar - {product['base_article']}",
            'status': 'published',
            'category_id': f"college_{product['college_id']}" if product['college_id'] else 'generic',
            'type': 'uniform',
            'collection_id': None,
            'tags': f"{product['college_name']},{product['base_article']}",
            'thumbnail': None,
            'weight': None,
            'length': None,
            'height': None, 
            'width': None,
            'hs_code': None,
            'origin_country': 'CL',
            'mid_code': None,
            'material': None
        })
        
        # Variantes
        for j, variant in enumerate(product['variants']):
            variants_data.append({
                'id': f"var_{i+1}_{j+1}",
                'product_id': product_id,
                'title': f"{product['title']} - Talla {variant['size']}" if variant['size'] else product['title'],
                'sku': variant['sku'],
                'barcode': None,
                'hs_code': None,
                'origin_country': 'CL',
                'mid_code': None,
                'material': None,
                'weight': None,
                'length': None,
                'height': None,
                'width': None,
                'allow_backorder': True,
                'manage_inventory': True,
                'inventory_quantity': 100,  # Default stock
                'prices': variant['price'],
                'option_1': variant['size'] or 'Única',
                'option_2': None,
                'option_3': None
            })
    
    pd.DataFrame(products_data).to_csv('medusa_products.csv', index=False)
    pd.DataFrame(variants_data).to_csv('medusa_variants.csv', index=False)

if __name__ == "__main__":
    process_access_data()