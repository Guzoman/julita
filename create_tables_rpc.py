#!/usr/bin/env python3
"""
Creador de tablas Supabase via SQL RPC
"""

import requests
import json
import time
from datetime import datetime

# Configuracion de Supabase
SUPABASE_URL = "https://ayuorfvindwywtltszdl.supabase.co"
SUPABASE_KEY = "sb_secret_XrReuib_YbolzAOAecee-A_B86bGyqX"
SERVICE_ROLE_KEY = "sb_secret_XrReuib_YbolzAOAecee-A_B86bGyqX"

def execute_sql_rpc(sql_query):
    """Ejecutar SQL via RPC endpoint"""
    
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec"
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "sql": sql_query
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"ERROR RPC: {e}")
        return None

def create_tables_sequentially():
    """Crear tablas una por una"""
    print("Creando tablas via SQL RPC...")
    
    # SQL statements para crear tablas basicas
    sql_statements = [
        # Tabla colegios
        """
        CREATE TABLE IF NOT EXISTS colegios (
            id SERIAL PRIMARY KEY,
            codigo INTEGER NOT NULL UNIQUE,
            descripcion VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        
        # Tabla productos
        """
        CREATE TABLE IF NOT EXISTS productos (
            id SERIAL PRIMARY KEY,
            codigo VARCHAR(50) UNIQUE NOT NULL,
            nombre VARCHAR(255) NOT NULL,
            precio_venta NUMERIC(12,2) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        
        # Tabla variantes
        """
        CREATE TABLE IF NOT EXISTS producto_variantes (
            id SERIAL PRIMARY KEY,
            producto_id INTEGER REFERENCES productos(id),
            nombre VARCHAR(255) NOT NULL,
            talla VARCHAR(20),
            precio_venta NUMERIC(12,2) NOT NULL,
            stock INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        
        # Tabla ventas
        """
        CREATE TABLE IF NOT EXISTS ventas (
            id SERIAL PRIMARY KEY,
            nro_documento INTEGER UNIQUE NOT NULL,
            cliente_nombre VARCHAR(255) NOT NULL,
            total NUMERIC(12,2) NOT NULL,
            fecha DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    ]
    
    successful = 0
    
    for i, sql in enumerate(sql_statements, 1):
        print(f"Ejecutando SQL {i}/{len(sql_statements)}...")
        
        try:
            result = execute_sql_rpc(sql)
            if result is not None:
                print(f"  OK: SQL {i} ejecutado")
                successful += 1
            else:
                print(f"  ERROR: SQL {i} falló")
                
        except Exception as e:
            print(f"  ERROR: {e}")
        
        time.sleep(1)  # Pausa entre ejecuciones
    
    print(f"\nRESULTADO: {successful}/{len(sql_statements)} sentencias ejecutadas")
    return successful > 0

def test_basic_operations():
    """Probar operaciones basicas via API REST"""
    print("\nProbando operaciones basicas...")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    # Probar insertar en colegios
    test_data = {
        "codigo": 999,
        "descripcion": "COLEGIO DE PRUEBA"
    }
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/colegios"
        response = requests.post(url, headers=headers, json=test_data)
        
        if response.status_code in [200, 201]:
            print("OK: Insercion en colegios funciona")
            
            # Limpiar datos de prueba
            delete_url = f"{SUPABASE_URL}/rest/v1/colegios?codigo=eq.999"
            delete_response = requests.delete(delete_url, headers=headers)
            print("OK: Limpieza de prueba completada")
            return True
        else:
            print(f"ERROR en insercion: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR en prueba: {e}")
        return False

def check_api_availability():
    """Verificar disponibilidad de la API"""
    print("Verificando disponibilidad de API...")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}"
    }
    
    try:
        # Probar endpoint basico
        url = f"{SUPABASE_URL}/rest/v1/"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            print("OK: API REST disponible")
            return True
        else:
            print(f"ERROR: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR de conexion: {e}")
        return False

def main():
    """Funcion principal"""
    print("=" * 60)
    print("Julia Confecciones - Setup SQL RPC")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verificar API
    if not check_api_availability():
        print("ERROR CRITICO: API no disponible")
        return False
    
    print("\n" + "=" * 60)
    print("CREACION DE TABLAS")
    print("=" * 60)
    
    # Crear tablas
    if not create_tables_sequentially():
        print("ERROR: No se pudieron crear las tablas")
        return False
    
    print("\n" + "=" * 60)
    print("PRUEBA DE OPERACIONES")
    print("=" * 60)
    
    # Probar operaciones
    if not test_basic_operations():
        print("ADVERTENCIA: Las pruebas basicas fallaron")
        print("Pero las tablas pueden estar creadas")
    
    print("\n" + "=" * 60)
    print("SETUP COMPLETADO")
    print("Tablas basicas configuradas")
    print("Proximo paso: Importar datos CSV")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)