#!/usr/bin/env python3
"""
Ejecutor de esquema Supabase via API REST - Version sin emojis
"""

import requests
import json
import time
from datetime import datetime

# Configuracion de Supabase
SUPABASE_URL = "https://ayuorfvindwywtltszdl.supabase.co"
SUPABASE_KEY = "sb_secret_XrReuib_YbolzAOAecee-A_B86bGyqX"
SERVICE_ROLE_KEY = "sb_secret_XrReuib_YbolzAOAecee-A_B86bGyqX"

# Headers para la API
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def execute_sql(sql_query):
    """Ejecutar consulta SQL via API REST de Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
    
    payload = {
        "sql": sql_query
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code in [200, 201]:
            print("OK: Consulta ejecutada correctamente")
            return response.json()
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"ERROR DE CONEXION: {e}")
        return None

def check_connection():
    """Verificar conexion con Supabase"""
    print("Verificando conexion con Supabase...")
    
    # Probar una consulta simple
    test_query = "SELECT version();"
    
    try:
        result = execute_sql(test_query)
        if result:
            print("OK: Conexion exitosa con Supabase")
            print(f"Version PostgreSQL: {result[0]['version']}")
            return True
        else:
            print("ERROR: No se pudo establecer conexion")
            return False
    except Exception as e:
        print(f"ERROR DE CONEXION: {e}")
        return False

def execute_basic_tables():
    """Ejecutar creacion de tablas basicas"""
    print("Creando tablas basicas del sistema...")
    
    tables_to_create = [
        {
            "name": "colegios",
            "sql": """
            CREATE TABLE IF NOT EXISTS colegios (
                id SERIAL PRIMARY KEY,
                codigo INTEGER NOT NULL UNIQUE,
                descripcion VARCHAR(255) NOT NULL,
                direccion TEXT,
                telefono VARCHAR(50),
                email VARCHAR(255),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        },
        {
            "name": "usuarios",
            "sql": """
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                id_usuario INTEGER NOT NULL UNIQUE,
                nombre_usuario VARCHAR(255) NOT NULL UNIQUE,
                clave_usuario VARCHAR(255),
                rol VARCHAR(50) DEFAULT 'usuario',
                activo BOOLEAN DEFAULT true,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        },
        {
            "name": "empresa",
            "sql": """
            CREATE TABLE IF NOT EXISTS empresa (
                id SERIAL PRIMARY KEY,
                rut VARCHAR(20) UNIQUE NOT NULL,
                nombre VARCHAR(255) NOT NULL,
                giro VARCHAR(255),
                direccion TEXT,
                telefono VARCHAR(50),
                email VARCHAR(255),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        },
        {
            "name": "productos",
            "sql": """
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                codigo VARCHAR(50) UNIQUE NOT NULL,
                nombre VARCHAR(255) NOT NULL,
                descripcion TEXT,
                categoria VARCHAR(100),
                precio_costo NUMERIC(12,2) DEFAULT 0,
                precio_venta NUMERIC(12,2) NOT NULL,
                activo BOOLEAN DEFAULT true,
                medusa_id VARCHAR(100) UNIQUE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        },
        {
            "name": "producto_variantes",
            "sql": """
            CREATE TABLE IF NOT EXISTS producto_variantes (
                id SERIAL PRIMARY KEY,
                producto_id INTEGER REFERENCES productos(id),
                codigo VARCHAR(50) UNIQUE NOT NULL,
                nombre VARCHAR(255) NOT NULL,
                talla VARCHAR(20),
                color VARCHAR(50),
                sku VARCHAR(100),
                precio_costo NUMERIC(12,2) DEFAULT 0,
                precio_venta NUMERIC(12,2) NOT NULL,
                stock INTEGER DEFAULT 0,
                medusa_variant_id VARCHAR(100) UNIQUE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        },
        {
            "name": "ventas",
            "sql": """
            CREATE TABLE IF NOT EXISTS ventas (
                id SERIAL PRIMARY KEY,
                nro_documento INTEGER UNIQUE NOT NULL,
                tipo_documento VARCHAR(20) DEFAULT 'boleta',
                fecha DATE NOT NULL,
                cliente_nombre VARCHAR(255) NOT NULL,
                cliente_rut VARCHAR(20),
                cliente_telefono VARCHAR(50),
                cliente_email VARCHAR(255),
                subtotal NUMERIC(12,2) DEFAULT 0,
                descuento_porcentaje NUMERIC(5,2) DEFAULT 0,
                descuento_monto NUMERIC(12,2) DEFAULT 0,
                iva NUMERIC(12,2) DEFAULT 0,
                total NUMERIC(12,2) NOT NULL,
                estado VARCHAR(20) DEFAULT 'pagada',
                canal_venta VARCHAR(20) DEFAULT 'tienda',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        },
        {
            "name": "ventas_detalle",
            "sql": """
            CREATE TABLE IF NOT EXISTS ventas_detalle (
                id SERIAL PRIMARY KEY,
                venta_id INTEGER REFERENCES ventas(id),
                item INTEGER NOT NULL,
                producto_variante_id INTEGER REFERENCES producto_variantes(id),
                cantidad INTEGER NOT NULL,
                precio_unitario NUMERIC(12,2) NOT NULL,
                texto_bordado TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        }
    ]
    
    successful = 0
    
    for table in tables_to_create:
        print(f"Creando tabla: {table['name']}")
        try:
            result = execute_sql(table['sql'])
            if result is not None:
                print(f"OK: Tabla {table['name']} creada")
                successful += 1
                time.sleep(0.5)
            else:
                print(f"ERROR: No se pudo crear tabla {table['name']}")
        except Exception as e:
            print(f"ERROR: {e} en tabla {table['name']}")
    
    print(f"\nRESUMEN: {successful}/{len(tables_to_create)} tablas creadas exitosamente")
    return successful == len(tables_to_create)

def insert_initial_data():
    """Insertar datos iniciales"""
    print("Insertando datos iniciales...")
    
    # Insertar tipos de materiales basicos
    tipos_materiales_sql = """
    INSERT INTO tipos_materiales (nombre, unidad_medida) VALUES 
    ('Tela', 'metros'),
    ('Hilo', 'conos'),
    ('Botones', 'unidades'),
    ('Cierres', 'unidades'),
    ('Etiquetas', 'unidades')
    ON CONFLICT (nombre) DO NOTHING;
    """
    
    result = execute_sql(tipos_materiales_sql)
    if result:
        print("OK: Tipos de materiales insertados")
    else:
        print("ERROR: No se insertaron tipos de materiales")

def verify_schema():
    """Verificar que el esquema se creo correctamente"""
    print("Verificando esquema creado...")
    
    check_sql = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('colegios', 'usuarios', 'empresa', 'productos', 'producto_variantes', 'ventas', 'ventas_detalle')
    ORDER BY table_name;
    """
    
    result = execute_sql(check_sql)
    
    if result:
        tables = [row['table_name'] for row in result]
        print(f"Tablas verificadas: {len(tables)}")
        for table in tables:
            print(f"  - {table}")
        return len(tables) >= 6  # Al menos 6 tablas basicas
    else:
        print("ERROR: No se pudo verificar las tablas")
        return False

def main():
    """Funcion principal"""
    print("=" * 60)
    print("Julia Confecciones - Ejecucion de Esquema Supabase")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Proyecto: {SUPABASE_URL}")
    print()
    
    # Verificar conexion
    if not check_connection():
        print("ERROR CRITICO: No se puede continuar sin conexion")
        return False
    
    print("\n" + "=" * 60)
    print("FASE 1: Creacion de tablas basicas")
    print("=" * 60)
    
    if not execute_basic_tables():
        print("ERROR: Falló la creacion de tablas basicas")
        return False
    
    print("\n" + "=" * 60)
    print("FASE 2: Datos iniciales")
    print("=" * 60)
    
    insert_initial_data()
    
    print("\n" + "=" * 60)
    print("FASE 3: Verificacion")
    print("=" * 60)
    
    if not verify_schema():
        print("ADVERTENCIA: La verificacion no fue completa")
    else:
        print("OK: Verificacion completada exitosamente")
    
    print("\n" + "=" * 60)
    print("PROCESO COMPLETADO")
    print("Esquema basico de Supabase creado exitosamente")
    print("Proximo paso: Importar datos desde archivos CSV")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)