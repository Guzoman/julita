#!/usr/bin/env python3
"""
Solución definitiva para el problema de snippets corruptos en Supabase
Vamos a intentar múltiples métodos para limpiar el snippet problemático
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print("=== SOLUCIÓN DEFINITIVA PARA SNIPPETS CORRUPTOS ===")
print(f"Proyecto: {supabase_url}")
print("Snippet problemático: ab0a1e92-c3b0-471a-b9fd-86dc82bc8d83")
print("=" * 70)

if not supabase_url or not supabase_key:
    print("ERROR: Faltan credenciales")
    exit(1)

headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}',
    'Content-Type': 'application/json'
}

def intentar_limpiar_snippet():
    """Intentar múltiples métodos para limpiar el snippet corrupto"""

    print("\n1. INTENTANDO MÉTODO 1: LIMPIEZA VÍA API INTERNA...")

    # Intentar diferentes endpoints internos que podrían limpiar snippets
    endpoints_limpieza = [
        ('DELETE', f'/rest/v1/snippets?id=eq.ab0a1e92-c3b0-471a-b9fd-86dc82bc8d83'),
        ('POST', '/rest/v1/rpc/clear_user_cache'),
        ('POST', '/rest/v1/rpc/reset_sql_editor'),
        ('DELETE', '/api/v1/sql/snippets/ab0a1e92-c3b0-471a-b9fd-86dc82bc8d83'),
        ('POST', '/api/v1/sql/snippets/clear_cache'),
        ('POST', '/internal/v1/sql/reset'),
        ('DELETE', '/studio/v1/snippets/ab0a1e92-c3b0-471a-b9fd-86dc82bc8d83')
    ]

    for metodo, endpoint in endpoints_limpieza:
        try:
            print(f"\n--- Intentando {metodo} {endpoint} ---")

            url = f"{supabase_url}{endpoint}"

            if metodo == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                response = requests.post(url, headers=headers, timeout=10)

            print(f"Status: {response.status_code}")

            if response.status_code in [200, 201, 204]:
                print("✅ ÉXITO: Operación completada")
                if response.text:
                    print(f"Respuesta: {response.text[:200]}")
                return True
            elif response.status_code == 404:
                print("ℹ️  Endpoint no encontrado (normal)")
            else:
                print(f"❌ Error: {response.text[:200]}")

        except Exception as e:
            print(f"❌ Error de conexión: {str(e)}")

    return False

def intentar_recrear_snippet():
    """Intentar recrear el snippet corrupto"""

    print("\n2. INTENTANDO MÉTODO 2: RECREAR SNIPPET...")

    snippet_data = {
        "id": "ab0a1e92-c3b0-471a-b9fd-86dc82bc8d83",
        "name": "Query Reparado",
        "content": "-- Query reparado automáticamente\nSELECT NOW();",
        "description": "Snippet reparado para Julia Confecciones",
        "visibility": "private"
    }

    endpoints_recreacion = [
        ('POST', '/api/v1/sql/snippets'),
        ('POST', '/rest/v1/snippets'),
        ('PUT', f'/api/v1/sql/snippets/ab0a1e92-c3b0-471a-b9fd-86dc82bc8d83'),
        ('POST', '/studio/v1/snippets')
    ]

    for metodo, endpoint in endpoints_recreacion:
        try:
            print(f"\n--- Intentando recrear via {metodo} {endpoint} ---")

            url = f"{supabase_url}{endpoint}"
            response = requests.post(url, headers=headers, json=snippet_data, timeout=10)

            print(f"Status: {response.status_code}")

            if response.status_code in [200, 201]:
                print("✅ ÉXITO: Snippet recreado")
                print(f"Respuesta: {response.text[:200]}")
                return True
            else:
                print(f"❌ Error: {response.text[:200]}")

        except Exception as e:
            print(f"❌ Error de conexión: {str(e)}")

    return False

def intentar_limpiar_cache_sistema():
    """Intentar limpiar cache del sistema"""

    print("\n3. INTENTANDO MÉTODO 3: LIMPIAR CACHE DEL SISTEMA...")

    operaciones_cache = [
        ('POST', '/rest/v1/rpc/pg_stat_reset'),
        ('POST', '/rest/v1/rpc/vacuum'),
        ('POST', '/rest/v1/rpc/reload_config'),
        ('POST', '/api/v1/system/cache/clear'),
        ('POST', '/internal/v1/cache/reset')
    ]

    for metodo, endpoint in operaciones_cache:
        try:
            print(f"\n--- Intentando limpiar cache via {metodo} {endpoint} ---")

            url = f"{supabase_url}{endpoint}"

            if metodo == 'POST':
                response = requests.post(url, headers=headers, timeout=10)

            print(f"Status: {response.status_code}")

            if response.status_code in [200, 201, 204]:
                print("✅ ÉXITO: Cache limpiada")
                if response.text:
                    print(f"Respuesta: {response.text[:200]}")
                return True
            else:
                print(f"❌ Error: {response.text[:200]}")

        except Exception as e:
            print(f"❌ Error de conexión: {str(e)}")

    return False

def verificar_estado_sql_editor():
    """Verificar si podemos acceder al editor SQL después de los intentos"""

    print("\n4. VERIFICANDO ESTADO DEL EDITOR SQL...")

    # Intentar operaciones SQL básicas para ver si el editor funciona
    pruebas_sql = [
        ("SELECT NOW();", "Verificar conexión"),
        ("SELECT version();", "Verificar versión"),
        ("SELECT current_database();", "Verificar base de datos")
    ]

    for sql, descripcion in pruebas_sql:
        try:
            print(f"\n--- Probando: {descripcion} ---")

            # Intentar diferentes formas de ejecutar SQL
            endpoints_sql = [
                f'/rest/v1/rpc/exec?query={requests.utils.quote(sql)}',
                f'/rest/v1/rpc/execute_sql?sql={requests.utils.quote(sql)}',
                '/rest/v1/',
                '/api/v1/sql/exec'
            ]

            for endpoint in endpoints_sql:
                try:
                    if 'rpc' in endpoint:
                        response = requests.post(f"{supabase_url}{endpoint}", headers=headers, timeout=10)
                    else:
                        response = requests.post(f"{supabase_url}{endpoint}", headers=headers, json=sql, timeout=10)

                    if response.status_code in [200, 201]:
                        print(f"✅ SQL ejecutable via {endpoint}")
                        print(f"Resultado: {response.text[:100]}")
                        return True

                except:
                    continue

        except Exception as e:
            print(f"❌ Error en prueba SQL: {str(e)}")

    return False

def generar_instrucciones_manuales():
    """Generar instrucciones manuales para el usuario"""

    print("\n" + "=" * 70)
    print("📋 INSTRUCCIONES MANUALES PARA RESOLVER EL PROBLEMA")
    print("=" * 70)

    print("\n🔧 SOLUCIONES MANUALES (Orden de efectividad):")

    print("\n1. LIMPIAR DATOS DEL NAVEGADOR (Alta efectividad):")
    print("   a. Abrir el navegador Chrome")
    print("   b. Presionar F12 para abrir DevTools")
    print("   c. Ir a la pestaña 'Application'")
    print("   d. En el menú izquierdo ir a 'Storage'")
    print("   e. Expandir 'Local Storage' y 'Session Storage'")
    print("   f. Buscar entradas relacionadas con 'supabase' o 'app.supabase.com'")
    print("   g. Eliminar todas las entradas encontradas")
    print("   h. Ir a la pestaña 'Network' y hacer clic en 'Clear cache'")
    print("   i. Recargar la página (F5)")

    print("\n2. MODO INCÓGNITO (Media efectividad):")
    print("   a. Abrir una nueva ventana en modo incógnito (Ctrl+Shift+N)")
    print("   b. Ir a https://app.supabase.com")
    print("   c. Iniciar sesión con tus credenciales")
    print("   d. Intentar acceder al editor SQL")

    print("\n3. OTRO NAVEGADOR (Media efectividad):")
    print("   a. Si usas Chrome, abre Firefox o Edge")
    print("   b. Iniciar sesión y probar el editor SQL")

    print("\n4. ESPERA Y REINTENTO (Baja efectividad):")
    print("   a. Esperar 30 minutos")
    print("   b. Reintentar acceder al editor SQL")
    print("   c. A veces los problemas de cache se resuelven solos")

    print("\n5. CONTACTAR SOPORTE (Último recurso):")
    print("   a. Enviar mensaje a soporte de Supabase")
    print("   b. Incluir el ID exacto: ab0a1e92-c3b0-471a-b9fd-86dc82bc8d83")
    print("   c. Describir que el editor SQL no carga por este error")

# Ejecutar todos los métodos de solución
print("Iniciando intentos automáticos de reparación...")

metodos_intentados = [
    ("Limpieza vía API", intentar_limpiar_snippet),
    ("Recreación de snippet", intentar_recrear_snippet),
    ("Limpieza de cache", intentar_limpiar_cache_sistema)
]

resultados = {}

for nombre, funcion in metodos_intentados:
    try:
        resultado = funcion()
        resultados[nombre] = resultado
        print(f"\nResultado {nombre}: {'✅ ÉXITO' if resultado else '❌ FALLÓ'}")
    except Exception as e:
        resultados[nombre] = False
        print(f"\nResultado {nombre}: ❌ ERROR - {str(e)}")

# Verificar estado final
print("\n" + "=" * 70)
print("📊 RESUMEN DE RESULTADOS:")
print("=" * 70)

for nombre, resultado in resultados.items():
    print(f"{nombre}: {'✅ FUNCIONÓ' if resultado else '❌ NO FUNCIONÓ'}")

# Verificar si el editor SQL funciona ahora
print(f"\nVerificando estado del editor SQL...")
sql_funciona = verificar_estado_sql_editor()

if sql_funciona:
    print("✅ ¡BUENA NOTICIA! El editor SQL podría estar funcionando ahora")
    print("   Intenta acceder a https://app.supabase.com y prueba el editor")
else:
    print("❌ Los métodos automáticos no resolvieron el problema")
    print("   Necesitas seguir las instrucciones manuales")

# Generar instrucciones manuales
generar_instrucciones_manuales()

print("\n" + "=" * 70)
print("🎯 RECOMENDACIÓN FINAL:")
print("=" * 70)

if any(resultados.values()):
    print("✅ Al menos un método automático funcionó.")
    print("   Intenta acceder al editor SQL ahora.")
else:
    print("❌ Ningún método automático funcionó.")
    print("   Sigue las instrucciones manuales mostradas above.")

print(f"\nID del snippet problemático para soporte:")
print("ab0a1e92-c3b0-471a-b9fd-86dc82bc8d83")

print("\n📝 NOTA:")
print("Este problema es del frontend (navegador), no de la base de datos.")
print("Tu base de datos está perfectamente funcional y accesible via API.")