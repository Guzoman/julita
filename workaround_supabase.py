#!/usr/bin/env python3
"""
Workaround temporal para Supabase mientras se resuelve el problema del editor SQL
Usaremos las funciones existentes y crearemos una capa de compatibilidad
"""

import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print("=== WORKAROUND SUPABASE - COMPATIBILIDAD VB6 ===")
print("Mientras se resuelve el problema del editor SQL")

if not supabase_url or not supabase_key:
    print("ERROR: Faltan credenciales")
    exit(1)

# Headers para API
headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}',
    'Content-Type': 'application/json',
    'Prefer': 'params=single-object'
}

print("\n1. VERIFICANDO ESTADO ACTUAL...")

# Verificar estado actual
try:
    response = requests.get(
        f"{supabase_url}/rest/v1/productos?select=*&limit=5",
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        productos = response.json()
        print(f"Productos encontrados: {len(productos)}")

        if productos:
            campos = list(productos[0].keys())
            print(f"Campos actuales: {campos}")

            # Verificar campos necesarios
            tiene_descripcion = 'descripcion' in campos
            tiene_cod_cole = 'cod_cole' in campos
            tiene_articulo = 'articulo' in campos

            print(f"\nEstado de campos:")
            print(f"- descripcion: {'OK' if tiene_descripcion else 'FALTA (usando nombre)'}")
            print(f"- cod_cole: {'OK' if tiene_cod_cole else 'FALTA (usando workaround)'}")
            print(f"- articulo: {'OK' if tiene_articulo else 'FALTA (usando workaround)'}")

            print("\n=== ESTRATEGIA TEMPORAL ===")
            print("Como no podemos ALTER TABLE, usaremos:")

            # Mostrar ejemplos con workaround
            print("\n2. EJEMPLOS CON WORKAROUND:")

            for i, p in enumerate(productos[:3], 1):
                print(f"\nProducto {i}:")
                print(f"  Código: {p.get('codigo')}")
                print(f"  Nombre/Descripción: {p.get('nombre', p.get('descripcion', 'SIN NOMBRE'))}")
                print(f"  Precio: {p.get('precio_venta')}")

                # Lógica VB6 simulada
                codigo = p.get('codigo')
                if codigo:
                    # Simular cálculo de talla como en VB6
                    try:
                        codigo_num = int(codigo) if isinstance(codigo, str) else codigo
                        if codigo_num < 100000:
                            talla_calculada = (codigo_num - (codigo_num // 100) * 100) // 2 - 1
                            grupo_articulo = codigo_num // 100

                            # Mapeo de tallas
                            mapa_tallas = {
                                4: 'T_4', 6: 'T_6', 8: 'T_8', 10: 'T_10',
                                12: 'T_12', 14: 'T_14', 16: 'T_16',
                                17: 'T_S', 18: 'T_M', 19: 'T_L',
                                20: 'T_XL', 21: 'T_XXL', 22: 'T_XXXL'
                            }
                            talla_etiqueta = mapa_tallas.get(talla_calculada, f'T_{talla_calculada}')

                            print(f"  Grupo Artículo (simulado): {grupo_articulo}")
                            print(f"  Talla calculada (simulada): {talla_calculada}")
                            print(f"  Talla etiqueta (simulada): {talla_etiqueta}")
                        else:
                            print(f"  Código especial: {codigo_num}")
                    except:
                        print(f"  Error procesando código: {codigo}")

                print(f"  ¿Tiene cod_cole?: {'SI' if p.get('cod_cole') else 'NO (asignar manual)'}")
                print(f"  ¿Tiene articulo?: {'SI' if p.get('articulo') else 'NO (calcular del código)'}")

    else:
        print(f"Error obteniendo productos: {response.text}")

except Exception as e:
    print(f"Error de conexión: {e}")

print("\n=== RECOMENDACIONES ===")
print("1. MIENTRAS TANTO, USA ESTA LÓGICA EN TU APLICACIÓN:")
print("   - Calcular grupo_articulo = codigo // 100")
print("   - Calcular talla = (codigo % 100) // 2 - 1")
print("   - Mapear talla a etiquetas usando el diccionario")
print("")
print("2. PARA SOLUCIONAR DEFINITIVAMENTE:")
print("   - Contacta a soporte de Supabase sobre el error de snippets")
print("   - O intenta acceder desde otro navegador/computadora")
print("   - O crea un nuevo proyecto de Supabase (último recurso)")
print("")
print("3. DATOS A ACTUALIZAR MANUALMENTE:")
print("   - Cada producto necesita cod_cole (ID del colegio)")
print("   - articulo puede calcularse automáticamente del código")

print("\n=== SIMULADOR VB6 ===")
print("Probando la lógica VB6 con ejemplos:")

ejemplos = [1008, 1012, 1018, 2010, 2014]
for codigo in ejemplos:
    grupo = codigo // 100
    talla_num = (codigo % 100) // 2 - 1
    mapa_tallas = {
        4: 'T_4', 6: 'T_6', 8: 'T_8', 10: 'T_10',
        12: 'T_12', 14: 'T_14', 16: 'T_16',
        17: 'T_S', 18: 'T_M', 19: 'T_L',
        20: 'T_XL', 21: 'T_XXL', 22: 'T_XXXL'
    }
    talla_etiqueta = mapa_tallas.get(talla_num, f'T_{talla_num}')

    print(f"Código {codigo} -> Grupo: {grupo}, Talla: {talla_etiqueta}")

print("\n¡Con esto tu aplicación puede funcionar aunque Supabase no tenga los campos aún!")