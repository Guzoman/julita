import pyodbc
import csv
import os

def extract_access_tables(mdb_path):
    """Extraer todas las tablas de la base de datos Access"""
    try:
        # Conexión a Access database
        conn_str = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={mdb_path};'
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        print("OK Conexion exitosa a Access database")
        
        # Listar todas las tablas
        tables = []
        for table_info in cursor.tables(tableType='TABLE'):
            table_name = table_info.table_name
            if not table_name.startswith('MSys'):  # Filtrar tablas del sistema
                tables.append(table_name)
        
        print(f"Tablas encontradas: {tables}")
        
        # Exportar cada tabla
        for table_name in tables:
            try:
                print(f"\nExportando tabla: {table_name}")
                
                # Query para obtener datos
                cursor.execute(f"SELECT * FROM [{table_name}]")
                rows = cursor.fetchall()
                
                if rows:
                    # Obtener nombres de columnas
                    columns = [column[0] for column in cursor.description]
                    
                    # Exportar a CSV
                    csv_filename = f"access_export_{table_name}.csv"
                    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(columns)  # Headers
                        
                        for row in rows:
                            # Convertir cada campo a string para evitar problemas de encoding
                            clean_row = []
                            for field in row:
                                if field is None:
                                    clean_row.append('')
                                else:
                                    clean_row.append(str(field))
                            writer.writerow(clean_row)
                    
                    print(f"   OK {len(rows)} registros exportados a {csv_filename}")
                else:
                    print(f"   WARNING Tabla {table_name} esta vacia")
                    
            except Exception as e:
                print(f"   ERROR exportando {table_name}: {e}")
        
        conn.close()
        print(f"\nExportacion completada. Revisa los archivos CSV generados.")
        
    except Exception as e:
        print(f"ERROR conectando a Access: {e}")
        print("Asegurate de tener Microsoft Access Driver instalado")

if __name__ == "__main__":
    mdb_path = r"C:\julia-confecciones\sistema en uso\Programa Inventario - Fuente\Comercial_jc.mdb"
    extract_access_tables(mdb_path)