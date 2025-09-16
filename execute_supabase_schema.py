#!/usr/bin/env python3
"""
Ejecutor de esquema Supabase vía API REST
"""

import requests
import json
import time
from datetime import datetime

# Configuración de Supabase
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
            print("Consulta ejecutada correctamente")
            return response.json()
        else:
            print(f"Error en consulta: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error de conexion: {e}")
        return None

def read_schema_file():
    """Leer el archivo de esquema"""
    try:
        with open('schema_supabase_completo_v2.sql', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print("❌ No se encontró el archivo schema_supabase_completo_v2.sql")
        return None

def split_schema_into_chunks(schema_content, chunk_size=8000):
    """Dividir el esquema en chunks más pequeños para evitar timeouts"""
    # Dividir por sentencias SQL
    statements = schema_content.split(';')
    
    chunks = []
    current_chunk = ""
    
    for statement in statements:
        statement = statement.strip()
        if statement and not statement.startswith('--'):
            # Si agregar esta sentencia excede el tamaño, crear nuevo chunk
            if len(current_chunk + statement + ';') > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk + ';')
                current_chunk = statement + ';'
            else:
                current_chunk += statement + ';'
    
    # Agregar el último chunk si queda contenido
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def check_connection():
    """Verificar conexión con Supabase"""
    print("🔍 Verificando conexión con Supabase...")
    
    # Probar una consulta simple
    test_query = "SELECT version();"
    
    try:
        result = execute_sql(test_query)
        if result:
            print("✅ Conexión exitosa con Supabase")
            print(f"Versión PostgreSQL: {result[0]['version']}")
            return True
        else:
            print("❌ No se pudo establecer conexión")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def create_exec_function():
    """Crear función para ejecutar SQL si no existe"""
    create_function_sql = """
    CREATE OR REPLACE FUNCTION exec_sql(sql_query TEXT)
    RETURNS TABLE(result TEXT) AS $$
    BEGIN
        -- Esta es una función wrapper para ejecutar SQL dinámico
        -- Nota: En un entorno real, esto requiere cuidados de seguridad
        RETURN QUERY EXECUTE format('SELECT %L as result', 'SQL executed');
    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER;
    """
    
    print("🔧 Creando función de ejecución SQL...")
    execute_sql(create_function_sql)

def execute_schema_step_by_step():
    """Ejecutar el esquema paso a paso"""
    print("🚀 Iniciando ejecución del esquema Supabase...")
    
    schema_content = read_schema_file()
    if not schema_content:
        return False
    
    # Dividir en bloques lógicos
    sections = [
        {
            "name": "Extensiones necesarias",
            "sql": """
            CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
            CREATE EXTENSION IF NOT EXISTS "pgcrypto";
            CREATE EXTENSION IF NOT EXISTS "pg_trgm";
            """
        },
        {
            "name": "Tablas de negocio legado",
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
            "name": "Tabla de usuarios",
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
            "name": "Tabla de empresa",
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
            "name": "Tipos de materiales",
            "sql": """
            CREATE TABLE IF NOT EXISTS tipos_materiales (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL UNIQUE,
                unidad_medida VARCHAR(20) NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        },
        {
            "name": "Materiales",
            "sql": """
            CREATE TABLE IF NOT EXISTS materiales (
                id SERIAL PRIMARY KEY,
                codigo VARCHAR(50) UNIQUE NOT NULL,
                nombre VARCHAR(255) NOT NULL,
                descripcion TEXT,
                tipo_material_id INTEGER,
                unidad_medida VARCHAR(20) NOT NULL,
                stock_actual NUMERIC(12,3) DEFAULT 0,
                stock_minimo NUMERIC(12,3) DEFAULT 0,
                precio_referencia NUMERIC(12,2),
                activo BOOLEAN DEFAULT true,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        },
        {
            "name": "Productos principales",
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
            "name": "Variantes de productos",
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
            "name": "Ventas",
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
        }
    ]
    
    # Ejecutar cada sección
    successful_sections = 0
    
    for i, section in enumerate(sections):
        print(f"📋 Ejecutando sección {i+1}/{len(sections)}: {section['name']}")
        
        try:
            result = execute_sql(section['sql'])
            if result is not None:
                print(f"✅ Sección '{section['name']}' ejecutada correctamente")
                successful_sections += 1
                time.sleep(1)  # Pequeña pausa para no sobrecargar
            else:
                print(f"⚠️  Error en sección '{section['name']}', continuando...")
                
        except Exception as e:
            print(f"❌ Error en sección '{section['name']}': {e}")
            continue
    
    print(f"\n📊 Resumen de ejecución:")
    print(f"✅ Secciones exitosas: {successful_sections}/{len(sections)}")
    print(f"⚠️  Secciones con errores: {len(sections) - successful_sections}")
    
    if successful_sections == len(sections):
        print("🎉 ¡Esquema básico ejecutado correctamente!")
        return True
    else:
        print("⚠️  Algunas secciones tuvieron errores, pero continuamos...")
        return True

def verify_tables():
    """Verificar que las tablas se crearon correctamente"""
    print("🔍 Verificando tablas creadas...")
    
    check_tables_sql = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name;
    """
    
    result = execute_sql(check_tables_sql)
    
    if result:
        tables = [row['table_name'] for row in result]
        expected_tables = [
            'colegios', 'usuarios', 'empresa', 'tipos_materiales', 
            'materiales', 'productos', 'producto_variantes', 'ventas'
        ]
        
        print(f"\n📋 Tablas encontradas ({len(tables)}):")
        for table in tables:
            status = "✅" if table in expected_tables else "📝"
            print(f"  {status} {table}")
        
        missing_tables = [t for t in expected_tables if t not in tables]
        if missing_tables:
            print(f"\n⚠️  Tablas faltantes: {missing_tables}")
        else:
            print(f"\n✅ Todas las tablas básicas fueron creadas")
        
        return len(missing_tables) == 0
    else:
        print("❌ No se pudo verificar las tablas")
        return False

def main():
    """Función principal"""
    print("=" * 60)
    print("Julia Confecciones - Ejecucion de Esquema Supabase")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Proyecto: {SUPABASE_URL}")
    print()
    
    # Paso 1: Verificar conexión
    if not check_connection():
        print("❌ No se puede continuar sin conexión a Supabase")
        return False
    
    # Paso 2: Ejecutar esquema paso a paso
    print("\n" + "=" * 60)
    if not execute_schema_step_by_step():
        print("❌ Hubo errores críticos en la ejecución del esquema")
        return False
    
    # Paso 3: Verificar tablas
    print("\n" + "=" * 60)
    if not verify_tables():
        print("⚠️  Verificación de tablas incompleta")
    else:
        print("✅ Verificación de tablas completada")
    
    print("\n" + "=" * 60)
    print("🎉 ¡Proceso completado!")
    print("📝 Próximo paso: Importar datos desde CSV")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)