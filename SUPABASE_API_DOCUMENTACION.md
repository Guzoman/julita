# 📡 Documentación API Supabase - Julia Confecciones

## 🔑 Credenciales de Acceso

### **URL del Proyecto**
```
https://ayuorfvindwywtltszdl.supabase.co
```

### **Claves de API**
- **SUPABASE_URL**: `https://ayuorfvindwywtltszdl.supabase.co`
- **SUPABASE_SERVICE_ROLE_KEY**: `sb_secret_XrReuib_YbolzAOAecee-A_B86bGyqX`

## 📋 Headers Requeridos

```python
headers = {
    'apikey': 'sb_secret_XrReuib_YbolzAOAecee-A_B86bGyqX',
    'Authorization': 'Bearer sb_secret_XrReuib_YbolzAOAecee-A_B86bGyqX',
    'Content-Type': 'application/json',
    'Prefer': 'params=single-object'
}
```

## 🗃️ Estructura de Base de Datos

### **Tablas Existentes**
1. **colegios** (completa)
2. **productos** (incompleta - faltan campos)
3. **ventas** (existe)
4. **ventas_detalle** (existe)
5. **articulos** (no existe - error PGRST205)

### **Campos Críticos Faltantes en Productos**
- `cod_cole` INTEGER (relación con colegios)
- `articulo` INTEGER (agrupación de tipos)

## 🔍 Endpoints Principales

### **1. Obtener Productos**
```http
GET /rest/v1/productos?select=*&limit=5
```

### **2. Obtener Colegios**
```http
GET /rest/v1/colegios?select=*
```

### **3. Obtener Ventas**
```http
GET /rest/v1/ventas?select=*
```

### **4. Insertar Producto**
```http
POST /rest/v1/productos
Content-Type: application/json

{
  "codigo": "21",
  "nombre": "Falda Gris",
  "precio_venta": 17000,
  "activo": true
}
```

### **5. Actualizar Producto**
```http
PATCH /rest/v1/productos?id=eq.1
Content-Type: application/json

{
  "precio_venta": 18000,
  "descripcion": "Falda Gris Escolar"
}
```

### **6. Eliminar Producto**
```http
DELETE /rest/v1/productos?id=eq.1
```

## 🔧 Operaciones Especiales

### **Filtrado**
```http
GET /rest/v1/productos?codigo=eq.21&select=*
GET /rest/v1/productos?precio_venta=gt.15000&select=*
GET /rest/v1/productos?nombre=ilike.*polera*&select=*
```

### **Ordenamiento**
```http
GET /rest/v1/productos?select=*&order=codigo.asc
GET /rest/v1/productos?select=*&order=precio_venta.desc
```

### **Relaciones**
```http
GET /rest/v1/productos?select=*,colegios(descripcion)&limit=5
```

## 💻 Ejemplos de Código

### **Python - Conexión Básica**
```python
import requests
import os

# Cargar variables de entorno
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}',
    'Content-Type': 'application/json'
}

# Obtener productos
response = requests.get(
    f"{supabase_url}/rest/v1/productos?select=*&limit=5",
    headers=headers,
    timeout=10
)

if response.status_code == 200:
    productos = response.json()
    print(f"Productos encontrados: {len(productos)}")
```

### **JavaScript - Fetch API**
```javascript
const supabaseUrl = 'https://ayuorfvindwywtltszdl.supabase.co';
const supabaseKey = 'sb_secret_XrReuib_YbolzAOAecee-A_B86bGyqX';

const headers = {
    'apikey': supabaseKey,
    'Authorization': `Bearer ${supabaseKey}`,
    'Content-Type': 'application/json'
};

async function getProductos() {
    const response = await fetch(`${supabaseUrl}/rest/v1/productos?select=*&limit=5`, {
        method: 'GET',
        headers: headers
    });

    if (response.ok) {
        const productos = await response.json();
        console.log('Productos:', productos);
    }
}
```

## 🎯 Lógica de Negocio VB6

### **Cálculo de Tallas**
```python
def calcular_datos_uniforme(codigo):
    codigo_num = int(codigo)
    if codigo_num < 100000:
        grupo_articulo = codigo_num // 100
        talla_num = (codigo_num % 100) // 2 - 1

        mapa_tallas = {
            4: 'T_4', 6: 'T_6', 8: 'T_8', 10: 'T_10',
            12: 'T_12', 14: 'T_14', 16: 'T_16',
            17: 'T_S', 18: 'T_M', 19: 'T_L',
            20: 'T_XL', 21: 'T_XXL', 22: 'T_XXXL'
        }

        talla_etiqueta = mapa_tallas.get(talla_num, f'T_{talla_num}')

        return {
            'grupo_articulo': grupo_articulo,
            'talla': talla_num,
            'talla_etiqueta': talla_etiqueta
        }
```

### **Ejemplos de Códigos**
- Código 1104 → Grupo 11, Talla 1 → Polera Pique MC LR Talla 4
- Código 1106 → Grupo 11, Talla 2 → Polera Pique MC LR Talla 6
- Código 21 → Grupo 0, Talla 9 → Falda Gris Talla 6

## 🚨 Problemas Conocidos

### **Error de Snippets**
- **ID**: `ab0a1e92-c3b0-471a-b9fd-86dc82bc8d83`
- **Descripción**: "Unable to find snippet with ID..."
- **Causa**: Corrupción en frontend (localStorage)
- **Soluciones**: Limpiar cache, modo incógnito, otro navegador

### **Campos Faltantes**
- La tabla `productos` necesita campos `cod_cole` y `articulo`
- La tabla `articulos` no existe y debe crearse

## 📊 Estado Actual

✅ **Funcional:**
- Conexión a API estable
- Operaciones CRUD básicas
- Lógica VB6 implementada

❌ **Pendiente:**
- Resolver error de snippets editor SQL
- Ejecutar ALTER TABLE para campos faltantes
- Importar datos completos desde Access

## 🔧 SQL Fixes Pendientes

```sql
-- Agregar campos faltantes
ALTER TABLE productos ADD COLUMN IF NOT EXISTS cod_cole INTEGER;
ALTER TABLE productos ADD COLUMN IF NOT EXISTS articulo INTEGER;

-- Crear tabla articulos
CREATE TABLE IF NOT EXISTS articulos (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    articulo INTEGER NOT NULL UNIQUE,
    descripcion VARCHAR(500) NOT NULL,
    categoria VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---
**Última actualización**: 15 de septiembre de 2024
**Proyecto**: Julia Confecciones Uniformes Escolares
**Base de datos**: Supabase PostgreSQL