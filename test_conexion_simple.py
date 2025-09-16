#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener credenciales
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print("=== Test de Conexion Supabase ===")
print(f"URL: {supabase_url}")
print(f"Key: {supabase_key[:20]}..." if supabase_key else "Key: No encontrada")

if not supabase_url or not supabase_key:
    print("ERROR: Faltan credenciales")
    exit(1)

# Test basico de conexion HTTP
try:
    print("\nProbando conexion basica...")
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}'
    }

    # Intentar conectar al endpoint de salud
    response = requests.get(f"{supabase_url}/rest/v1/", headers=headers, timeout=10)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:200]}...")

    if response.status_code == 200:
        print("✅ Conexion exitosa!")

        # Probar listar tablas
        print("\nProbando listar tablas...")
        response = requests.get(f"{supabase_url}/rest/v1/colegios?select=*&limit=1",
                               headers=headers, timeout=10)
        print(f"Colegios Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ Tabla colegios accesible")
            data = response.json()
            print(f"Registros: {len(data)}")
            if data:
                print(f"Ejemplo: {data[0]}")
        else:
            print(f"❌ Error accediendo colegios: {response.text}")

    else:
        print(f"❌ Error de conexion: {response.status_code}")
        print(f"Response: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"❌ Error de red: {e}")
except Exception as e:
    print(f"❌ Error inesperado: {e}")