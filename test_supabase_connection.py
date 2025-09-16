#!/usr/bin/env python3
"""
Verificador y ejecutor de conexion Supabase
"""

import psycopg2
import time
from datetime import datetime

# Diferentes opciones de conexion para probar
connection_options = [
    # Opcion 1: Conexion directa con project ref
    "postgresql://postgres.ayuorfvindwywtltszdl:sb_secret_XrReuib_YbolzAOAecee-A_B86bGyqX@aws-0-us-west-1.pooler.supabase.com:6543/postgres",
    
    # Opcion 2: Conexion con formato estandar
    "postgresql://postgres:sb_secret_XrReuib_YbolzAOAecee-A_B86bGyqX@ayuorfvindwywtltszdl.supabase.co:5432/postgres",
    
    # Opcion 3: Conexion via pooler con diferentes formato
    "postgresql://postgres.juliaconfecciones:sb_secret_XrReuib_YbolzAOAecee-A_B86bGyqX@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
]

def test_connection(conn_string):
    """Probar una conexion especifica"""
    print(f"Probando conexion...")
    print(f"String: {conn_string[:50]}...")
    
    try:
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Probar consulta simple
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        print(f"OK: Conexion exitosa!")
        print(f"Version: {version[:50]}...")
        
        # Probar crear tabla simple
        test_sql = """
        CREATE TABLE IF NOT EXISTS test_connection (
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        INSERT INTO test_connection (id) VALUES (1)
        ON CONFLICT (id) DO UPDATE SET id = 1;
        """
        
        cursor.execute(test_sql)
        conn.commit()
        
        print("OK: Tabla de prueba creada correctamente")
        
        conn.close()
        return True, conn_string
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False, None

def create_basic_tables(conn_string):
    """Crear tablas basicas del sistema"""
    print("\nCreando tablas basicas...")
    
    try:
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Tablas esenciales
        tables = [
            # Colegios
            """
            CREATE TABLE IF NOT EXISTS colegios (
                id SERIAL PRIMARY KEY,
                codigo INTEGER NOT NULL UNIQUE,
                descripcion VARCHAR(255) NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """,
            
            # Productos
            """
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                codigo VARCHAR(50) UNIQUE NOT NULL,
                nombre VARCHAR(255) NOT NULL,
                precio_venta NUMERIC(12,2) NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """,
            
            # Variantes
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
            
            # Ventas
            """
            CREATE TABLE IF NOT EXISTS ventas (
                id SERIAL PRIMARY KEY,
                nro_documento INTEGER UNIQUE NOT NULL,
                cliente_nombre VARCHAR(255) NOT NULL,
                total NUMERIC(12,2) NOT NULL,
                fecha DATE NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        ]
        
        successful = 0
        for i, sql in enumerate(tables, 1):
            print(f"  Creando tabla {i}/{len(tables)}...")
            try:
                cursor.execute(sql)
                conn.commit()
                print(f"    OK: Tabla {i} creada")
                successful += 1
                time.sleep(0.2)
            except Exception as e:
                print(f"    ERROR: {e}")
                conn.rollback()
        
        conn.close()
        print(f"\nRESULTADO: {successful}/{len(tables)} tablas creadas")
        return successful == len(tables)
        
    except Exception as e:
        print(f"ERROR CRITICO: {e}")
        return False

def main():
    print("=" * 60)
    print("Julia Confecciones - Configuracion Supabase")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Probar diferentes opciones de conexion
    working_connection = None
    
    for i, conn_str in enumerate(connection_options, 1):
        print(f"\n--- Opcion {i} ---")
        success, working_str = test_connection(conn_str)
        
        if success:
            working_connection = working_str
            break
    
    if not working_connection:
        print("\n" + "=" * 60)
        print("ERROR CRITICO: Ninguna opcion de conexion funciono")
        print("Verifica:")
        print("1. Las credenciales de Supabase")
        print("2. El Project Ref: ayuorfvindwywtltszdl")
        print("3. El Service Role Key")
        print("=" * 60)
        return False
    
    print(f"\n" + "=" * 60)
    print("CONEXION EXITOSA ENCONTRADA")
    print(f"Usando: {working_connection}")
    print("=" * 60)
    
    # Crear tablas basicas
    if create_basic_tables(working_connection):
        print("\n" + "=" * 60)
        print("EXITO: Tablas basicas creadas correctamente")
        print("Proximo paso: Importar datos desde CSV")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("ERROR: No se pudieron crear todas las tablas")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)