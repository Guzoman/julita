#!/usr/bin/env python3
"""
Script para ejecutar el fix de concordancia Supabase-VB6 directamente
"""

import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener credenciales
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print("=== EJECUTANDO FIX CONCORDANCIA SUPABASE-VB6 ===")
print(f"URL: {supabase_url}")

if not supabase_url or not supabase_key:
    print("ERROR: Faltan credenciales")
    exit(1)

# Leer el archivo SQL
try:
    with open('fix_concordancia_supabase.sql', 'r', encoding='utf-8') as f:
        sql_content = f.read()
    print("Archivo SQL leido correctamente")
except Exception as e:
    print(f"ERROR leyendo archivo SQL: {e}")
    exit(1)

# Headers para la petición
headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}',
    'Content-Type': 'application/json',
    'Prefer': 'params=single-object'
}

# Función para ejecutar SQL
def ejecutar_sql(sql, descripcion):
    try:
        print(f"\nEjecutando: {descripcion}")

        # Usar el endpoint RPC para ejecutar SQL
        response = requests.post(
            f"{supabase_url}/rest/v1/rpc/exec_sql",
            headers=headers,
            json={'query': sql},
            timeout=30
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print("OK: Ejecutado correctamente")
            return True
        else:
            print(f"ERROR: {response.text}")
            return False

    except Exception as e:
        print(f"ERROR de conexion: {e}")
        return False

# Separar el SQL en comandos individuales
comandos_sql = []
comando_actual = ""

for linea in sql_content.split('\n'):
    linea = linea.strip()
    if linea.startswith('--') or not linea:
        continue
    if linea.endswith(';'):
        comando_actual += linea[:-1]  # Quitar el ;
        if comando_actual.strip():
            comandos_sql.append(comando_actual.strip())
        comando_actual = ""
    else:
        comando_actual += linea + " "

if comando_actual.strip():
    comandos_sql.append(comando_actual.strip())

print(f"\nSe encontraron {len(comandos_sql)} comandos SQL para ejecutar")

# Ejecutar comandos uno por uno
exitosos = 0
fallidos = 0

for i, comando in enumerate(comandos_sql, 1):
    print(f"\n--- Comando {i}/{len(comandos_sql)} ---")

    # Mostrar primeros 100 caracteres del comando
    print(f"SQL: {comando[:100]}...")

    if ejecutar_sql(comando, f"Comando {i}"):
        exitosos += 1
    else:
        fallidos += 1

print(f"\n=== RESUMEN ===")
print(f"Comandos exitosos: {exitosos}")
print(f"Comandos fallidos: {fallidos}")
print(f"Total: {len(comandos_sql)}")

if fallidos == 0:
    print("\n✅ FIX COMPLETADO CON EXITO!")
    print("Tu Supabase ahora entiende la logica de uniformes escolares")
else:
    print(f"\n⚠️  {fallidos} comandos fallaron - revisa los errores")

# Verificar los cambios
print(f"\n=== VERIFICANDO CAMBIOS ===")
try:
    response = requests.get(
        f"{supabase_url}/rest/v1/productos?select=codigo,nombre,precio_venta,cod_cole,articulo&limit=3",
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        productos = response.json()
        print("Estructura actual de productos:")
        for p in productos:
            print(f"  - Codigo: {p.get('codigo', 'N/A')}")
            print(f"    Nombre: {p.get('nombre', 'N/A')}")
            print(f"    cod_cole: {p.get('cod_cole', 'NO TIENE')}")
            print(f"    articulo: {p.get('articulo', 'NO TIENE')}")
    else:
        print(f"Error verificando: {response.text}")

except Exception as e:
    print(f"Error en verificacion: {e}")