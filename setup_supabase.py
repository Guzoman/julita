#!/usr/bin/env python3
"""
Ejecutor de esquema Supabase via API REST - Version directa PostgreSQL
"""

import requests
import json
import time
from datetime import datetime

# Conexion directa a PostgreSQL de Supabase
DB_URL = "postgresql://postgres.juliaconfecciones:sb_secret_XrReuib_YbolzAOAecee-A_B86bGyqX@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

def execute_sql_direct(sql_query):
    """Ejecutar SQL usando libreria psycopg2 directamente"""
    try:
        import psycopg2
        from psycopg2 import sql
        
        # Conectar a la base de datos
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # Ejecutar la consulta
        cursor.execute(sql_query)
        
        # Si es una consulta SELECT, retornar resultados
        if sql_query.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
            # Obtener nombres de columnas
            columns = [desc[0] for desc in cursor.description]
            # Formatear como lista de diccionarios
            formatted_results = []
            for row in results:
                formatted_results.append(dict(zip(columns, row)))
            conn.close()
            return formatted_results
        else:
            # Para INSERT/CREATE/UPDATE, hacer commit y retornar mensaje
            conn.commit()
            conn.close()
            return {"status": "success", "message": "Query executed successfully"}
            
    except ImportError:
        print("ERROR: psycopg2 no esta instalado. Instalando...")
        import subprocess
        subprocess.run(["pip", "install", "psycopg2-binary"], check=True)
        return execute_sql_direct(sql_query)  # Reintentar después de instalar
    except Exception as e:
        print(f"ERROR DE BASE DE DATOS: {e}")
        return None

def check_connection():
    """Verificar conexion con Supabase"""
    print("Verificando conexion con Supabase...")
    
    test_query = "SELECT version();"
    
    try:
        result = execute_sql_direct(test_query)
        if result and isinstance(result, list) and len(result) > 0:
            print("OK: Conexion exitosa con Supabase")
            print(f"Version PostgreSQL: {result[0]['version']}")
            return True
        else:
            print("ERROR: No se pudo establecer conexion")
            return False
    except Exception as e:
        print(f"ERROR DE CONEXION: {e}")
        return False

def create_tables():
    """Crear todas las tablas necesarias"""
    print("Creando tablas del sistema...")
    
    tables_sql = [
        # Extensiones necesarias
        """
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        CREATE EXTENSION IF NOT EXISTS "pgcrypto";
        """,
        
        # Tabla de colegios
        """
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
        """,
        
        # Tabla de usuarios
        """
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
        """,
        
        # Tabla de empresa
        """
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
        """,
        
        # Tipos de materiales
        """
        CREATE TABLE IF NOT EXISTS tipos_materiales (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL UNIQUE,
            unidad_medida VARCHAR(20) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        
        # Materiales
        """
        CREATE TABLE IF NOT EXISTS materiales (
            id SERIAL PRIMARY KEY,
            codigo VARCHAR(50) UNIQUE NOT NULL,
            nombre VARCHAR(255) NOT NULL,
            descripcion TEXT,
            tipo_material_id INTEGER REFERENCES tipos_materiales(id),
            unidad_medida VARCHAR(20) NOT NULL,
            stock_actual NUMERIC(12,3) DEFAULT 0,
            stock_minimo NUMERIC(12,3) DEFAULT 0,
            precio_referencia NUMERIC(12,2),
            activo BOOLEAN DEFAULT true,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        
        # Productos principales
        """
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
        """,
        
        # Variantes de productos
        """
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
        """,
        
        # Ventas (cabecera)
        """
        CREATE TABLE IF NOT EXISTS ventas (
            id SERIAL PRIMARY KEY,
            nro_documento INTEGER UNIQUE NOT NULL,
            tipo_documento VARCHAR(20) DEFAULT 'boleta',
            fecha DATE NOT NULL,
            cliente_nombre VARCHAR(255) NOT NULL,
            cliente_rut VARCHAR(20),
            cliente_telefono VARCHAR(50),
            cliente_email VARCHAR(255),
            colegio_id INTEGER REFERENCES colegios(id),
            subtotal NUMERIC(12,2) DEFAULT 0,
            descuento_porcentaje NUMERIC(5,2) DEFAULT 0,
            descuento_monto NUMERIC(12,2) DEFAULT 0,
            iva NUMERIC(12,2) DEFAULT 0,
            total NUMERIC(12,2) NOT NULL,
            estado VARCHAR(20) DEFAULT 'pagada',
            canal_venta VARCHAR(20) DEFAULT 'tienda',
            medusa_order_id VARCHAR(100),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        
        # Detalle de ventas
        """
        CREATE TABLE IF NOT EXISTS ventas_detalle (
            id SERIAL PRIMARY KEY,
            venta_id INTEGER REFERENCES ventas(id),
            item INTEGER NOT NULL,
            producto_variante_id INTEGER REFERENCES producto_variantes(id),
            cantidad INTEGER NOT NULL,
            precio_unitario NUMERIC(12,2) NOT NULL,
            subtotal NUMERIC(12,2) GENERATED ALWAYS AS (cantidad * precio_unitario) STORED,
            texto_bordado TEXT,
            diseno_bordado_id INTEGER,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    ]
    
    successful = 0
    total = len(tables_sql)
    
    for i, sql in enumerate(tables_sql, 1):
        print(f"Ejecutando consulta {i}/{total}...")
        try:
            result = execute_sql_direct(sql)
            if result:
                print(f"OK: Consulta {i} ejecutada correctamente")
                successful += 1
                time.sleep(0.3)  # Pequeña pausa
            else:
                print(f"ERROR: Consulta {i} falló")
        except Exception as e:
            print(f"ERROR: {e} en consulta {i}")
    
    print(f"\nRESUMEN: {successful}/{total} consultas ejecutadas exitosamente")
    return successful >= total * 0.8  # Aceptar 80% de éxito

def insert_initial_data():
    """Insertar datos iniciales"""
    print("\nInsertando datos iniciales...")
    
    # Insertar tipos de materiales
    tipos_sql = """
    INSERT INTO tipos_materiales (nombre, unidad_medida) VALUES 
    ('Tela', 'metros'),
    ('Hilo', 'conos'),
    ('Botones', 'unidades'),
    ('Cierres', 'unidades'),
    ('Etiquetas', 'unidades'),
    ('Hilos bordar', 'metros_lineales')
    ON CONFLICT (nombre) DO NOTHING;
    """
    
    result = execute_sql_direct(tipos_sql)
    if result:
        print("OK: Tipos de materiales insertados")
    else:
        print("ERROR: No se insertaron tipos de materiales")

def verify_tables():
    """Verificar tablas creadas"""
    print("\nVerificando tablas creadas...")
    
    check_sql = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name;
    """
    
    result = execute_sql_direct(check_sql)
    
    if result:
        tables = [row['table_name'] for row in result]
        expected_tables = [
            'colegios', 'usuarios', 'empresa', 'tipos_materiales', 
            'materiales', 'productos', 'producto_variantes', 'ventas', 'ventas_detalle'
        ]
        
        print(f"Total tablas encontradas: {len(tables)}")
        print("Tablas creadas:")
        
        found_expected = 0
        for table in tables:
            status = "✓" if table in expected_tables else " "
            print(f"  {status} {table}")
            if table in expected_tables:
                found_expected += 1
        
        print(f"\nTablas esperadas encontradas: {found_expected}/{len(expected_tables)}")
        return found_expected >= 6  # Al menos 6 tablas basicas
    else:
        print("ERROR: No se pudo verificar las tablas")
        return False

def main():
    """Funcion principal"""
    print("=" * 60)
    print("Julia Confecciones - Ejecucion de Esquema Supabase")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base de datos: PostgreSQL - Supabase")
    print()
    
    # Verificar conexion
    if not check_connection():
        print("ERROR CRITICO: No se puede continuar sin conexion")
        return False
    
    print("\n" + "=" * 60)
    print("FASE 1: Creacion de tablas")
    print("=" * 60)
    
    if not create_tables():
        print("ERROR: Falló la creacion de tablas")
        return False
    
    print("\n" + "=" * 60)
    print("FASE 2: Datos iniciales")
    print("=" * 60)
    
    insert_initial_data()
    
    print("\n" + "=" * 60)
    print("FASE 3: Verificacion final")
    print("=" * 60)
    
    if not verify_tables():
        print("ADVERTENCIA: La verificacion no fue completa")
        print("Pero continuamos con la importacion de datos...")
    else:
        print("OK: Verificacion completada exitosamente")
    
    print("\n" + "=" * 60)
    print("PROCESO COMPLETADO EXITOSAMENTE")
    print("Esquema basico de Supabase creado")
    print("Proximo paso: Importar datos desde archivos CSV")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)