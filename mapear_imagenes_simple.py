#!/usr/bin/env python3
"""
Versión simple sin caracteres especiales para mapear imágenes
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print("=== MAPEO DE IMÁGENES A PRODUCTOS ===")
print("Versión simple sin caracteres especiales")

if not supabase_url or not supabase_key:
    print("ERROR: Faltan credenciales")
    exit(1)

headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}',
    'Content-Type': 'application/json'
}

def leer_imagenes():
    try:
        with open('image_matches.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        sku_imagenes = {}
        for item in data:
            sku = item.get('access_sku')
            if sku and item.get('images'):
                sku_imagenes[sku] = {
                    'thumbnail': item.get('thumbnail', ''),
                    'images': item.get('images', [])
                }

        print(f"Imágenes para {len(sku_imagenes)} SKUs")
        return sku_imagenes

    except Exception as e:
        print(f"Error: {str(e)}")
        return {}

def obtener_productos():
    try:
        response = requests.get(
            f"{supabase_url}/rest/v1/productos?select=*&limit=1000",
            headers=headers,
            timeout=15
        )

        if response.status_code == 200:
            productos = response.json()
            print(f"Obtenidos {len(productos)} productos")
            return productos
        else:
            print(f"Error: {response.text}")
            return []

    except Exception as e:
        print(f"Error: {str(e)}")
        return []

def generar_sql_actualizaciones():
    imagenes = leer_imagenes()
    productos = obtener_productos()

    if not imagenes or not productos:
        return

    print("\nGenerando actualizaciones SQL...")
    print("-" * 40)

    actualizaciones = []
    con_imagen = 0
    sin_imagen = 0

    for producto in productos:
        codigo = producto.get('codigo')
        nombre = producto.get('nombre', '')

        if codigo in imagenes:
            img_info = imagenes[codigo]
            imagen_url = img_info['thumbnail']

            if imagen_url:
                # Escapar comillas para SQL
                imagen_url_sql = imagen_url.replace("'", "''")
                actualizacion = f"UPDATE productos SET imagen_url = '{imagen_url_sql}' WHERE codigo = '{codigo}';"
                actualizaciones.append(actualizacion)
                con_imagen += 1

                if len(actualizaciones) <= 5:
                    print(f"OK {codigo}: {nombre[:40]}...")
                    print(f"   URL: {imagen_url[:60]}...")
        else:
            sin_imagen += 1
            if sin_imagen <= 5:
                print(f"NO {codigo}: {nombre[:40]}...")

    print(f"\nResumen:")
    print(f"  Con imagen: {con_imagen}")
    print(f"  Sin imagen: {sin_imagen}")
    print(f"  Total updates: {len(actualizaciones)}")

    return actualizaciones

if __name__ == "__main__":
    actualizaciones = generar_sql_actualizaciones()

    if actualizaciones:
        print(f"\nGuardando archivo SQL...")
        with open('ACTUALIZAR_IMAGENES.sql', 'w', encoding='utf-8') as f:
            f.write("-- Actualización de imágenes para productos\n")
            f.write("-- Julia Confecciones\n")
            f.write(f"-- {len(actualizaciones)} actualizaciones\n\n")

            for actualizacion in actualizaciones:
                f.write(actualizacion + "\n")

        print(f"✅ Guardado: ACTUALIZAR_IMAGENES.sql")
        print(f"\nInstrucciones:")
        print("1. Copia el contenido de ACTUALIZAR_IMAGENES.sql")
        print("2. Pégalo en tu editor SQL de Supabase")
        print("3. Ejecuta todas las sentencias")
    else:
        print("No se generaron actualizaciones")