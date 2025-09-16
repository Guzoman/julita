#!/usr/bin/env python3
"""
Investigación profunda del problema de snippets corruptos en Supabase
Vamos a usar la API para entender qué está pasando con el snippet ab0a1e92-c3b0-471a-b9fd-86dc82bc8d83
"""

import os
import requests
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print("=== INVESTIGACIÓN DE SNIPPETS CORRUPTOS EN SUPABASE ===")
print(f"URL: {supabase_url}")
print(f"Proyecto: ayuorfvindwywtltszdl")
print("=" * 70)

if not supabase_url or not supabase_key:
    print("ERROR: Faltan credenciales")
    exit(1)

# Headers para API
headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}',
    'Content-Type': 'application/json'
}

def probar_endpoint(endpoint, metodo='GET', datos=None, descripcion=""):
    """Probar un endpoint específico de la API"""
    try:
        print(f"\n--- {descripcion} ---")
        print(f"Endpoint: {metodo} {endpoint}")

        url = f"{supabase_url}{endpoint}"

        if metodo == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif metodo == 'POST':
            response = requests.post(url, headers=headers, json=datos, timeout=10)
        elif metodo == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=10)
        elif metodo == 'PATCH':
            response = requests.patch(url, headers=headers, json=datos, timeout=10)

        print(f"Status: {response.status_code}")

        if response.status_code in [200, 201]:
            try:
                data = response.json()
                print(f"Respuesta: {json.dumps(data, indent=2)[:500]}...")
                return True, data
            except:
                print(f"Respuesta (texto): {response.text[:200]}...")
                return True, response.text
        else:
            print(f"Error: {response.text}")
            return False, response.text

    except Exception as e:
        print(f"Error de conexión: {e}")
        return False, str(e)

print("\n1. EXPLORANDO ENDPOINTS DISPONIBLES...")

# Endpoints a explorar
endpoints = [
    ('/rest/v1/', 'GET', None, "API REST principal"),
    ('/rest/v1/rpc/', 'GET', None, "RPC Functions"),
    ('/storage/v1/', 'GET', None, "Storage API"),
    ('/auth/v1/', 'GET', None, "Auth API"),
    ('/functions/v1/', 'GET', None, "Functions API"),
]

for endpoint, metodo, datos, desc in endpoints:
    probar_endpoint(endpoint, metodo, datos, desc)

print("\n2. BUSCANDO TABLAS DEL SISTEMA...")

# Intentar acceder a tablas del sistema que podrían contener snippets
tablas_sistema = [
    'pg_tables',
    'information_schema.tables',
    'pg_catalog.pg_tables',
    'information_schema.routines',
    'pg_proc',
    'pg_namespace'
]

for tabla in tablas_sistema:
    probar_endpoint(f"/rest/v1/{tabla}?select=*&limit=5", 'GET', None, f"Tabla sistema: {tabla}")

print("\n3. BUSCANDO ESPECÍFICAMENTE SNIPPETS...")

# Buscar tablas relacionadas con snippets
posibles_tablas_snippets = [
    'snippets',
    'sql_snippets',
    'code_snippets',
    'user_snippets',
    'project_snippets',
    'saved_snippets',
    'query_snippets',
    'pg_stat_statements'
]

for tabla in posibles_tablas_snippets:
    probar_endpoint(f"/rest/v1/{tabla}?select=*&limit=5", 'GET', None, f"Posible tabla snippets: {tabla}")

print("\n4. INTENTANDO ACCESO DIRECTO AL SNIPPET PROBLEMÁTICO...")

# Intentar acceder al snippet específico
snippet_id = "ab0a1e92-c3b0-471a-b9fd-86dc82bc8d83"

# Probar diferentes formas de acceder al snippet
endpoints_snippet = [
    f"/rest/v1/snippets?id=eq.{snippet_id}",
    f"/rest/v1/sql_snippets?id=eq.{snippet_id}",
    f"/rest/v1/query_snippets?id=eq.{snippet_id}",
    f"/rpc/get_snippet?id={snippet_id}",
    f"/storage/v1/object/snippets/{snippet_id}",
    f"/functions/v1/snippets/{snippet_id}",
]

for endpoint in endpoints_snippet:
    probar_endpoint(endpoint, 'GET', None, f"Acceso directo al snippet {snippet_id[:8]}...")

print("\n5. EXPLORANDO METADATA DEL PROYECTO...")

# Intentar obtener metadata del proyecto
endpoints_metadata = [
    '/rest/v1/',
    '/storage/v1/bucket',
    '/auth/v1/user',
    '/functions/v1/',
]

for endpoint in endpoints_metadata:
    probar_endpoint(endpoint, 'GET', None, f"Metadata: {endpoint}")

print("\n6. BUSCANDO EN ESQUEMAS ALTERNATIVOS...")

# Buscar en diferentes esquemas
esquemas = ['public', 'auth', 'storage', 'extensions', 'information_schema']

for esquema in esquemas:
    probar_endpoint(f"/rest/v1/{esquema}.tables?select=tablename&limit=10", 'GET', None, f"Tablas en esquema {esquema}")

print("\n7. INTENTANDO EJECUTAR SQL PARA VER TABLAS...")

# SQL para buscar tablas que podrían contener snippets
sql_queries = [
    "SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%snippet%'",
    "SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%sql%'",
    "SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%query%'",
    "SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%code%'",
    "SELECT schemaname, tablename FROM pg_tables WHERE tablename LIKE '%snippet%'",
    "SELECT n.nspname, c.relname FROM pg_class c JOIN pg_namespace n ON c.relnamespace = n.oid WHERE c.relname LIKE '%snippet%'"
]

for i, sql in enumerate(sql_queries, 1):
    print(f"\n--- Consulta SQL {i} ---")
    print(f"SQL: {sql}")

    # Intentar con diferentes formatos de RPC
    rpc_endpoints = [
        f"/rest/v1/rpc/exec?query={requests.utils.quote(sql)}",
        f"/rest/v1/rpc/exec_sql?query={requests.utils.quote(sql)}",
        f"/rest/v1/rpc/execute_sql?sql={requests.utils.quote(sql)}"
    ]

    for endpoint in rpc_endpoints:
        probar_endpoint(endpoint, 'POST', None, f"RPC para consulta {i}")

print("\n8. REVISANDO EL ERROR ORIGINAL...")

# Analizar el error específico
print("El error original fue:")
print("'Unable to find snippet with ID ab0a1e92-c3b0-471a-b9fd-86dc82bc8d83'")
print("This snippet doesn't exist in your project")

print("\nEsto sugiere que:")
print("1. El snippet existe en algún lado pero está corrupto")
print("2. O hay una referencia a un snippet que fue eliminado")
print("3. O hay un problema en la configuración del proyecto")

print("\n9. INTENTANDO ACCESO A CONFIGURACIÓN DEL PROYECTO...")

# Intentar acceder a configuración
config_endpoints = [
    '/rest/v1/project_config',
    '/rest/v1/project_settings',
    '/rest/v1/config',
    '/storage/v1/project/settings'
]

for endpoint in config_endpoints:
    probar_endpoint(endpoint, 'GET', None, f"Configuración: {endpoint}")

print("\n=== INVESTIGACIÓN COMPLETADA ===")
print("Revisa los resultados above para entender la estructura de tu proyecto Supabase")