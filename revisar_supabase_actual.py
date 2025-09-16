#!/usr/bin/env python3
"""
Script para revisar la estructura actual de Supabase y verificar concordancia con VB6
"""

import os
import sys
from dotenv import load_dotenv
import supabase

# Cargar variables de entorno
load_dotenv()

def revisar_supabase():
    """Revisar estructura actual de tablas en Supabase"""

    # Obtener credenciales desde entorno
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not supabase_key:
        print("ERROR: No se encontraron las credenciales de Supabase")
        print("Por favor, configura SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY en tu .env")
        return False

    try:
        # Conectar a Supabase
        client = supabase.create_client(supabase_url, supabase_key)
        print("Conexion a Supabase establecida")

        # Lista de tablas esperadas según el modelo de negocio
        tablas_esperadas = [
            'colegios',
            'productos',
            'articulos',
            'ventas',
            'ventas_detalle'
        ]

        print("\nRevisando estructura de tablas:")
        print("=" * 50)

        for tabla in tablas_esperadas:
            try:
                # Intentar consultar la tabla para ver si existe
                response = client.table(tabla).select('*').limit(1).execute()

                if hasattr(response, 'data') and response.data is not None:
                    print(f"OK Tabla '{tabla}' existe")

                    # Mostrar algunas filas de ejemplo
                    if len(response.data) > 0:
                        print(f"   Campos: {list(response.data[0].keys())}")
                        print(f"   Ejemplo: {response.data[0]}")
                else:
                    print(f"ERROR Tabla '{tabla}' no existe o esta vacia")

            except Exception as e:
                print(f"ERROR al acceder tabla '{tabla}': {str(e)}")

        # Verificar específicamente la estructura de productos
        print("\nVerificacion critica - Tabla Productos:")
        print("=" * 50)

        try:
            response = client.table('productos').select('*').limit(5).execute()

            if hasattr(response, 'data') and response.data:
                primeros_productos = response.data

                for i, producto in enumerate(primeros_productos, 1):
                    print(f"\nProducto {i}:")
                    print(f"  Código: {producto.get('codigo', 'N/A')}")
                    print(f"  Descripción: {producto.get('descripcion', 'N/A')}")
                    print(f"  Precio: {producto.get('precio_venta', 'N/A')}")

                    # Verificar campos críticos
                    tiene_cod_cole = 'cod_cole' in producto
                    tiene_articulo = 'articulo' in producto

                    print(f"  ¿Tiene cod_cole? {'✅' if tiene_cod_cole else '❌'}")
                    print(f"  ¿Tiene articulo? {'✅' if tiene_articulo else '❌'}")

                    if not tiene_cod_cole or not tiene_articulo:
                        print("  ⚠️  ¡FALTAN CAMPOS CRÍTICOS!")

                # Análisis final
                productos_con_campos = [p for p in primeros_productos
                                      if 'cod_cole' in p and 'articulo' in p]

                if len(productos_con_campos) == 0:
                    print(f"\n🚨 CRÍTICO: Ningún producto tiene los campos necesarios")
                    print("   Se necesita ejecutar el fix_concordancia_supabase.sql")
                    return False
                else:
                    print(f"\n✅ {len(productos_con_campos)}/{len(primeros_productos)} productos tienen estructura correcta")

            else:
                print("❌ No se pudo acceder a la tabla productos")
                return False

        except Exception as e:
            print(f"❌ Error al verificar productos: {str(e)}")
            return False

        return True

    except Exception as e:
        print(f"❌ Error de conexión a Supabase: {str(e)}")
        return False

def main():
    print("Revision de Supabase - Julia Confecciones")
    print("Verificando concordancia con logica de negocio VB6")
    print("=" * 60)

    if revisar_supabase():
        print("\nRevision completada - Supabase parece estar correctamente configurado")
    else:
        print("\nSe detectaron problemas - Ejecuta fix_concordancia_supabase.sql")
        sys.exit(1)

if __name__ == "__main__":
    main()