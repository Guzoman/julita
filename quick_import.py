#!/usr/bin/env python3
"""
Importador rápido solo de productos y ventas
"""

import requests
import csv
import time
from datetime import datetime
from pathlib import Path

# Configuración de Supabase
SUPABASE_URL = "https://ayuorfvindwywtltszdl.supabase.co"
SUPABASE_KEY = "sb_secret_XrReuib_YbolzAOAecee-A_B86bGyqX"
SERVICE_ROLE_KEY = "sb_secret_XrReuib_YbolzAOAecee-A_B86bGyqX"

def clean_value(value):
    """Limpiar valores del CSV"""
    if value is None or value == '':
        return None
    
    value = str(value).strip()
    
    try:
        if '.' in value:
            return float(value)
        else:
            return int(value)
    except:
        pass
    
    return value if value else None

def import_productos():
    """Importar datos de productos"""
    print("Importando productos...")
    
    file_path = "access_export_productos.csv"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    url = f"{SUPABASE_URL}/rest/v1/productos"
    imported = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                descripcion = row['descripcion']
                nombre_base = descripcion.split('Talla')[0].strip()
                codigo_base = str(row['codigo']).split('.')[0]
                
                data = {
                    "codigo": codigo_base,
                    "nombre": nombre_base,
                    "precio_venta": clean_value(row['Precio_venta']) or 0
                }
                
                response = requests.post(url, headers=headers, json=data)
                
                if response.status_code in [200, 201, 409]:
                    imported += 1
                    if imported % 50 == 0:
                        print(f"  Progreso: {imported} productos")
                else:
                    print(f"  Error {codigo_base}: {response.status_code}")
    
    except Exception as e:
        print(f"  Error: {e}")
        return False
    
    print(f"  OK: {imported} productos importados")
    return imported > 0

def import_ventas():
    """Importar datos de ventas"""
    print("\nImportando ventas...")
    
    file_path = "access_export_Ventas.csv"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    url = f"{SUPABASE_URL}/rest/v1/ventas"
    imported = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                if not row['Nombre'] or row['Nombre'] == '':
                    continue
                
                data = {
                    "nro_documento": clean_value(row['Nro_doc']),
                    "cliente_nombre": row['Nombre'],
                    "total": clean_value(row['Total']) or 0,
                    "fecha": row['Fecha'].split()[0] if ' ' in row['Fecha'] else row['Fecha']
                }
                
                response = requests.post(url, headers=headers, json=data)
                
                if response.status_code in [200, 201, 409]:
                    imported += 1
                    if imported % 100 == 0:
                        print(f"  Progreso: {imported} ventas")
                else:
                    print(f"  Error venta {row['Nro_doc']}: {response.status_code}")
    
    except Exception as e:
        print(f"  Error: {e}")
        return False
    
    print(f"  OK: {imported} ventas importadas")
    return imported > 0

def main():
    print("=" * 50)
    print("Importación Rápida - Productos y Ventas")
    print("=" * 50)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = 0
    
    if import_productos():
        success += 1
        time.sleep(1)
    
    if import_ventas():
        success += 1
    
    print("\n" + "=" * 50)
    if success == 2:
        print("EXITO: Importación completada")
    else:
        print("AVISO: Importación parcial")
    print("=" * 50)
    
    return success == 2

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)