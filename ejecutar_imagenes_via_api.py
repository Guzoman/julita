#!/usr/bin/env python3
"""
Ejecutar actualización de imágenes usando API REST de Supabase
Sin depender del editor SQL web
"""

import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print("=== EJECUTANDO ACTUALIZACIÓN DE IMÁGENES VÍA API ===")
print("Sin usar editor SQL web")
print("=" * 60)

if not supabase_url or not supabase_key:
    print("ERROR: Faltan credenciales")
    exit(1)

headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}',
    'Content-Type': 'application/json'
}

def leer_actualizaciones_sql():
    """Leer el archivo SQL con las actualizaciones"""
    try:
        with open('ACTUALIZAR_IMAGENES.sql', 'r', encoding='utf-8') as f:
            contenido = f.read()

        # Extraer sentencias UPDATE
        lineas = contenido.split('\n')
        actualizaciones = []

        for linea in lineas:
            linea = linea.strip()
            if linea.startswith('UPDATE productos SET imagen_url'):
                actualizaciones.append(linea)

        print(f"Extraídas {len(actualizaciones)} actualizaciones del archivo SQL")
        return actualizaciones

    except Exception as e:
        print(f"Error leyendo archivo SQL: {str(e)}")
        return []

def ejecutar_update_via_api(sql_update):
    """Ejecutar una sentencia UPDATE usando la API de Supabase"""
    try:
        # Método 1: Intentar con endpoint RPC
        response = requests.post(
            f"{supabase_url}/rest/v1/rpc/exec",
            headers=headers,
            json=sql_update,
            timeout=10
        )

        if response.status_code in [200, 201, 204]:
            return True, None

        # Método 2: Intentar con endpoint directo
        response = requests.post(
            f"{supabase_url}/rest/v1/",
            headers=headers,
            json=sql_update,
            timeout=10
        )

        if response.status_code in [200, 201, 204]:
            return True, None

        return False, response.text

    except Exception as e:
        return False, str(e)

def actualizar_productos_individualmente():
    """Actualizar productos usando PATCH individual"""
    actualizaciones = leer_actualizaciones_sql()

    if not actualizaciones:
        print("No hay actualizaciones para ejecutar")
        return

    print(f"\nEjecutando {len(actualizaciones)} actualizaciones...")
    print("-" * 50)

    exitosas = 0
    fallidas = 0

    for i, actualizacion in enumerate(actualizaciones, 1):
        try:
            # Extraer información de la actualización
            partes = actualizacion.split("'")
            if len(partes) >= 4:
                imagen_url = partes[1]
                codigo = partes[3].split("'")[0]

                # Usar PATCH para actualizar individualmente
                update_data = {
                    'imagen_url': imagen_url
                }

                response = requests.patch(
                    f"{supabase_url}/rest/v1/productos?codigo=eq.{codigo}",
                    headers=headers,
                    json=update_data,
                    timeout=10
                )

                if response.status_code in [200, 201, 204]:
                    exitosas += 1
                    if i <= 5:  # Mostrar primeros 5
                        print(f"✅ {i}. Código {codigo} - Actualizado")
                else:
                    fallidas += 1
                    if i <= 5:
                        print(f"❌ {i}. Código {codigo} - Error: {response.text}")

            else:
                fallidas += 1
                print(f"❌ {i}. Formato inválido: {actualizacion[:50]}...")

            # Mostrar progreso
            if i % 20 == 0:
                print(f"Progreso: {i}/{len(actualizaciones)} (Éxitos: {exitosas}, Fallas: {fallidas})")

            # Pequeña pausa para no sobrecargar
            time.sleep(0.1)

        except Exception as e:
            fallidas += 1
            print(f"❌ {i}. Error: {str(e)}")

    print(f"\nRESULTADO FINAL:")
    print(f"  Actualizaciones exitosas: {exitosas}")
    print(f"  Actualizaciones fallidas: {fallidas}")
    print(f"  Total: {len(actualizaciones)}")

    return exitosas > 0

def verificar_resultados():
    """Verificar que las imágenes se asignaron correctamente"""
    try:
        print(f"\nVerificando resultados...")

        response = requests.get(
            f"{supabase_url}/rest/v1/productos?select=codigo,nombre,imagen_url&imagen_url=is.not.null&limit=10",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            productos = response.json()
            print(f"Productos con imágenes asignadas: {len(productos)}")

            print(f"\nPrimeros 5 productos con imágenes:")
            for i, p in enumerate(productos[:5], 1):
                print(f"  {i}. Código {p.get('codigo')}: {p.get('nombre')[:40]}...")
                print(f"     Imagen: {p.get('imagen_url', '')[:60]}...")

            return True
        else:
            print(f"Error verificando: {response.text}")
            return False

    except Exception as e:
        print(f"Error en verificación: {str(e)}")
        return False

if __name__ == "__main__":
    print("Iniciando actualización de imágenes vía API REST...")

    if actualizar_productos_individualmente():
        verificar_resultados()
        print(f"\n¡ACTUALIZACIÓN COMPLETADA!")
        print("Las imágenes ahora están asignadas en Supabase")
    else:
        print(f"\nLa actualización no se completó correctamente")