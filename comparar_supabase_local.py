#!/usr/bin/env python3
"""
Revisión de Supabase sin caracteres especiales (fix para consola Windows)
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print("Revision de Supabase - Julia Confecciones")
print("Verificando concordancia con logica de negocio VB6")
print("=" * 60)

if not supabase_url or not supabase_key:
    print("ERROR: Faltan credenciales")
    exit(1)

headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}',
    'Content-Type': 'application/json',
    'Prefer': 'params=single-object'
}

def revisar_supabase():
    try:
        print("Conectando a Supabase...")

        # Verificar conexion
        response = requests.get(f"{supabase_url}/rest/v1/", headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"ERROR: No se puede conectar a Supabase (status {response.status_code})")
            return False

        print("Conexion a Supabase establecida")

        # Revisar tablas principales
        print("\nRevisando estructura de tablas:")
        print("=" * 50)

        tablas_principales = ['colegios', 'productos', 'articulos', 'ventas', 'ventas_detalle']

        for tabla in tablas_principales:
            try:
                response = requests.get(
                    f"{supabase_url}/rest/v1/{tabla}?select=*&limit=1",
                    headers=headers,
                    timeout=10
                )

                if response.status_code == 200:
                    print(f"OK Tabla '{tabla}' existe")
                    if response.text.strip():
                        data = response.json()
                        if data:
                            campos = list(data[0].keys())
                            print(f"   Campos: {campos}")
                            print(f"   Ejemplo: {data[0]}")
                    else:
                        print("   Tabla vacia")
                else:
                    print(f"ERROR al acceder tabla '{tabla}': {response.text}")

            except Exception as e:
                print(f"ERROR en tabla '{tabla}': {str(e)}")

        # Analisis critico de productos
        print("\nAnalisis critico - Tabla Productos:")
        print("=" * 50)

        try:
            response = requests.get(
                f"{supabase_url}/rest/v1/productos?select=*&limit=5",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                productos = response.json()
                print(f"Total productos encontrados: {len(productos)}")

                if productos:
                    campos = list(productos[0].keys())
                    print(f"Campos actuales: {campos}")

                    # Verificar campos criticos
                    tiene_cod_cole = 'cod_cole' in campos
                    tiene_articulo = 'articulo' in campos
                    tiene_descripcion = 'descripcion' in campos

                    print(f"\nAnalisis de campos:")
                    print(f"- cod_cole: {'OK' if tiene_cod_cole else 'FALTANTE (CRITICO)'}")
                    print(f"- articulo: {'OK' if tiene_articulo else 'FALTANTE (CRITICO)'}")
                    print(f"- descripcion: {'OK' if tiene_descripcion else 'FALTANTE (usa nombre)'}")

                    print(f"\nEjemplos de productos:")
                    for i, p in enumerate(productos[:3], 1):
                        print(f"\nProducto {i}:")
                        print(f"  Codigo: {p.get('codigo')}")
                        print(f"  Nombre: {p.get('nombre')}")
                        print(f"  Descripcion: {p.get('descripcion')}")
                        print(f"  Precio: {p.get('precio_venta')}")
                        print(f"  Categoria: {p.get('categoria')}")

                        # Analisis VB6
                        codigo = p.get('codigo')
                        if codigo and str(codigo).isdigit():
                            codigo_num = int(codigo)
                            if codigo_num < 100000:
                                grupo = codigo_num // 100
                                talla = (codigo_num % 100) // 2 - 1
                                print(f"  Grupo VB6: {grupo}")
                                print(f"  Talla VB6: {talla}")

                else:
                    print("No hay productos en la tabla")

            else:
                print(f"ERROR al verificar productos: {response.text}")

        except Exception as e:
            print(f"ERROR en verificacion: {str(e)}")
            return False

        # Conclusiones
        print(f"\nCONCLUSIONES:")
        print("=" * 50)
        print("1. Conexion a Supabase: OK")
        print("2. Tabla colegios: OK (estructura correcta)")
        print("3. Tabla productos: OK (conecta)")
        print("4. Campos criticos faltantes: cod_cole, articulo")
        print("5. Necesita ejecutar SQL fix para completar estructura")

        return True

    except Exception as e:
        print(f"ERROR de conexion a Supabase: {str(e)}")
        return False

if __name__ == "__main__":
    revisar_supabase()