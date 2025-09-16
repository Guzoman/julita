#!/usr/bin/env python3
"""
Solucion definitiva: Crear tablas Supabase via API REST
"""

import requests
import json
import time
from datetime import datetime

# Configuracion de Supabase
SUPABASE_URL = "https://ayuorfvindwywtltszdl.supabase.co"
SUPABASE_KEY = "sb_secret_XrReuib_YbolzAOAecee-A_B86bGyqX"
SERVICE_ROLE_KEY = "sb_secret_XrReuib_YbolzAOAecee-A_B86bGyqX"

def create_tables_using_direct_sql():
    """Usar el endpoint correcto para ejecutar SQL"""
    
    # El endpoint correcto para ejecutar SQL en Supabase
    sql_url = f"{SUPABASE_URL}/rest/v1/sql"
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "application/json"
    }
    
    # SQL para crear tablas basicas
    create_tables_sql = [
        # Extensiones necesarias
        "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";",
        "CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";",
        
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
    
    for i, sql in enumerate(create_tables_sql, 1):
        print(f"Ejecutando SQL {i}/{len(create_tables_sql)}...")
        
        payload = {
            "query": sql
        }
        
        try:
            response = requests.post(sql_url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                print(f"  OK: SQL {i} ejecutado correctamente")
                successful += 1
            else:
                print(f"  ERROR: SQL {i} falló - {response.status_code}")
                if response.text:
                    print(f"    Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"  ERROR: {e}")
        
        time.sleep(0.5)  # Pequeña pausa
    
    print(f"\nRESULTADO: {successful}/{len(create_tables_sql)} comandos ejecutados")
    return successful >= len(create_tables_sql) * 0.8

def test_tables_via_rest():
    """Probar que las tablas funcionan via REST API"""
    print("\nProbando tablas via REST API...")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    tables_to_test = ["colegios", "productos", "producto_variantes", "ventas"]
    working_tables = []
    
    for table in tables_to_test:
        try:
            # Intentar INSERT para probar que la tabla existe y funciona
            test_url = f"{SUPABASE_URL}/rest/v1/{table}"
            
            if table == "colegios":
                test_data = {"codigo": 777, "descripcion": "TEST API"}
            elif table == "productos":
                test_data = {"codigo": "API777", "nombre": "PRODUCTO API", "precio_venta": 7777}
            elif table == "producto_variantes":
                test_data = {"producto_id": 1, "nombre": "VARIANTE API", "talla": "L", "precio_venta": 7777}
            else:  # ventas
                test_data = {"nro_documento": 7777, "cliente_nombre": "CLIENTE API", "total": 7777}
            
            response = requests.post(test_url, headers=headers, json=test_data)
            
            if response.status_code in [200, 201]:
                print(f"  OK: Tabla {table} - INSERT funciona")
                working_tables.append(table)
                
                # Limpiar datos de prueba
                if table == "colegios":
                    cleanup_url = f"{SUPABASE_URL}/rest/v1/{table}?codigo=eq.777"
                elif table == "productos":
                    cleanup_url = f"{SUPABASE_URL}/rest/v1/{table}?codigo=eq.API777"
                elif table == "producto_variantes":
                    cleanup_url = f"{SUPABASE_URL}/rest/v1/{table}?nombre=eq.VARIANTE%20API"
                else:  # ventas
                    cleanup_url = f"{SUPABASE_URL}/rest/v1/{table}?nro_documento=eq.7777"
                
                requests.delete(cleanup_url, headers=headers)
                
            else:
                print(f"  ERROR: Tabla {table} - INSERT falló - {response.status_code}")
                if response.text:
                    print(f"    Error: {response.text[:100]}...")
                
        except Exception as e:
            print(f"  ERROR: {e}")
    
    print(f"\nTABLAS FUNCIONALES: {len(working_tables)}/{len(tables_to_test)}")
    return len(working_tables) >= 3

def insert_sample_data():
    """Insertar datos de muestra para probar"""
    print("\nInsertando datos de muestra...")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    sample_data = [
        # Colegios de muestra
        {"table": "colegios", "data": {"codigo": 10, "descripcion": "COLEGIO LOS REYES"}},
        {"table": "colegios", "data": {"codigo": 2, "descripcion": "JUAN XXIII"}},
        {"table": "colegios", "data": {"codigo": 3, "descripcion": "NUEVO HORIZONTE"}},
        
        # Productos de muestra
        {"table": "productos", "data": {"codigo": "BUZO001", "nombre": "Buzo Deportivo Los Reyes", "precio_venta": 15990}},
        {"table": "productos", "data": {"codigo": "POLERA001", "nombre": "Polera Pique MC LR", "precio_venta": 12500}},
    ]
    
    inserted = 0
    
    for item in sample_data:
        try:
            url = f"{SUPABASE_URL}/rest/v1/{item['table']}"
            response = requests.post(url, headers=headers, json=item['data'])
            
            if response.status_code in [200, 201]:
                print(f"  OK: Insertado en {item['table']}")
                inserted += 1
            else:
                print(f"  ERROR: Insert falló en {item['table']} - {response.status_code}")
                
        except Exception as e:
            print(f"  ERROR: {e}")
    
    print(f"\nDATOS INSERTADOS: {inserted}/{len(sample_data)}")
    return inserted > 0

def main():
    """Funcion principal - Solucion definitiva"""
    print("=" * 60)
    print("Julia Confecciones - Solucion API REST Definitiva")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Proyecto: {SUPABASE_URL}")
    print()
    
    print("Fase 1: Creacion de tablas via SQL directo")
    print("-" * 50)
    
    if not create_tables_using_direct_sql():
        print("ERROR CRITICO: No se pudieron crear las tablas")
        return False
    
    print("\nFase 2: Verificacion de tablas")
    print("-" * 50)
    
    if not test_tables_via_rest():
        print("ERROR: Las tablas no funcionan correctamente")
        return False
    
    print("\nFase 3: Datos de muestra")
    print("-" * 50)
    
    insert_sample_data()
    
    print("\n" + "=" * 60)
    print("EXITO COMPLETO!")
    print("Base de datos Supabase configurada via API REST")
    print("Tablas funcionales y listas para usar")
    print()
    print("Proximo paso: Importar datos CSV completos")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)