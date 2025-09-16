#!/usr/bin/env python3
"""
Verificar qué colegios del Access no están en Supabase
"""

import os
import requests
import csv
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print("=== VERIFICANDO COLEGIOS FALTANTES ===")

if not supabase_url or not supabase_key:
    print("ERROR: Faltan credenciales")
    exit(1)

headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}',
    'Content-Type': 'application/json'
}

def leer_colegios_access():
    """Leer colegios del archivo CSV de Access"""
    colegios_access = {}

    try:
        with open('access_export_Colegios.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                codigo = row.get('codigo', '')
                descripcion = row.get('descripcion', '')
                if codigo and descripcion:
                    colegios_access[codigo] = descripcion

        print(f"Colegios en Access: {len(colegios_access)}")
        for codigo, desc in colegios_access.items():
            print(f"  {codigo}: {desc}")

        return colegios_access

    except Exception as e:
        print(f"Error leyendo colegios de Access: {str(e)}")
        return {}

def leer_colegios_supabase():
    """Leer colegios de Supabase"""
    try:
        response = requests.get(
            f"{supabase_url}/rest/v1/colegios?select=*",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            colegios_supabase = {}
            for colegio in response.json():
                colegios_supabase[str(colegio['codigo'])] = colegio['descripcion']

            print(f"\nColegios en Supabase: {len(colegios_supabase)}")
            for codigo, desc in colegios_supabase.items():
                print(f"  {codigo}: {desc}")

            return colegios_supabase
        else:
            print(f"Error obteniendo colegios de Supabase: {response.text}")
            return {}

    except Exception as e:
        print(f"Error leyendo colegios de Supabase: {str(e)}")
        return {}

def comparar_colegios():
    """Comparar colegios entre Access y Supabase"""
    print("\n" + "=" * 50)
    print("COMPARANDO COLEGIOS")
    print("=" * 50)

    colegios_access = leer_colegios_access()
    colegios_supabase = leer_colegios_supabase()

    if not colegios_access or not colegios_supabase:
        return

    # Encontrar colegios faltantes en Supabase
    faltantes = {}
    for codigo, desc in colegios_access.items():
        if codigo not in colegios_supabase:
            faltantes[codigo] = desc

    print(f"\nCOLEGIOS FALTANTES EN SUPABASE: {len(faltantes)}")
    for codigo, desc in faltantes.items():
        print(f"  {codigo}: {desc} <- FALTA")

    # Mostrar resumen
    print(f"\nRESUMEN:")
    print(f"  Total en Access: {len(colegios_access)}")
    print(f"  Total en Supabase: {len(colegios_supabase)}")
    print(f"  Faltantes: {len(faltantes)}")
    print(f"  Completitud: {len(colegios_supabase)}/{len(colegios_access)} ({len(colegios_supabase)/len(colegios_access)*100:.1f}%)")

    return faltantes

if __name__ == "__main__":
    faltantes = comparar_colegios()

    if faltantes:
        print(f"\n¿DESEA MIGRAR LOS COLEGIOS FALTANTES?")
        print(f"Estos colegios faltan en Supabase y son necesarios para los productos")
    else:
        print(f"\n¡TODOS LOS COLEGIOS ESTÁN EN SUPABASE!")