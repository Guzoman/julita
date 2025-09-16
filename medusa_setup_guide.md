# Julia Confecciones - Configuración de MedusaJS

## Pasos para configurar MedusaJS con Supabase

### 1. Prerrequisitos
- Node.js v18+ instalado
- PostgreSQL access (ya tenemos Supabase)
- Redis (opcional, para caché)

### 2. Instalar MedusaJS

```bash
# Crear proyecto Medusa
npx create-medusa-app@latest julia-confecciones-medusa --seed-db=false

# O instalar manualmente:
mkdir julia-confecciones-medusa && cd julia-confecciones-medusa
npm init -y
npm install @medusajs/medusa
npm install medusa-fulfillment-manual medusa-payment-manual
```

### 3. Configurar conexión a Supabase

Archivo: `julia-confecciones-medusa/medusa-config.js`

```javascript
module.exports = {
  projectConfig: {
    // Database
    database_url: "postgresql://postgres:[TU_PASSWORD]@db.ayuorfvindwywtltszdl.supabase.co:5432/postgres",
    
    // Redis (opcional)
    redis_url: process.env.REDIS_URL,
    
    // JWT
    jwt_secret: process.env.JWT_SECRET || "supersecret",
    cookie_secret: process.env.COOKIE_SECRET || "supersecret",
  },
  
  plugins: [
    `medusa-fulfillment-manual`,
    `medusa-payment-manual`,
  ],
}
```

### 4. Obtener credenciales de Supabase

Desde el dashboard de Supabase:
1. Settings → Database → Connection string
2. Copiar la URI de conexión PostgreSQL
3. Reemplazar `[TU_PASSWORD]` con tu password de base de datos

### 5. Instalar y ejecutar

```bash
cd julia-confecciones-medusa
npm install
# Configurar variables de entorno
echo "DATABASE_URL=postgresql://postgres:[PASSWORD]@db.ayuorfvindwywtltszdl.supabase.co:5432/postgres" > .env
echo "JWT_SECRET=supersecret" >> .env
echo "COOKIE_SECRET=supersecret" >> .env

# Ejecutar migraciones
npx medusa migrations run

# Iniciar servidor
npx medusa develop
```

### 6. Verificar instalación

El servidor debería iniciarse en:
- Admin: http://localhost:7000
- Store API: http://localhost:9000

### 7. Importar productos existentes

Crear script para sincronizar productos de Supabase con Medusa:

```javascript
// scripts/import-products.js
const { createClient } = require("@medusajs/medusa")

async function importProducts() {
  const medusa = createClient({
    baseUrl: "http://localhost:9000",
    maxRetries: 3,
  })
  
  // Obtener productos de Supabase
  const products = await getSupabaseProducts()
  
  for (const product of products) {
    await medusa.admin.products.create({
      title: product.nombre,
      handle: product.codigo.toLowerCase(),
      variants: [{
        title: "Default",
        prices: [{
          amount: product.precio_venta,
          currency_code: "CLP"
        }]
      }]
    })
  }
}
```

## Siguientes pasos después de MedusaJS

1. **Configurar dominio personalizado**
2. **Integrar pasarelas de pago chilenas (Getnet, Transbank)**
3. **Conectar con MercadoLibre**
4. **Implementar sistema de producción**
5. **Desarrollar frontend con SvelteKit**

## Notas importantes

- MedusaJS requiere configuración adicional para Chilean pesos (CLP)
- Necesitarás plugins personalizados para boletas electrónicas
- La integración con LibreDTE requerirá desarrollo personalizado