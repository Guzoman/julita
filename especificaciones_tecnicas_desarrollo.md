# Julia Confecciones - Especificaciones Técnicas para Desarrollo Web

## 📊 Estructura de Datos

### Esquema de Productos (Supabase)
```sql
-- Tabla principal de productos
CREATE TABLE productos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    precio_costo NUMERIC(12,2) DEFAULT 0,
    precio_venta NUMERIC(12,2) NOT NULL,
    medusa_id VARCHAR(100) UNIQUE
);

-- Variantes (tallas, colores, colegios)
CREATE TABLE producto_variantes (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER REFERENCES productos(id),
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    talla VARCHAR(20),
    color VARCHAR(50),
    sku VARCHAR(100),
    precio_costo NUMERIC(12,2),
    precio_venta NUMERIC(12,2),
    stock INTEGER DEFAULT 0,
    medusa_variant_id VARCHAR(100)
);

-- Categorías por colegio
CREATE TABLE colegios (
    id SERIAL PRIMARY KEY,
    codigo INTEGER NOT NULL UNIQUE,
    descripcion VARCHAR(255) NOT NULL
);
```

### API Endpoints Disponibles

#### Productos
```typescript
// Obtener todos los productos
GET /api/products
Response: {
  products: Array<{
    id: string;
    title: string;
    description: string;
    variants: Array<{
      id: string;
      title: string;
      sku: string;
      prices: Array<{
        amount: number;
        currency: string;
      }>;
      options: Array<{
        id: string;
        value: string;
      }>;
    }>;
  }>;
}

// Obtener producto específico
GET /api/products/{id}

// Buscar productos
GET /api/products?q={query}

// Obtener productos por categoría
GET /api/products?category_id={id}
```

#### Pedidos
```typescript
// Crear orden
POST /api/orders
Request: {
  email: string;
  shipping_address: Address;
  items: Array<{
    variant_id: string;
    quantity: number;
    metadata?: {
      embroidery_text?: string;
      embroidery_font?: string;
      embroidery_design_id?: string;
    };
  }>;
  region_id: string;
}

// Obtener orden del cliente
GET /api/orders/{id}
```

#### Personalización de Bordados
```typescript
// Generar archivo PES (a través de n8n)
POST /api/embroidery/generate
Request: {
  text: string; // max 50 caracteres
  font: string; // fuente aprobada
  size: number; // tamaño en mm
}
Response: {
  file_url: string;
  stitch_count: number;
  estimated_price: number;
}

// Obtener diseños aprobados
GET /api/embroidery/designs
Response: {
  designs: Array<{
    id: string;
    name: string;
    preview_url: string;
    stitch_count: number;
  }>;
}
```

## 🛠️ Componentes Técnicos Requeridos

### 1. ProductGrid Component
```svelte
<!-- ProductGrid.svelte -->
<script>
  export let products = [];
  export let loading = false;
  
  // Props del componente
  let selectedFilters = {
    category: null,
    priceRange: null,
    sizes: [],
    colors: []
  };
  
  // Funciones de filtrado
  function filterProducts() {
    return products.filter(product => {
      // Lógica de filtrado
      return true;
    });
  }
</script>

<div class="product-grid">
  {#if loading}
    <div class="loading">Cargando productos...</div>
  {:else}
    <div class="filters">
      <!-- Filtros por categoría, precio, etc. -->
    </div>
    
    <div class="grid">
      {#each filterProducts() as product}
        <ProductCard {product} />
      {/each}
    </div>
  {/if}
</div>
```

### 2. ProductCard Component
```svelte
<!-- ProductCard.svelte -->
<script>
  export let product;
  
  function handleQuickView() {
    dispatch('quickView', { product });
  }
  
  function addToCart() {
    dispatch('addToCart', { productId: product.id });
  }
</script>

<div class="product-card">
  <div class="product-image">
    <img 
      src={product.thumbnail} 
      alt={product.title}
      loading="lazy"
    />
  </div>
  
  <div class="product-info">
    <h3>{product.title}</h3>
    <p class="price">${product.variants[0]?.prices[0]?.amount || 0}</p>
    
    {#if product.variants.length > 1}
      <div class="variant-indicator">
        {product.variants.length} opciones
      </div>
    {/if}
    
    <div class="actions">
      <button on:click={handleQuickView}>Ver Detalles</button>
      <button on:click={addToCart} class="primary">Agregar</button>
    </div>
  </div>
</div>
```

### 3. ProductVariantSelector Component
```svelte
<!-- ProductVariantSelector.svelte -->
<script>
  export let variants = [];
  export let selectedVariant = null;
  
  // Agrupar variantes por tipo de opción
  $: options = variants.reduce((acc, variant) => {
    variant.options.forEach(option => {
      if (!acc[option.id]) {
        acc[option.id] = [];
      }
      if (!acc[option.id].includes(option.value)) {
        acc[option.id].push(option.value);
      }
    });
    return acc;
  }, {});
  
  // Encontrar variante seleccionada
  function findVariant() {
    const selectedOptions = {};
    Object.keys(options).forEach(optionId => {
      const selected = selectedOptions[optionId];
      // Lógica para encontrar variante con las opciones seleccionadas
    });
  }
</script>

<div class="variant-selector">
  {#each Object.entries(options) as [optionId, values]}
    <div class="option-group">
      <h4>{optionId}</h4>
      <div class="option-values">
        {#each values as value}
          <button 
            class:selected={selectedOptions[optionId] === value}
            on:click={() => selectOption(optionId, value)}
          >
            {value}
          </button>
        {/each}
      </div>
    </div>
  {/each}
</div>
```

### 4. EmbroideryCustomizer Component
```svelte
<!-- EmbroideryCustomizer.svelte -->
<script>
  export let maxChars = 50;
  export let availableFonts = ['Arial', 'Times New Roman', 'Helvetica'];
  
  let embroideryText = '';
  let selectedFont = availableFonts[0];
  let includeEmbroidery = false;
  let additionalPrice = 0;
  
  // Validación en tiempo real
  $: charCount = embroideryText.length;
  $: isValidText = charCount > 0 && charCount <= maxChars;
  $: canAddEmbroidery = includeEmbroidery && isValidText;
  
  // Calcular precio adicional
  $: additionalPrice = includeEmbroidery && isValidText ? 5000 : 0; // $5.000 por bordado
  
  // Función para generar preview
  async function generatePreview() {
    if (!isValidText) return;
    
    try {
      const response = await fetch('/api/embroidery/preview', {
        method: 'POST',
        body: JSON.stringify({
          text: embroideryText,
          font: selectedFont
        })
      });
      
      const data = await response.json();
      return data.preview_url;
    } catch (error) {
      console.error('Error generando preview:', error);
    }
  }
  
  // Exportar datos al componente padre
  function getEmbroideryData() {
    if (!canAddEmbroidery) return null;
    
    return {
      text: embroideryText,
      font: selectedFont,
      additionalPrice: additionalPrice
    };
  }
</script>

<div class="embroidery-customizer">
  <div class="toggle-embroidery">
    <label>
      <input 
        type="checkbox" 
        bind:checked={includeEmbroidery}
      />
      Agregar bordado personalizado (+${additionalPrice})
    </label>
  </div>
  
  {#if includeEmbroidery}
    <div class="embroidery-options">
      <div class="text-input">
        <label>Texto para bordar:</label>
        <input 
          type="text" 
          bind:value={embroideryText}
          maxlength={maxChars}
          placeholder="Ingrese el texto (max {maxChars} caracteres)"
        />
        <div class="char-counter">
          {charCount}/{maxChars}
        </div>
      </div>
      
      <div class="font-selector">
        <label>Fuente:</label>
        <select bind:value={selectedFont}>
          {#each availableFonts as font}
            <option value={font}>{font}</option>
          {/each}
        </select>
      </div>
      
      <div class="preview">
        <!-- Preview generado por API o placeholder -->
        <div class="preview-placeholder">
          Vista previa: "{embroideryText}"
        </div>
      </div>
    </div>
  {/if}
</div>
```

### 5. ShoppingCart Component
```svelte
<!-- ShoppingCart.svelte -->
<script>
  import { onMount } from 'svelte';
  
  let cartItems = [];
  let isOpen = false;
  
  onMount(async () => {
    // Cargar carrito desde localStorage o API
    loadCart();
  });
  
  async function loadCart() {
    const stored = localStorage.getItem('cart');
    if (stored) {
      cartItems = JSON.parse(stored);
    }
  }
  
  function updateQuantity(itemId, newQuantity) {
    if (newQuantity <= 0) {
      removeFromCart(itemId);
      return;
    }
    
    cartItems = cartItems.map(item => 
      item.id === itemId 
        ? { ...item, quantity: newQuantity }
        : item
    );
    saveCart();
  }
  
  function removeFromCart(itemId) {
    cartItems = cartItems.filter(item => item.id !== itemId);
    saveCart();
  }
  
  function saveCart() {
    localStorage.setItem('cart', JSON.stringify(cartItems));
  }
  
  function getTotal() {
    return cartItems.reduce((total, item) => {
      const itemTotal = item.price * item.quantity;
      const embroideryTotal = (item.embroidery?.additionalPrice || 0) * item.quantity;
      return total + itemTotal + embroideryTotal;
    }, 0);
  }
</script>

<div class="shopping-cart" class:open={isOpen}>
  <button class="cart-toggle" on:click={() => isOpen = !isOpen}>
    Carrito ({cartItems.reduce((sum, item) => sum + item.quantity, 0)})
  </button>
  
  {#if isOpen}
    <div class="cart-dropdown">
      {#if cartItems.length === 0}
        <div class="empty-cart">El carrito está vacío</div>
      {:else}
        <div class="cart-items">
          {#each cartItems as item}
            <div class="cart-item">
              <div class="item-info">
                <h4>{item.name}</h4>
                <p>{item.variant}</p>
                {#if item.embroidery}
                  <div class="embroidery-info">
                    Bordado: "{item.embroidery.text}" ({item.embroidery.font})
                  </div>
                {/if}
              </div>
              
              <div class="item-controls">
                <div class="quantity-controls">
                  <button on:click={() => updateQuantity(item.id, item.quantity - 1)}>-</button>
                  <span>{item.quantity}</span>
                  <button on:click={() => updateQuantity(item.id, item.quantity + 1)}>+</button>
                </div>
                
                <div class="item-price">
                  ${((item.price + (item.embroidery?.additionalPrice || 0)) * item.quantity).toFixed(0)}
                </div>
                
                <button class="remove" on:click={() => removeFromCart(item.id)}>
                  ×
                </button>
              </div>
            </div>
          {/each}
        </div>
        
        <div class="cart-summary">
          <div class="total">
            <strong>Total: ${getTotal().toFixed(0)}</strong>
          </div>
          <button class="checkout-button" on:click={proceedToCheckout}>
            Proceder al pago
          </button>
        </div>
      {/if}
    </div>
  {/if}
</div>
```

### 6. OrderTracking Component
```svelte
<!-- OrderTracking.svelte -->
<script>
  export let orderId;
  
  let trackingData = [];
  let loading = true;
  
  onMount(async () => {
    try {
      const response = await fetch(`/api/orders/${orderId}/tracking`);
      trackingData = await response.json();
    } catch (error) {
      console.error('Error cargando seguimiento:', error);
    } finally {
      loading = false;
    }
  });
  
  function getStageIcon(stage) {
    const icons = {
      'pending': '⏳',
      'cutting': '✂️',
      'embroidery': '🧵',
      'sewing': '🧵',
      'quality_check': '✅',
      'shipping': '📦',
      'delivered': '🎯'
    };
    return icons[stage] || '⏳';
  }
</script>

<div class="order-tracking">
  <h3>Seguimiento del Pedido #{orderId}</h3>
  
  {#if loading}
    <div class="loading">Cargando seguimiento...</div>
  {:else if trackingData.length === 0}
    <div class="no-tracking">No hay información de seguimiento disponible</div>
  {:else}
    <div class="tracking-timeline">
      {#each trackingData as step, index}
        <div class="tracking-step" class:completed={step.completed}>
          <div class="step-icon">
            {getStageIcon(step.stage)}
          </div>
          
          <div class="step-content">
            <h4>{step.title}</h4>
            <p>{step.description}</p>
            {#if step.timestamp}
              <small class="timestamp">
                {new Date(step.timestamp).toLocaleString('es-CL')}
              </small>
            {/if}
          </div>
          
          {#if index < trackingData.length - 1}
            <div class="step-connector"></div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>
```

## 🔄 Integración con Supabase

### Client de Supabase para SvelteKit
```typescript
// src/lib/supabase.ts
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseKey);

// Tipos para TypeScript
export interface Product {
  id: number;
  codigo: string;
  nombre: string;
  descripcion: string;
  precio_venta: number;
}

export interface ProductVariant {
  id: number;
  producto_id: number;
  nombre: string;
  talla?: string;
  color?: string;
  sku: string;
  precio_venta: number;
  stock: number;
}

// Funciones de utilidad
export async function getProducts() {
  const { data, error } = await supabase
    .from('productos')
    .select(`
      *,
      producto_variantes (*)
    `);
  
  if (error) throw error;
  return data;
}

export async function getProductByCode(code: string) {
  const { data, error } = await supabase
    .from('productos')
    .select(`
      *,
      producto_variantes (*)
    `)
    .eq('codigo', code)
    .single();
  
  if (error) throw error;
  return data;
}
```

## 📡 Real-time Updates

### Suscripción a cambios de stock
```typescript
// src/lib/realtime.ts
import { supabase } from './supabase';

export function subscribeToStockUpdates(callback: (variants: ProductVariant[]) => void) {
  const channel = supabase
    .channel('stock-changes')
    .on(
      'postgres_changes',
      {
        event: 'UPDATE',
        schema: 'public',
        table: 'producto_variantes',
        filter: 'stock=lt.10' // Stock bajo
      },
      (payload) => {
        console.log('Stock update:', payload);
        callback(payload.new as ProductVariant[]);
      }
    )
    .subscribe();
  
  return () => {
    supabase.removeChannel(channel);
  };
}
```

## 🔧 Variables de Entorno Requeridas

```bash
# .env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_MEDUSA_URL=https://your-medusa-store.com
VITE_GETNET_PUBLIC_KEY=your-getnet-key
VITE_N8N_WEBHOOK_URL=your-n8n-webhook
```

## 📦 Build y Deploy

### SvelteKit Config
```typescript
// svelte.config.js
import adapter from '@sveltejs/adapter-cloudflare';

export default {
  kit: {
    adapter: adapter({
      // Configuración para Cloudflare Pages
      platformProxy: {
        configPath: 'wrangler.toml',
        environment: undefined,
      }
    })
  }
};
```

### Optimizaciones de Build
```javascript
// vite.config.js
import { sveltekit } from '@sveltejs/kit/vite';
import { optimizeDeps } from 'vite';

export default {
  plugins: [sveltekit()],
  optimizeDeps: {
    include: ['lodash-es', 'date-fns']
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['svelte', 'svelte/store'],
          utils: ['lodash-es', 'date-fns']
        }
      }
    }
  }
};
```

Este documento proporciona toda la información técnica necesaria para implementar el frontend sin detalles estéticos, enfocándose únicamente en la funcionalidad y la integración con el backend existente.