#!/usr/bin/env python3
"""
Script para importar datos de CSV a Supabase
Requiere: pip install pandas psycopg2-binary python-dotenv
"""

import os
import pandas as pd
import psycopg2
from psycopg2 import sql
import logging
from datetime import datetime
import sys

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración de la base de datos
DB_URL = "postgresql://postgres.juliaconfecciones:sb_secret_XrReuib_YbolzAOAecee-A_B86bGyqX@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

# Mapeo de archivos CSV a tablas de Supabase
CSV_TO_TABLE_MAPPING = {
    'access_export_Colegios.csv': 'colegios',
    'access_export_productos.csv': 'productos',
    'access_export_Articulos.csv': 'articulos_colegio',
    'access_export_Ventas.csv': 'ventas',
    'access_export_Detalle_vta.csv': 'detalle_ventas',
    'access_export_Inventarios.csv': 'inventario',
    'access_export_Produccion.csv': 'produccion',
    'access_export_EntradasSalidas.csv': 'movimientos_inventario',
    'access_export_Usuarios.csv': 'usuarios',
    'access_export_Empresa.csv': 'empresa',
    'access_export_Parametros.csv': 'parametros',
    'access_export_Caja_Chica.csv': 'caja_chica',
    'access_export_Retiros_ingresos.csv': 'retiros_ingresos',
    'access_export_Tipos_vta.csv': 'tipos_venta',
    'access_export_Correlativo.csv': 'correlativos',
    'access_export_Entregas.csv': 'entregas',
    'access_export_Planes_mov.csv': 'planes_mov',
    'access_export_correoenviado.csv': 'correos_enviados'
}

def clean_column_name(col_name):
    """Limpiar nombres de columnas para PostgreSQL"""
    return col_name.lower().replace(' ', '_').replace('.', '_').replace('-', '_')

def get_csv_headers(csv_path):
    """Obtener headers del archivo CSV"""
    try:
        df_sample = pd.read_csv(csv_path, nrows=1)
        return [clean_column_name(col) for col in df_sample.columns]
    except Exception as e:
        logger.error(f"Error al leer headers de {csv_path}: {e}")
        return []

def import_csv_to_table(csv_path, table_name, conn):
    """Importar datos de un archivo CSV a una tabla específica"""
    try:
        logger.info(f"Importando {csv_path} a tabla {table_name}")
        
        # Leer el CSV
        df = pd.read_csv(csv_path)
        logger.info(f"CSV tiene {len(df)} filas")
        
        # Limpiar nombres de columnas
        df.columns = [clean_column_name(col) for col in df.columns]
        
        # Convertir valores NaN a None para PostgreSQL
        df = df.where(pd.notnull(df), None)
        
        # Crear cursor
        cur = conn.cursor()
        
        # Obtener columnas de la tabla destino
        cur.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """)
        table_columns = [row[0] for row in cur.fetchall()]
        
        # Filtrar solo las columnas que existen en la tabla
        available_columns = [col for col in df.columns if col in table_columns]
        if not available_columns:
            logger.warning(f"No hay columnas coincidentes para {table_name}")
            return False
        
        df_filtered = df[available_columns]
        
        # Preparar datos para inserción
        data = []
        for _, row in df_filtered.iterrows():
            data.append([None if pd.isna(val) else val for val in row.tolist()])
        
        # Construir consulta de inserción
        columns_sql = sql.SQL(', ').join([sql.Identifier(col) for col in available_columns])
        placeholders = sql.SQL(', ').join([sql.Placeholder()] * len(available_columns))
        
        insert_query = sql.SQL("""
            INSERT INTO {} ({}) 
            VALUES ({})
        """).format(
            sql.Identifier(table_name),
            columns_sql,
            placeholders
        )
        
        # Ejecutar inserción por lotes
        batch_size = 1000
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            cur.executemany(insert_query, batch)
            conn.commit()
            logger.info(f"Insertados {len(batch)} registros (total: {i + len(batch)})")
        
        cur.close()
        logger.info(f"Importación completada para {table_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error importando {csv_path} a {table_name}: {e}")
        conn.rollback()
        return False

def main():
    """Función principal"""
    logger.info("Iniciando importación de datos a Supabase")
    
    # Verificar conexión
    try:
        conn = psycopg2.connect(DB_URL)
        logger.info("Conexión a Supabase establecida")
    except Exception as e:
        logger.error(f"Error de conexión: {e}")
        return False
    
    # Directorio de archivos CSV
    csv_dir = "C:\\julia-confecciones"
    
    success_count = 0
    total_count = len(CSV_TO_TABLE_MAPPING)
    
    # Procesar cada archivo CSV
    for csv_file, table_name in CSV_TO_TABLE_MAPPING.items():
        csv_path = os.path.join(csv_dir, csv_file)
        
        if os.path.exists(csv_path):
            logger.info(f"Procesando {csv_file}")
            if import_csv_to_table(csv_path, table_name, conn):
                success_count += 1
            else:
                logger.error(f"Falló importación de {csv_file}")
        else:
            logger.warning(f"Archivo no encontrado: {csv_path}")
    
    conn.close()
    
    logger.info(f"Importación completada: {success_count}/{total_count} tablas importadas exitosamente")
    
    if success_count == total_count:
        logger.info("¡Todos los datos importados exitosamente!")
        return True
    else:
        logger.warning(f"Algunas tablas no pudieron importarse: {total_count - success_count} fallidas")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)