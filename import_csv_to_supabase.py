#!/usr/bin/env python3
"""
Importador de datos desde CSV a Supabase
"""

import requests
import csv
import json
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
    
    # Convertir a string y limpiar
    value = str(value).strip()
    
    # Si es numérico pero viene como string
    try:
        if '.' in value:
            return float(value)
        else:
            return int(value)
    except:
        pass
    
    return value if value else None

def import_colegios():
    """Importar datos de colegios"""
    print("Importando colegios...")
    
    file_path = "access_export_Colegios.csv"
    if not Path(file_path).exists():
        print(f"  Archivo no encontrado: {file_path}")
        return False
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    url = f"{SUPABASE_URL}/rest/v1/colegios"
    imported = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                data = {
                    "codigo": clean_value(row['codigo']),
                    "descripcion": row['descripcion']
                }
                
                response = requests.post(url, headers=headers, json=data)
                
                if response.status_code in [200, 201, 409]:  # 409 = duplicate, which is OK
                    imported += 1
                    if imported % 10 == 0:
                        print(f"  Progreso: {imported} colegios importados")
                else:
                    print(f"  Error en colegio {row['codigo']}: {response.status_code}")
                    if response.text:
                        print(f"    {response.text[:100]}")
    
    except Exception as e:
        print(f"  Error leyendo archivo: {e}")
        return False
    
    print(f"  OK: Colegios importados: {imported}")
    return imported > 0

def import_productos():
    """Importar datos de productos"""
    print("\nImportando productos...")
    
    file_path = "access_export_productos.csv"
    if not Path(file_path).exists():
        print(f"  Archivo no encontrado: {file_path}")
        return False
    
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
                # Extraer talla de la descripción
                descripcion = row['descripcion']
                talla = None
                if 'Talla' in descripcion:
                    parts = descripcion.split('Talla')
                    if len(parts) > 1:
                        talla = parts[1].strip().split()[0]
                
                # Crear producto base (sin talla)
                nombre_base = descripcion.split('Talla')[0].strip()
                codigo_base = str(row['codigo']).split('.')[0]
                
                # Datos básicos del producto (sin colegio_id ya que no existe)
                data = {
                    "codigo": codigo_base,
                    "nombre": nombre_base,
                    "precio_venta": clean_value(row['Precio_venta']) or 0
                }
                
                response = requests.post(url, headers=headers, json=data)
                
                if response.status_code in [200, 201, 409]:
                    imported += 1
                    if imported % 20 == 0:
                        print(f"  Progreso: {imported} productos importados")
                else:
                    print(f"  Error en producto {codigo_base}: {response.status_code}")
                    if response.text:
                        print(f"    {response.text[:100]}")
    
    except Exception as e:
        print(f"  Error leyendo archivo: {e}")
        return False
    
    print(f"  OK: Productos importados: {imported}")
    return imported > 0

def import_ventas():
    """Importar datos de ventas"""
    print("\nImportando ventas...")
    
    file_path = "access_export_Ventas.csv"
    if not Path(file_path).exists():
        print(f"  Archivo no encontrado: {file_path}")
        return False
    
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
                # Saltar ventas sin nombre o con valores inválidos
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
                    if imported % 50 == 0:
                        print(f"  Progreso: {imported} ventas importadas")
                else:
                    print(f"  Error en venta {row['Nro_doc']}: {response.status_code}")
                    if response.text:
                        print(f"    {response.text[:100]}")
    
    except Exception as e:
        print(f"  Error leyendo archivo: {e}")
        return False
    
    print(f"  OK: Ventas importadas: {imported}")
    return imported > 0

def test_imported_data():
    """Probar datos importados"""
    print("\nVerificando datos importados...")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}"
    }
    
    tables = ["colegios", "productos", "ventas"]
    
    for table in tables:
        try:
            url = f"{SUPABASE_URL}/rest/v1/{table}?select=count"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                count = response.json()[0]['count'] if response.json() else 0
                print(f"  OK: {table}: {count} registros")
            else:
                print(f"  ERROR en {table}: {response.status_code}")
                
        except Exception as e:
            print(f"  ERROR verificando {table}: {e}")

def main():
    """Función principal"""
    print("=" * 60)
    print("Julia Confecciones - Importador de Datos")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success_count = 0
    
    # Importar datos
    if import_colegios():
        success_count += 1
    
    if import_productos():
        success_count += 1
    
    if import_ventas():
        success_count += 1
    
    # Verificar importación
    test_imported_data()
    
    print("\n" + "=" * 60)
    if success_count >= 2:
        print("EXITO: IMPORTACION COMPLETADA!")
        print("Datos básicos importados correctamente")
        print()
        print("Próximos pasos:")
        print("1. Verificar los datos en el dashboard de Supabase")
        print("2. Importar datos adicionales si es necesario")
        print("3. Configurar MedusaJS para la tienda online")
    else:
        print("AVISO: IMPORTACION PARCIAL")
        print("Algunos datos no se pudieron importar")
        print("Revisa los errores mostrados arriba")
    print("=" * 60)
    
    return success_count >= 2

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)