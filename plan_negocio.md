# 

## 1. Resumen Ejecutivo

**Julia Confecciones** se posicionará como un proveedor líder de uniformes escolares y corporativos, combinando la confección de alta calidad con una plataforma digital moderna para la personalización y gestión de pedidos. Nuestra propuesta de valor se centra en la calidad del producto, la eficiencia operativa a través de la automatización y un sistema de precios dinámico que garantiza la rentabilidad.

Utilizaremos un stack tecnológico escalable basado en Medusa.js como motor de e-commerce, Supabase como nuestra base de datos central, y n8n para la automatización de flujos de trabajo críticos, desde la producción hasta el cálculo de costos.

## 2. Descripción del Negocio

- **Concepto:** Ofrecemos a colegios, empresas e instituciones un servicio integral para el diseño, personalización (bordado y estampado) y suministro de uniformes. El sistema permite gestionar pedidos de gran volumen y calcular presupuestos precisos basados en costos de materiales en tiempo real.
    
- **Misión:** Ser el socio estratégico de instituciones y empresas para su vestimenta corporativa y escolar, garantizando calidad, durabilidad y un proceso de compra sin fricciones.
    
- **Mercado Objetivo:**
    
    - Instituciones educativas (colegios, universidades).
        
    - Empresas de todos los tamaños que requieran uniformes para su personal.
        
    - Equipos deportivos y clubes.
        
    - Agencias de eventos y marketing para merchandising.
        

## 3. Propuesta de Valor Única

- **Precios Dinámicos y Rentables:** Un sistema automatizado que calcula los precios de los lotes basándose en el costo actualizado de los insumos, protegiendo los márgenes de ganancia.
    
- **Calidad y Durabilidad:** Uso de materiales de alta calidad y técnicas de bordado y confección probadas, ideales para el uso intensivo de uniformes.
    
- **Portal de Cliente (Futuro):** Posibilidad de desarrollar portales para que clientes recurrentes (como colegios) puedan realizar pedidos fácilmente.
    
- **Eficiencia Operativa:** Automatización de la cadena de producción, desde la recepción del pedido hasta la notificación de envío, reduciendo errores manuales.
    

## 4. Operaciones y Flujo de Trabajo Automatizado

1. **Solicitud de Presupuesto/Pedido:** Un cliente (ej. un colegio) solicita un presupuesto para 100 polos bordados con su insignia.
    
2. **Cálculo de Precio (Ver sección 4.1):** El sistema calcula el costo total basándose en los precios actuales de los materiales.
    
3. **Creación del Pedido:** Una vez aprobado el presupuesto, se crea un pedido en Medusa.js. La información del bordado (logo, colores) se guarda en los metadatos.
    
4. **Activación del Workflow (n8n):** El evento `order.placed` en Medusa activa un flujo en n8n que:
    
    - **Notifica a Producción:** Envía los detalles y archivos del logo al equipo de bordado.
        
    - **Gestiona el Proyecto:** Crea una tarjeta en Trello/Asana.
        
    - **Actualiza Contabilidad:** Registra el pedido en el sistema contable.
        
5. **Producción y Envío:** El equipo produce el lote y actualiza el estado en Medusa, notificando al cliente.
    

### 4.1. Cálculo de Precios Dinámico para Lotes

Este es un componente central de la operación:

- **Scraping de Costos (n8n):** Un flujo de trabajo programado en n8n visita diariamente las webs de los proveedores para obtener los precios actualizados de hilos, telas y prendas base.
    
- **Base de Datos de Costos (Supabase):** Los precios scrapeados se almacenan en una tabla `material_costs` en Supabase.
    
- **Motor de Cálculo (Lógica en Medusa):** Un servicio personalizado consulta esta tabla para calcular un presupuesto preciso, considerando la cantidad, la complejidad del bordado (ej. número de puntadas) y los márgenes de ganancia.
    

## 5. Stack Tecnológico

- **E-commerce Headless:** **Medusa.js**
    
- **Base de Datos y BaaS:** **Supabase**
    
- **Automatización:** **n8n**
    
- **Frontend:** **Next.js / React**
    

## 6. Estructura de la Base de Datos (en Supabase)

### Tablas Principales Gestionadas por Medusa

(Se mantienen las tablas `product`, `product_option`, `product_variant`, `order`)

**`line_item` (Artículo del Pedido)**

- **`metadata`: `JSONB`**
    
    - **Ejemplo de valor para `metadata` en un pedido corporativo:**
        
        ```
        {
          "embroidery_enabled": true,
          "embroidery_logo_ref": "storage/logos/colegio_san_andres.svg",
          "embroidery_notes": "Confirmar Pantone 347C para el verde.",
          "department": "Administración"
        }
        ```
        

### Tablas Personalizadas (Esenciales para este modelo)

**`material_costs` (Tabla Personalizada)**

- Para almacenar los costos actualizados de los insumos.
    
- **Campos:**
    
    - `id`: `uuid` (Primary Key)
        
    - `material_name`: `text` (ej. "Hilo de Poliéster Verde Botella")
        
    - `supplier`: `text` (ej. "Proveedor Hilos Alfa")
        
    - `cost_per_unit`: `decimal`
        
    - `unit`: `text` (ej. "cono de 5000m", "metro", "unidad")
        
    - `last_updated`: `timestamp with time zone`
        

**`embroidery_designs` (Tabla Personalizada)**

- Para almacenar logos de clientes y diseños.
    
- **Campos:**
    
    - `id`: `uuid` (Primary Key)
        
    - `customer_id`: `text` (fk a `customer.id` de Medusa)
        
    - `name`: `text` (ej. "Logo Colegio San Andrés")
        
    - `svg_path`: `text` (ruta al archivo en Supabase Storage)
        
    - `stitch_count`: `integer` (para calcular el costo de bordado)
        
    - `is_active`: `boolean`