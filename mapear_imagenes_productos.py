#!/usr/bin/env python3
"""
Script para mapear URLs de imágenes desde JSON a productos en Supabase
Usa imágenes genéricas por producto base
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print("=== MAPEO DE IMÁGENES A PRODUCTOS SUPABASE ===")
print("Imágenes genéricas por producto base")
print("=" * 60)

if not supabase_url or not supabase_key:
    print("ERROR: Faltan credenciales de Supabase")
    exit(1)

headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}',
    'Content-Type': 'application/json'
}

def leer_imagenes_disponibles():
    """Leer el archivo JSON con URLs de imágenes"""
    try:
        with open('image_matches.json', 'r', encoding='utf-8') as f:
            imagenes_data = json.load(f)

        # Crear mapeo SKU -> información de imagen
        sku_imagenes = {}
        for item in imagenes_data:
            sku = item.get('access_sku')
            if sku and item.get('images'):
                sku_imagenes[sku] = {
                    'thumbnail': item.get('thumbnail', ''),
                    'images': item.get('images', []),
                    'descripcion': item.get('access_desc', ''),
                    'title': item.get('wp_title', '')
                }

        print(f"Imágenes disponibles para {len(sku_imagenes)} SKUs")
        return sku_imagenes

    except Exception as e:
        print(f"Error leyendo imágenes: {str(e)}")
        return {}

def obtener_productos_supabase():
    """Obtener productos actuales de Supabase"""
    try:
        response = requests.get(
            f"{supabase_url}/rest/v1/productos?select=*&limit=1000",
            headers=headers,
            timeout=15
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

def generar_actualizaciones_imagenes():
    """Generar sentencias UPDATE para actualizar URLs de imágenes"""

    imagenes = leer_imagenes_disponibles()
    productos = obtener_productos_supabase()

    if not imagenes or not productos:
        return

    print("\n" + "=" * 60)
    print("GENERANDO ACTUALIZACIONES DE IMÁGENES")
    print("=" * 60)

    actualizaciones = []
    productos_con_imagen = 0
    productos_sin_imagen = 0

    for producto in productos:
        codigo = producto.get('codigo')
        nombre = producto.get('nombre', '')

        if codigo in imagenes:
            img_info = imagenes[codigo]
            imagen_url = img_info['thumbnail']  # Usar thumbnail como principal

            if imagen_url:
                # Escapar comillas simples para SQL
                imagen_url_sql = imagen_url.replace("'", "''")

                actualizacion = f"UPDATE productos SET imagen_url = '{imagen_url_sql}' WHERE codigo = '{codigo}';"
                actualizaciones.append(actualizacion)
                productos_con_imagen += 1

                # Mostrar algunos ejemplos
                if len(actualizaciones) <= 10:
                    print(f"✅ {codigo}: {nombre[:50]}...")
                    print(f"   Imagen: {imagen_url[:80]}...")

        else:
            productos_sin_imagen += 1
            if productos_sin_imagen <= 5:
                print(f"❌ {codigo}: {nombre[:50]}... - SIN IMAGEN")

    print(f"\nRESUMEN:")
    print(f"  Productos con imagen: {productos_con_imagen}")
    print(f"  Productos sin imagen: {productos_sin_imagen}")
    print(f"  Total actualizaciones: {len(actualizaciones)}")

    return actualizaciones

def ejecutar_actualizaciones(actualizaciones):
    """Ejecutar las actualizaciones en Supabase"""
    if not actualizaciones:
        print("No hay actualizaciones para ejecutar")
        return False

    print(f"\n" + "=" * 60)
    print("EJECUTANDO ACTUALIZACIONES EN SUPABASE")
    print("=" * 60)

    exitosas = 0
    fallidas = 0

    for i, actualizacion in enumerate(actualizaciones, 1):
        try:
            if i <= 5:  # Mostrar primeras 5 actualizaciones
                print(f"{i}. {actualizacion}")

            # Ejecutar la actualización
            response = requests.post(
                f"{supabase_url}/rest/v1/rpc/exec",
                headers=headers,
                json=actualizacion,
                timeout=10
            )

            if response.status_code in [200, 201, 204]:
                exitosas += 1
                if i <= 5:
                    print(f"   -> EXITOSA")
            else:
                fallidas += 1
                if i <= 5:
                    print(f"   -> FALLIDA: {response.text}")

            # Pausa para no sobrecargar la API
            if i % 10 == 0:
                print(f"Procesando... {i}/{len(actualizaciones)}")

        except Exception as e:
            fallidas += 1
            print(f"Error en actualización {i}: {str(e)}")

    print(f"\nRESULTADO:")
    print(f"  Actualizaciones exitosas: {exitosas}")
    print(f"  Actualizaciones fallidas: {fallidas}")
    print(f"  Total: {len(actualizaciones)}")

    return fallidas == 0

def guardar_sql_para_manual(actualizaciones):
    """Guardar las actualizaciones en un archivo SQL para ejecución manual"""
    if not actualizaciones:
        return

    print(f"\nGuardando actualizaciones en archivo SQL...")

    with open('ACTUALIZAR_IMAGENES_PRODUCTOS.sql', 'w', encoding='utf-8') as f:
        f.write("-- Actualización de URLs de imágenes en productos\n")
        f.write("-- Julia Confecciones - Imágenes genéricas por producto\n")
        f.write(f"-- Generated: {len(actualizaciones)} actualizaciones\n\n")

        for actualizacion in actualizaciones:
            f.write(actualizacion + "\n")

    print(f"✅ Guardado en: ACTUALIZAR_IMAGENES_PRODUCTOS.sql")

if __name__ == "__main__":
    # Generar actualizaciones
    actualizaciones = generar_actualizaciones_imagenes()

    if actualizaciones:
        # Opción 1: Guardar SQL para ejecución manual
        guardar_sql_para_manual(actualizaciones)

        # Opción 2: Intentar ejecutar via API (comentado por seguridad)
        # ejecutar_actualizaciones(actualizaciones)

        print(f"\n" + "=" * 60)
        print("INSTRUCCIONES:")
        print("=" * 60)
        print("1. El archivo ACTUALIZAR_IMAGENES_PRODUCTOS.sql ha sido generado")
        print("2. Cópialo y pégalo en tu editor SQL de Supabase")
        print("3. Ejecuta todas las sentencias UPDATE")
        print("4. Verifica que las imágenes se asignaron correctamente")
    else:
        print("No se generaron actualizaciones")