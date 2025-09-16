#!/usr/bin/env python3
"""
Verificación simple de URLs de imágenes sin caracteres especiales
"""

import json

print("=== VERIFICACIÓN DE URLs DE IMÁGENES ===")
print("Julia Confecciones Uniformes Escolares")
print("=" * 50)

try:
    with open('image_matches.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Total de entradas con imágenes: {len(data)}")

    print("\nEJEMPLOS DE URLs DE IMÁGENES:")
    print("-" * 40)

    # Mostrar primeros 10 productos con imágenes
    for i, item in enumerate(data[:10]):
        sku = item.get('access_sku', 'N/A')
        desc = item.get('access_desc', 'N/A')
        images = item.get('images', [])

        print(f"\n{i+1}. SKU: {sku}")
        print(f"   Descripción: {desc}")
        print(f"   Imágenes: {len(images)}")

        if images:
            print(f"   Primera imagen: {images[0]}")

    print(f"\nRESUMEN:")
    print(f"- Total SKUs con imágenes: {len(data)}")
    print(f"- Imágenes son del sitio: juliaconfecciones.cl")
    print(f"- Formato: /wp-content/uploads/año/mes/nombre-archivo.jpg")

    print(f"\nALGUNAS URLS DE EJEMPLO:")
    for item in data[:3]:
        if item.get('images'):
            print(f"- {item['images'][0]}")

except Exception as e:
    print(f"Error: {str(e)}")

print(f"\n¿QUIERES AGREGAR ESTAS IMÁGENES A SUPABASE?")
print(f"Se necesita un campo 'imagen_url' en la tabla productos")