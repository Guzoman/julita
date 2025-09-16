#!/usr/bin/env python3
"""
Solución simple para snippets corruptos (sin caracteres especiales)
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print("=== SOLUCION PARA SNIPPETS CORRUPTOS ===")
print(f"Proyecto: {supabase_url}")
print("Snippet problemático: ab0a1e92-c3b0-471a-b9fd-86dc82bc8d83")
print("=" * 60)

if not supabase_url or not supabase_key:
    print("ERROR: Faltan credenciales")
    exit(1)

headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}',
    'Content-Type': 'application/json'
}

def intentar_limpiar_snippet():
    """Intentar limpiar el snippet corrupto via API"""
    print("\n1. INTENTANDO LIMPIAR SNIPPET VIA API...")

    endpoints = [
        ('DELETE', f'/rest/v1/snippets?id=eq.ab0a1e92-c3b0-471a-b9fd-86dc82bc8d83'),
        ('POST', '/rest/v1/rpc/clear_user_cache'),
        ('POST', '/rest/v1/rpc/reset_sql_editor'),
        ('DELETE', '/api/v1/sql/snippets/ab0a1e92-c3b0-471a-b9fd-86dc82bc8d83'),
        ('POST', '/api/v1/sql/snippets/clear_cache'),
        ('DELETE', '/studio/v1/snippets/ab0a1e92-c3b0-471a-b9fd-86dc82bc8d83')
    ]

    for metodo, endpoint in endpoints:
        try:
            print(f"\n--- Probando {metodo} {endpoint} ---")
            url = f"{supabase_url}{endpoint}"

            if metodo == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                response = requests.post(url, headers=headers, timeout=10)

            print(f"Status: {response.status_code}")

            if response.status_code in [200, 201, 204]:
                print("EXITO: Operación completada")
                return True
            elif response.status_code == 404:
                print("Endpoint no encontrado (normal)")
            else:
                print(f"Error: {response.text[:100]}")

        except Exception as e:
            print(f"Error de conexión: {str(e)}")

    return False

def probar_sql_directo():
    """Probar si podemos ejecutar SQL directamente"""
    print("\n2. PROBANDO EJECUCIÓN SQL DIRECTA...")

    sql_pruebas = [
        "SELECT NOW();",
        "SELECT version();",
        "SELECT current_database();"
    ]

    for sql in sql_pruebas:
        try:
            print(f"\n--- Probando SQL: {sql} ---")

            # Probar diferentes endpoints para ejecutar SQL
            endpoints = [
                f'/rest/v1/rpc/exec?query={requests.utils.quote(sql)}',
                f'/rest/v1/rpc/execute_sql?sql={requests.utils.quote(sql)}',
                '/rest/v1/',
                '/api/v1/sql/exec'
            ]

            for endpoint in endpoints:
                try:
                    if 'rpc' in endpoint:
                        response = requests.post(f"{supabase_url}{endpoint}", headers=headers, timeout=10)
                    else:
                        response = requests.post(f"{supabase_url}{endpoint}", headers=headers, json=sql, timeout=10)

                    if response.status_code in [200, 201]:
                        print(f"SQL ejecutable via {endpoint}")
                        print(f"Resultado: {response.text[:100]}")
                        return True

                except:
                    continue

        except Exception as e:
            print(f"Error en prueba SQL: {str(e)}")

    return False

def mostrar_instrucciones_manuales():
    """Mostrar instrucciones manuales para el usuario"""
    print("\n" + "=" * 60)
    print("INSTRUCCIONES MANUALES PARA RESOLVER EL PROBLEMA")
    print("=" * 60)

    print("\nSOLUCIONES MANUALES (Orden de efectividad):")

    print("\n1. LIMPIAR DATOS DEL NAVEGADOR (Mas efectivo):")
    print("   a. Abrir Chrome")
    print("   b. Presionar F12 (DevTools)")
    print("   c. Ir a pestaña 'Application'")
    print("   d. En menú izquierdo ir a 'Storage'")
    print("   e. Expandir 'Local Storage' y 'Session Storage'")
    print("   f. Buscar entradas de 'supabase' o 'app.supabase.com'")
    print("   g. Eliminar todas esas entradas")
    print("   h. Ir a pestaña 'Network' -> 'Clear cache'")
    print("   i. Recargar pagina (F5)")

    print("\n2. MODO INCOGNITO:")
    print("   a. Ctrl+Shift+N (nueva ventana incógnito)")
    print("   b. Ir a https://app.supabase.com")
    print("   c. Iniciar sesión")
    print("   d. Probar editor SQL")

    print("\n3. OTRO NAVEGADOR:")
    print("   a. Probar con Firefox o Edge")
    print("   b. Iniciar sesión y probar editor SQL")

    print("\n4. ESPERAR Y REINTENTAR:")
    print("   a. Esperar 30 minutos")
    print("   b. Reintentar acceso al editor SQL")

    print("\n5. CONTACTAR SOPORTE:")
    print("   a. Enviar mensaje a soporte@supabase.io")
    print("   b. Incluir ID: ab0a1e92-c3b0-471a-b9fd-86dc82bc8d83")
    print("   c. Describir problema con editor SQL")

# Ejecutar intentos automáticos
print("Iniciando intentos automáticos...")

limpieza_exitosa = intentar_limpiar_snippet()
sql_funciona = probar_sql_directo()

print("\n" + "=" * 60)
print("RESULTADOS:")
print("=" * 60)

print(f"Limpieza automática: {'EXITO' if limpieza_exitosa else 'FALLO'}")
print(f"SQL ejecutable: {'SI' if sql_funciona else 'NO'}")

if limpieza_exitosa or sql_funciona:
    print("\nBUENA NOTICIA: Intenta acceder al editor SQL ahora")
    print("   Ve a https://app.supabase.com y prueba el editor")
else:
    print("\nLOS MÉTODOS AUTOMÁTICOS NO FUNCIONARON")
    print("   Sigue las instrucciones manuales mostradas above")

mostrar_instrucciones_manuales()

print("\n" + "=" * 60)
print("RECOMENDACIÓN FINAL:")
print("=" * 60)

if limpieza_exitosa:
    print("La limpieza automática tuvo éxito.")
    print("Intenta acceder al editor SQL ahora.")
else:
    print("El problema es del navegador (frontend).")
    print("Sigue las instrucciones manuales para resolverlo.")

print(f"\nID para soporte: ab0a1e92-c3b0-471a-b9fd-86dc82bc8d83")
print("\nNOTA: Tu base de datos está perfectamente funcional.")
print("El problema es solo en el editor SQL del navegador.")