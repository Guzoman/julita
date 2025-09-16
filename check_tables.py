#!/usr/bin/env python3
"""
Verificar estructura de tablas en Supabase
"""

import requests
import json
from datetime import datetime

# Configuración de Supabase
SUPABASE_URL = "https://ayuorfvindwywtltszdl.supabase.co"
SUPABASE_KEY = "sb_secret_XrReuib_YbolzAOAecee-A_B86bGyqX"
SERVICE_ROLE_KEY = "sb_secret_XrReuib_YbolzAOAecee-A_B86bGyqX"

def check_table_structure(table_name):
    """Verificar estructura de una tabla"""
    print(f"\nVerificando tabla: {table_name}")
    print("-" * 40)
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}"
    }
    
    # Intentar obtener un registro para ver la estructura
    url = f"{SUPABASE_URL}/rest/v1/{table_name}?limit=1"
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                print("Columnas encontradas:")
                for key, value in data[0].items():
                    print(f"  - {key}: {type(value).__name__} = {value}")
            else:
                print("Tabla existe pero está vacía")
        else:
            print(f"Error: {response.status_code}")
            if response.text:
                print(f"Detalle: {response.text[:200]}")
                
    except Exception as e:
        print(f"Error: {e}")

def check_all_tables():
    """Verificar todas las tablas principales"""
    tables = ["colegios", "productos", "ventas", "producto_variantes"]
    
    print("=" * 60)
    print("Verificación de Estructura de Tablas")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Proyecto: {SUPABASE_URL}")
    print()
    
    for table in tables:
        check_table_structure(table)
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_all_tables()