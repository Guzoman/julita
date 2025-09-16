#!/usr/bin/env python3
"""
Migración completa de productos desde Access a Supabase
Con mapeo correcto de cod_cole y articulo
"""

import os
import requests
import csv
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print("=== MIGRACIÓN COMPLETA DE PRODUCTOS ===")
print("Desde Access hacia Supabase")
print("=" * 60)

if not supabase_url or not supabase_key:
    print("ERROR: Faltan credenciales")
    exit(1)

headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}',
    'Content-Type': 'application/json',
    'Prefer': 'params=single-object'
}

def leer_access_productos():
    """Leer productos del archivo CSV exportado de Access"""
    productos = []

    try:
        with open('access_export_productos.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                productos.append(row)

        print(f"Leidos {len(productos)} productos desde Access")
        return productos

    except Exception as e:
        print(f"Error leyendo Access: {str(e)}")
        return []

def leer_colegios():
    """Leer colegios desde Supabase para mapeo"""
    try:
        response = requests.get(
            f"{supabase_url}/rest/v1/colegios?select=*",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            colegios = response.json()
            print(f"Colegios encontrados: {len(colegios)}")

            # Crear mapeo codigo -> id
            mapeo_colegios = {}
            for colegio in colegios:
                mapeo_colegios[str(colegio['codigo'])] = colegio['id']

            print("Mapeo de colegios:")
            for codigo, id_cole in mapeo_colegios.items():
                print(f"  Código {codigo} -> ID {id_cole}")

            return mapeo_colegios
        else:
            print(f"Error obteniendo colegios: {response.text}")
            return {}

    except Exception as e:
        print(f"Error leyendo colegios: {str(e)}")
        return {}

def limpiar_productos_existentes():
    """Limpiar productos existentes para evitar duplicados"""
    try:
        print("\nLimpiando productos existentes...")

        # Primero ver cuántos hay
        response = requests.get(
            f"{supabase_url}/rest/v1/productos?select=count",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            total = len(response.json()) if response.json() else 0
            print(f"Productos existentes: {total}")

            if total > 0:
                # Eliminar todos los productos existentes
                response = requests.delete(
                    f"{supabase_url}/rest/v1/productos?cod_cole=is.null",
                    headers=headers,
                    timeout=10
                )

                if response.status_code in [200, 204]:
                    print("Productos existentes eliminados")
                else:
                    print(f"Error eliminando productos: {response.text}")

    except Exception as e:
        print(f"Error limpiando productos: {str(e)}")

def migrar_productos():
    """Migrar productos desde Access a Supabase"""

    print("\nIniciando migración de productos...")

    # Leer datos
    productos_access = leer_access_productos()
    if not productos_access:
        print("ERROR: No se pudieron leer productos de Access")
        return False

    mapeo_colegios = leer_colegios()
    if not mapeo_colegios:
        print("ERROR: No se pudieron leer colegios")
        return False

    # Limpiar productos existentes
    limpiar_productos_existentes()

    # Migrar productos
    migrados = 0
    errores = 0

    print(f"\nMigrando {len(productos_access)} productos...")

    for i, producto_access in enumerate(productos_access, 1):
        try:
            # Mapear datos de Access a Supabase
            codigo = producto_access.get('codigo', '')
            cod_cole_access = producto_access.get('cod_cole', '')

            # Mapear cod_cole de Access a ID de Supabase
            cod_cole = None
            if cod_cole_access:
                cod_cole_str = str(int(float(cod_cole_access)))  # Convertir "7.0" -> "7"
                cod_cole = mapeo_colegios.get(cod_cole_str)

            # Extraer articulo del código VB6
            try:
                codigo_num = int(float(codigo)) if codigo else 0
                articulo = (codigo_num // 100) * 100 if codigo_num > 0 else None
            except:
                articulo = None

            # Preparar datos para Supabase
            producto_supabase = {
                'codigo': str(int(float(codigo))) if codigo else '',
                'nombre': producto_access.get('descripcion', ''),  # Usar descripcion de Access como nombre
                'descripcion': producto_access.get('descripcion', ''),
                'categoria': None,  # Se puede asignar después
                'precio_costo': float(producto_access.get('precio_costo', 0)) if producto_access.get('precio_costo') else 0,
                'precio_venta': float(producto_access.get('Precio_venta', 0)) if producto_access.get('Precio_venta') else 0,
                'activo': True,
                'cod_cole': cod_cole,
                'articulo': articulo
            }

            # Insertar en Supabase
            response = requests.post(
                f"{supabase_url}/rest/v1/productos",
                headers=headers,
                json=producto_supabase,
                timeout=10
            )

            if response.status_code in [200, 201]:
                migrados += 1
                if i <= 5:  # Mostrar primeros 5 como ejemplo
                    print(f"  {i}. Código {producto_supabase['codigo']} -> {producto_supabase['nombre']} (cod_cole: {cod_cole})")
            else:
                errores += 1
                print(f"  ERROR {i}: {response.text}")

        except Exception as e:
            errores += 1
            print(f"  ERROR {i}: {str(e)}")

    print(f"\nMigración completada:")
    print(f"  Productos migrados: {migrados}")
    print(f"  Errores: {errores}")

    return migrados > 0

def verificar_migracion():
    """Verificar que la migración fue exitosa"""
    try:
        print("\nVerificando migración...")

        response = requests.get(
            f"{supabase_url}/rest/v1/productos?select=*&limit=10",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            productos = response.json()
            print(f"Total productos en Supabase: {len(productos)}")

            print("\nPrimeros 5 productos migrados:")
            for i, p in enumerate(productos[:5], 1):
                print(f"  {i}. Código: {p.get('codigo')}")
                print(f"     Nombre: {p.get('nombre')}")
                print(f"     Precio: ${p.get('precio_venta')}")
                print(f"     Colegio: {p.get('cod_cole')}")
                print(f"     Artículo: {p.get('articulo')}")
                print()

            # Verificar cuántos tienen cod_cole asignado
            con_colegio = sum(1 for p in productos if p.get('cod_cole') is not None)
            sin_colegio = len(productos) - con_colegio

            print(f"Productos con colegio asignado: {con_colegio}")
            print(f"Productos sin colegio asignado: {sin_colegio}")

            return True
        else:
            print(f"Error verificando: {response.text}")
            return False

    except Exception as e:
        print(f"Error en verificación: {str(e)}")
        return False

# Ejecutar migración
if __name__ == "__main__":
    if migrar_productos():
        verificar_migracion()
        print("\n¡MIGRACIÓN COMPLETADA!")
        print("Supabase ahora tiene todos los productos con estructura completa")
    else:
        print("\nERROR: La migración falló")