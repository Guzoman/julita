#!/usr/bin/env python3
"""
Buscar URLs de imágenes para productos principales de Julia Confecciones
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print("=== BÚSQUEDA DE IMÁGENES DE PRODUCTOS ===")
print("Para Julia Confecciones Uniformes Escolares")
print("=" * 60)

def leer_imagenes_mapeadas():
    """Leer el archivo de mapeo de imágenes"""
    try:
        with open('image_matches.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Leídas {len(data)} entradas de imágenes")
        return data
    except Exception as e:
        print(f"Error leyendo imágenes: {str(e)}")
        return []

def obtener_productos_supabase():
    """Obtener productos actuales de Supabase"""
    if not supabase_url or not supabase_key:
        print("ERROR: Faltan credenciales de Supabase")
        return []

    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(
            f"{supabase_url}/rest/v1/productos?select=*&limit=10",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            productos = response.json()
            print(f"Obtenidos {len(productos)} productos de Supabase")
            return productos
        else:
            print(f"Error obteniendo productos: {response.text}")
            return []

    except Exception as e:
        print(f"Error: {str(e)}")
        return []

def mapear_imagenes_a_productos():
    """Mapear imágenes disponibles a productos de Supabase"""

    imagenes = leer_imagenes_mapeadas()
    productos = obtener_productos_supabase()

    if not imagenes or not productos:
        return

    print("\n" + "=" * 60)
    print("MAPEO DE IMÁGENES A PRODUCTOS")
    print("=" * 60)

    # Crear diccionario de mapeo SKU -> imágenes
    sku_imagenes = {}
    for img_data in imagenes:
        sku = img_data.get('access_sku')
        if sku:
            sku_imagenes[sku] = {
                'images': img_data.get('images', []),
                'thumbnail': img_data.get('thumbnail'),
                'descripcion': img_data.get('access_desc', ''),
                'wp_title': img_data.get('wp_title', '')
            }

    print(f"\nMAPEO DISPONIBLE PARA {len(sku_imagenes)} SKUs:")
    print()

    # Mostrar productos de Supabase con imágenes disponibles
    productos_con_imagen = 0
    productos_sin_imagen = 0

    for producto in productos:
        codigo = producto.get('codigo')
        nombre = producto.get('nombre', '')

        if codigo in sku_imagenes:
            img_info = sku_imagenes[codigo]
            productos_con_imagen += 1

            print(f"✅ SKU {codigo}: {nombre}")
            print(f"   Imágenes: {len(img_info['images'])} disponibles")
            print(f"   Thumbnail: {img_info['thumbnail'][:80]}...")
            print(f"   Origen: {img_info['wp_title']}")
            print()
        else:
            productos_sin_imagen += 1
            print(f"❌ SKU {codigo}: {nombre} - SIN IMÁGENES")
            print()

    print(f"\nRESUMEN:")
    print(f"  Productos con imágenes: {productos_con_imagen}")
    print(f"  Productos sin imágenes: {productos_sin_imagen}")
    print(f"  Total SKUs con imágenes: {len(sku_imagenes)}")

    # Mostrar algunas URLs de ejemplo
    print(f"\nEJEMPLOS DE URLs DE IMÁGENES:")
    print("-" * 40)

    for sku, img_info in list(sku_imagenes.items())[:5]:
        print(f"\nSKU {sku} - {img_info['descripcion']}")
        if img_info['images']:
            print(f"URL: {img_info['images'][0]}")

    return sku_imagenes

def generar_sql_para_imagenes():
    """Generar SQL para agregar URLs de imágenes a productos"""
    imagenes = leer_imagenes_mapeadas()

    print("\n" + "=" * 60)
    print("SQL PARA AGREGAR IMÁGENES A PRODUCTOS")
    print("=" * 60)

    print("-- Agregar campo para imágenes a productos (si no existe)")
    print("ALTER TABLE productos ADD COLUMN IF NOT EXISTS imagen_url TEXT;")
    print("ALTER TABLE productos ADD COLUMN IF NOT EXISTS imagenes TEXT[];")
    print()

    print("-- Actualizar productos con URLs de imágenes")
    for img_data in imagenes[:10]:  # Primeros 10 como ejemplo
        sku = img_data.get('access_sku')
        if sku and img_data.get('images'):
            thumbnail = img_data.get('thumbnail', '')
            if thumbnail:
                # Escapar comillas para SQL
                thumbnail_sql = thumbnail.replace("'", "''")
                print(f"UPDATE productos SET imagen_url = '{thumbnail_sql}' WHERE codigo = '{sku}';")

    print("\n-- Nota: Esto es un ejemplo. Deberás:")
    print("1. Agregar el campo imagen_url a la tabla productos")
    print("2. Ejecutar los UPDATE correspondientes")
    print("3. Considerar usar un array de imágenes si necesitas múltiples")

if __name__ == "__main__":
    mapeo = mapear_imagenes_a_productos()

    if mapeo:
        generar_sql_para_imagenes()

        print(f"\n" + "=" * 60)
        print("CONCLUSIONES:")
        print("=" * 60)
        print("✅ Se encontraron URLs de imágenes para varios productos")
        print("✅ Las imágenes están en el sitio web actual: juliaconfecciones.cl")
        print("✅ Formato: /wp-content/uploads/año/mes/nombre-archivo.jpg")
        print("✅ Se pueden integrar a Supabase con un campo adicional")
        print()
        print("📋 PRÓXIMOS PASOS:")
        print("1. Agregar campo imagen_url a tabla productos")
        print("2. Ejecutar script de actualización de URLs")
        print("3. Verificar que las imágenes sean accesibles")
    else:
        print("No se encontraron imágenes para mapear")