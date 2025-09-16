-- Julia Confecciones - Esquema Completo de Supabase V2
-- Incluye toda la cadena productiva, tributación chilena y gestión operativa

-- Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============ TABLAS DE NEGOCIO LEGADO (Migración desde Access) ============

-- Colegios (Clientes principales)
CREATE TABLE colegios (
    id SERIAL PRIMARY KEY,
    codigo INTEGER NOT NULL UNIQUE,
    descripcion VARCHAR(255) NOT NULL,
    direccion TEXT,
    telefono VARCHAR(50),
    email VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Usuarios del sistema
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL UNIQUE,
    nombre_usuario VARCHAR(255) NOT NULL UNIQUE,
    clave_usuario VARCHAR(255),
    rol VARCHAR(50) DEFAULT 'usuario', -- admin, ventas, produccion, cortador, costurera
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Configuración de la empresa
CREATE TABLE empresa (
    id SERIAL PRIMARY KEY,
    rut VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    giro VARCHAR(255),
    direccion TEXT,
    telefono VARCHAR(50),
    email VARCHAR(255),
    servidor_smtp VARCHAR(255),
    puerto_smtp INTEGER,
    email_from VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============ GESTIÓN DE MATERIALES E INSUMOS (NUEVO) ============

-- Tipos de materiales
CREATE TABLE tipos_materiales (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE, -- 'Tela', 'Hilo', 'Botones', 'Cierres', 'Etiquetas'
    unidad_medida VARCHAR(20) NOT NULL, -- 'metros', 'unidades', 'conos', 'metros_lineales'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Materiales e insumos
CREATE TABLE materiales (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    tipo_material_id INTEGER REFERENCES tipos_materiales(id),
    unidad_medida VARCHAR(20) NOT NULL,
    stock_actual NUMERIC(12,3) DEFAULT 0,
    stock_minimo NUMERIC(12,3) DEFAULT 0,
    precio_referencia NUMERIC(12,2),
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Proveedores
CREATE TABLE proveedores (
    id SERIAL PRIMARY KEY,
    rut VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    contacto VARCHAR(255),
    telefono VARCHAR(50),
    email VARCHAR(255),
    direccion TEXT,
    web VARCHAR(255),
    activo BOOLEAN DEFAULT true,
    scraping_config JSONB, -- Configuración para scraping automático
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Precios de materiales por proveedor (con scraping)
CREATE TABLE precios_materiales (
    id SERIAL PRIMARY KEY,
    material_id INTEGER REFERENCES materiales(id),
    proveedor_id INTEGER REFERENCES proveedores(id),
    precio NUMERIC(12,2) NOT NULL,
    moneda VARCHAR(3) DEFAULT 'CLP',
    fecha_actualizacion TIMESTAMPTZ DEFAULT NOW(),
    fuente VARCHAR(100), -- 'manual', 'scraping', 'api'
    scrap_percentage NUMERIC(5,2) DEFAULT 0, -- Porcentaje de merma
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Órdenes de compra a proveedores
CREATE TABLE ordenes_compra (
    id SERIAL PRIMARY KEY,
    numero INTEGER UNIQUE NOT NULL,
    proveedor_id INTEGER REFERENCES proveedores(id),
    fecha_emision DATE NOT NULL,
    fecha_entrega_estimada DATE,
    estado VARCHAR(20) DEFAULT 'pendiente', -- 'pendiente', 'confirmada', 'recibida', 'cancelada'
    subtotal NUMERIC(12,2) DEFAULT 0,
    iva NUMERIC(12,2) DEFAULT 0,
    total NUMERIC(12,2) DEFAULT 0,
    observaciones TEXT,
    usuario_id INTEGER REFERENCES usuarios(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Detalle de órdenes de compra
CREATE TABLE ordenes_compra_detalle (
    id SERIAL PRIMARY KEY,
    orden_compra_id INTEGER REFERENCES ordenes_compra(id),
    material_id INTEGER REFERENCES materiales(id),
    cantidad NUMERIC(12,3) NOT NULL,
    precio_unitario NUMERIC(12,2) NOT NULL,
    subtotal NUMERIC(12,2) GENERATED ALWAYS AS (cantidad * precio_unitario) STORED,
    cantidad_recibida NUMERIC(12,3) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============ PRODUCTOS Y VARIANTES (Integración con Medusa) ============

-- Productos principales
CREATE TABLE productos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    categoria VARCHAR(100),
    precio_costo NUMERIC(12,2) DEFAULT 0,
    precio_venta NUMERIC(12,2) NOT NULL,
    activo BOOLEAN DEFAULT true,
    medusa_id VARCHAR(100) UNIQUE, -- ID de Medusa para sincronización
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Variantes de productos (tallas, colores)
CREATE TABLE producto_variantes (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER REFERENCES productos(id),
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL, -- 'Polera Azul Manga Corta Talla S'
    talla VARCHAR(20),
    color VARCHAR(50),
    sku VARCHAR(100),
    precio_costo NUMERIC(12,2) DEFAULT 0,
    precio_venta NUMERIC(12,2) NOT NULL,
    stock INTEGER DEFAULT 0,
    medusa_variant_id VARCHAR(100) UNIQUE, -- ID de Medusa
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bill of Materials (Receta de producción por variante)
CREATE TABLE bill_of_materials (
    id SERIAL PRIMARY KEY,
    variante_id INTEGER REFERENCES producto_variantes(id),
    material_id INTEGER REFERENCES materiales(id),
    cantidad_requerida NUMERIC(12,4) NOT NULL, -- Cantidad por unidad de producto
    descripcion_uso TEXT, -- 'Para cuerpo principal', 'Forro interior', etc.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(variante_id, material_id)
);

-- ============ BORDADOS Y DISEÑOS (NUEVO) ============

-- Diseños de bordado aprobados
CREATE TABLE disenos_bordado (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    storage_path VARCHAR(500), -- Ruta en Supabase Storage
    stitch_count INTEGER, -- Conteo de puntadas
    pes_hash VARCHAR(64), -- Hash del archivo PES para integridad
    ancho_mm NUMERIC(8,2),
    alto_mm NUMERIC(8,2),
    colores_necesarios INTEGER,
    estado VARCHAR(20) DEFAULT 'aprobado', -- 'borrador', 'aprobado', 'rechazado'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Configuración de fuentes para bordado de texto
CREATE TABLE fuentes_bordado (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    archivo_fuente VARCHAR(255), -- Archivo de fuente compatible
    altura_mm NUMERIC(6,2) NOT NULL,
    densidad NUMERIC(3,2) DEFAULT 0.4,
    max_puntadas INTEGER DEFAULT 50000,
    activa BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============ VENTAS Y PEDIDOS (Migración + Nuevos campos) ============

-- Ventas (cabecera)
CREATE TABLE ventas (
    id SERIAL PRIMARY KEY,
    nro_documento INTEGER UNIQUE NOT NULL,
    tipo_documento VARCHAR(20) DEFAULT 'boleta', -- 'boleta', 'factura', 'nota_credito'
    fecha DATE NOT NULL,
    cliente_nombre VARCHAR(255) NOT NULL,
    cliente_rut VARCHAR(20),
    cliente_telefono VARCHAR(50),
    cliente_email VARCHAR(255),
    colegio_id INTEGER REFERENCES colegios(id),
    subtotal NUMERIC(12,2) DEFAULT 0,
    descuento_porcentaje NUMERIC(5,2) DEFAULT 0,
    descuento_monto NUMERIC(12,2) DEFAULT 0,
    iva NUMERIC(12,2) DEFAULT 0,
    total NUMERIC(12,2) NOT NULL,
    estado VARCHAR(20) DEFAULT 'pagada', -- 'pendiente', 'pagada', 'cancelada'
    canal_venta VARCHAR(20) DEFAULT 'tienda', -- 'tienda', 'web', 'mercadolibre'
    medusa_order_id VARCHAR(100), -- ID de Medusa para órdenes web
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Detalle de ventas
CREATE TABLE ventas_detalle (
    id SERIAL PRIMARY KEY,
    venta_id INTEGER REFERENCES ventas(id),
    item INTEGER NOT NULL,
    producto_variante_id INTEGER REFERENCES producto_variantes(id),
    cantidad INTEGER NOT NULL,
    precio_unitario NUMERIC(12,2) NOT NULL,
    subtotal NUMERIC(12,2) GENERATED ALWAYS AS (cantidad * precio_unitario) STORED,
    texto_bordado TEXT, -- Personalización de hasta 50 caracteres
    diseno_bordado_id INTEGER REFERENCES disenos_bordado(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============ PRODUCCIÓN Y Trazabilidad (NUEVO) ============

-- Órdenes de trabajo
CREATE TABLE ordenes_trabajo (
    id SERIAL PRIMARY KEY,
    numero VARCHAR(50) UNIQUE NOT NULL,
    tipo VARCHAR(50) NOT NULL, -- 'corte', 'bordado', 'confeccion', 'control_calidad', 'terminado'
    venta_detalle_id INTEGER REFERENCES ventas_detalle(id),
    producto_variante_id INTEGER REFERENCES producto_variantes(id),
    cantidad INTEGER NOT NULL,
    estado VARCHAR(20) DEFAULT 'pendiente', -- 'pendiente', 'en_progreso', 'completado', 'cancelado'
    prioridad VARCHAR(20) DEFAULT 'normal', -- 'baja', 'normal', 'alta', 'urgente'
    asignado_a INTEGER REFERENCES usuarios(id), -- Cortador, costurera, etc.
    fecha_inicio TIMESTAMPTZ,
    fecha_fin TIMESTAMPTZ,
    tiempo_estimado_minutos INTEGER,
    tiempo_real_minutos INTEGER,
    observaciones TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Asignación de materiales a órdenes de trabajo
CREATE TABLE ordenes_trabajo_materiales (
    id SERIAL PRIMARY KEY,
    orden_trabajo_id INTEGER REFERENCES ordenes_trabajo(id),
    material_id INTEGER REFERENCES materiales(id),
    cantidad_asignada NUMERIC(12,3) NOT NULL,
    cantidad_utilizada NUMERIC(12,3) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Control de calidad
CREATE TABLE control_calidad (
    id SERIAL PRIMARY KEY,
    orden_trabajo_id INTEGER REFERENCES ordenes_trabajo(id),
    inspector_id INTEGER REFERENCES usuarios(id),
    resultado VARCHAR(20) NOT NULL, -- 'aprobado', 'rechazado', 'necesita_ajustes'
    observaciones TEXT,
    fotos JSONB[], -- URLs de fotos en Storage
    fecha_inspeccion TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seguimiento de producción por operario
CREATE TABLE produccion_operario (
    id SERIAL PRIMARY KEY,
    orden_trabajo_id INTEGER REFERENCES ordenes_trabajo(id),
    operario_id INTEGER REFERENCES usuarios(id),
    fecha DATE NOT NULL,
    horas_trabajadas NUMERIC(5,2) DEFAULT 0,
    piezas_producidas INTEGER DEFAULT 0,
    pago_por_pieza NUMERIC(10,2),
    pago_total NUMERIC(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============ PAGOS Y TRIBUTACIÓN (NUEVO) ============

-- Pagos
CREATE TABLE pagos (
    id SERIAL PRIMARY KEY,
    venta_id INTEGER REFERENCES ventas(id),
    fecha_pago TIMESTAMPTZ DEFAULT NOW(),
    monto NUMERIC(12,2) NOT NULL,
    metodo_pago VARCHAR(50) NOT NULL, -- 'efectivo', 'transferencia', 'getnet', 'mercadopago'
    referencia VARCHAR(100),
    getnet_payment_id VARCHAR(100), -- ID de Getnet para conciliación
    estado VARCHAR(20) DEFAULT 'completado', -- 'pendiente', 'completado', 'fallido', 'reembolsado'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documentos tributarios electrónicos (SII)
CREATE TABLE documentos_tributarios (
    id SERIAL PRIMARY KEY,
    tipo_documento VARCHAR(20) NOT NULL, -- 'boleta', 'factura', 'nota_credito'
    folio INTEGER NOT NULL,
    venta_id INTEGER REFERENCES ventas(id),
    dte_id VARCHAR(100), -- ID del documento en LibreDTE/SII
    estado VARCHAR(20) DEFAULT 'pendiente', -- 'pendiente', 'emitido', 'rechazado', 'anulado'
    monto_total NUMERIC(12,2) NOT NULL,
    pdf_url VARCHAR(500), -- URL del PDF generado
    xml_url VARCHAR(500), -- URL del XML generado
    fecha_emision TIMESTAMPTZ,
    fecha_acuse_sii TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============ GASTOS OPERACIONALES Y NOMINA (NUEVO) ============

-- Tipos de gastos operativos
CREATE TABLE tipos_gastos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE, -- 'Electricidad', 'Agua', 'Arriendo', 'Mantenimiento'
    cuenta_contable VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Gastos operativos
CREATE TABLE gastos_operativos (
    id SERIAL PRIMARY KEY,
    tipo_gasto_id INTEGER REFERENCES tipos_gastos(id),
    descripcion TEXT,
    monto NUMERIC(12,2) NOT NULL,
    fecha DATE NOT NULL,
    periodo_mes INTEGER NOT NULL,
    periodo_ano INTEGER NOT NULL,
    proveedor_id INTEGER REFERENCES proveedores(id),
    documento_referencia VARCHAR(100),
    comprobante_url VARCHAR(500), -- URL del comprobante en Storage
    estado VARCHAR(20) DEFAULT 'pendiente_pago', -- 'pendiente_pago', 'pagado'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Nómina y remuneraciones
CREATE TABLE nomina (
    id SERIAL PRIMARY KEY,
    periodo_mes INTEGER NOT NULL,
    periodo_ano INTEGER NOT NULL,
    usuario_id INTEGER REFERENCES usuarios(id),
    tipo_contrato VARCHAR(20) NOT NULL, -- 'fijo', 'por_pieza', 'honorarios'
    sueldo_base NUMERIC(12,2),
    horas_extras NUMERIC(5,2),
    valor_hora_extra NUMERIC(10,2),
    piezas_producidas INTEGER,
    valor_por_pieza NUMERIC(10,2),
    bonos NUMERIC(12,2) DEFAULT 0,
    descuentos NUMERIC(12,2) DEFAULT 0,
    total_pagar NUMERIC(12,2) GENERATED ALWAYS AS (
        (sueldo_base + COALESCE(horas_extras * valor_hora_extra, 0) + 
         COALESCE(piezas_producidas * valor_por_pieza, 0) + bonos - descuentos)
    ) STORED,
    estado VARCHAR(20) DEFAULT 'pendiente_pago', -- 'pendiente_pago', 'pagado'
    fecha_pago TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============ CAJA Y MOVIMIENTOS (Migración + Mejoras) ============

-- Arqueo de caja
CREATE TABLE arqueo_caja (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    usuario_id INTEGER REFERENCES usuarios(id),
    hora_inicio TIME,
    hora_termino TIME,
    monto_inicial NUMERIC(12,2) NOT NULL,
    monto_final NUMERIC(12,2) NOT NULL,
    diferencia NUMERIC(12,2) GENERATED ALWAYS AS (monto_final - monto_inicial) STORED,
    observaciones TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Detalle de denominaciones (Caja Chica - migración)
CREATE TABLE caja_denominaciones (
    id SERIAL PRIMARY KEY,
    arqueo_id INTEGER REFERENCES arqueo_caja(id),
    billete_20000 INTEGER DEFAULT 0,
    billete_10000 INTEGER DEFAULT 0,
    billete_5000 INTEGER DEFAULT 0,
    billete_2000 INTEGER DEFAULT 0,
    billete_1000 INTEGER DEFAULT 0,
    moneda_500 INTEGER DEFAULT 0,
    moneda_100 INTEGER DEFAULT 0,
    moneda_50 INTEGER DEFAULT 0,
    moneda_10 INTEGER DEFAULT 0,
    total_calculado NUMERIC(12,2) GENERATED ALWAYS AS (
        (billete_20000 * 20000) + (billete_10000 * 10000) + (billete_5000 * 5000) +
        (billete_2000 * 2000) + (billete_1000 * 1000) + (moneda_500 * 500) +
        (moneda_100 * 100) + (moneda_50 * 50) + (moneda_10 * 10)
    ) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Movimientos varios (retiros/ingresos)
CREATE TABLE movimientos_caja (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    tipo VARCHAR(20) NOT NULL, -- 'retiro', 'ingreso', 'prestamo', 'pago_proveedor'
    concepto TEXT NOT NULL,
    monto NUMERIC(12,2) NOT NULL,
    responsable VARCHAR(255),
    documento_referencia VARCHAR(100),
    estado VARCHAR(20) DEFAULT 'completado',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============ INVENTARIO Y STOCK (Migración + Mejoras) ============

-- Movimientos de inventario
CREATE TABLE movimientos_inventario (
    id SERIAL PRIMARY KEY,
    tipo_movimiento VARCHAR(20) NOT NULL, -- 'entrada', 'salida', 'ajuste', 'transferencia'
    producto_variante_id INTEGER REFERENCES producto_variantes(id),
    material_id INTEGER REFERENCES materiales(id),
    cantidad NUMERIC(12,3) NOT NULL,
    motivo TEXT,
    documento_referencia VARCHAR(100), -- N° de OC, N° de venta, etc.
    usuario_id INTEGER REFERENCES usuarios(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Stock actual (vista materializada para mejor rendimiento)
CREATE MATERIALIZED VIEW stock_actual AS
SELECT 
    COALESCE(pv.id, m.id) as id,
    COALESCE(pv.nombre, m.nombre) as nombre,
    COALESCE(pv.codigo, m.codigo) as codigo,
    COALESCE('producto', 'material') as tipo,
    COALESCE(pv.stock, m.stock_actual) as stock_actual,
    COALESCE(pv.precio_costo, m.precio_referencia) as costo_unitario,
    COALESCE(pv.stock * pv.precio_costo, m.stock_actual * m.precio_referencia) as valor_total
FROM producto_variantes pv
FULL OUTER JOIN materiales m ON 1=0 -- Separar productos de materiales
UNION ALL
SELECT m.id, m.nombre, m.codigo, 'material' as tipo, 
       m.stock_actual, m.precio_referencia, 
       m.stock_actual * m.precio_referencia
FROM materiales m
WHERE m.activo = true;

-- Actualizar vista materializada diariamente
CREATE OR REPLACE FUNCTION refresh_stock_actual()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW stock_actual;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- ============ INTEGRACIONES Y API (NUEVO) ============

-- Configuración de integraciones
CREATE TABLE integraciones (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE, -- 'mercadolibre', 'chatwoot', 'getnet'
    tipo VARCHAR(50) NOT NULL, -- 'marketplace', 'comunicacion', 'pagos'
    activa BOOLEAN DEFAULT true,
    configuracion JSONB NOT NULL, -- API keys, tokens, etc.
    ultima_sincronizacion TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Logs de sincronización
CREATE TABLE sincronizacion_logs (
    id SERIAL PRIMARY KEY,
    integracion_id INTEGER REFERENCES integraciones(id),
    tipo_operacion VARCHAR(50) NOT NULL, -- 'import_productos', 'export_ordenes', etc.
    estado VARCHAR(20) NOT NULL, -- 'exitoso', 'error', 'parcial'
    registros_procesados INTEGER DEFAULT 0,
    registros_error INTEGER DEFAULT 0,
    mensaje_error TEXT,
    duracion_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============ INDICES Y RENDIMIENTO ============

-- Índices principales
CREATE INDEX idx_productos_codigo ON productos(codigo);
CREATE INDEX idx_producto_variantes_sku ON producto_variantes(sku);
CREATE INDEX idx_ventas_fecha ON ventas(fecha);
CREATE INDEX idx_ventas_estado ON ventas(estado);
CREATE INDEX idx_ventas_detalle_venta_id ON ventas_detalle(venta_id);
CREATE INDEX idx_ordenes_trabajo_estado ON ordenes_trabajo(estado);
CREATE INDEX idx_ordenes_trabajo_tipo ON ordenes_trabajo(tipo);
CREATE INDEX idx_materiales_codigo ON materiales(codigo);
CREATE INDEX idx_materiales_stock_minimo ON materiales(stock_actual, stock_minimo);
CREATE INDEX idx_precios_materiales_material_id ON precios_materiales(material_id);
CREATE INDEX idx_pagos_venta_id ON pagos(venta_id);
CREATE INDEX idx_documentos_tributarios_folio ON documentos_tributarios(folio);
CREATE INDEX idx_documentos_tributarios_estado ON documentos_tributarios(estado);

-- Índices para búsquedas de texto
CREATE INDEX idx_colegios_descripcion ON colegios USING gin(descripcion gin_trgm_ops);
CREATE INDEX idx_productos_nombre ON productos USING gin(nombre gin_trgm_ops);
CREATE INDEX idx_materiales_nombre ON materiales USING gin(nombre gin_trgm_ops);

-- ============ SEGURIDAD (RLS) ============

-- Habilitar Row Level Security en tablas críticas
ALTER TABLE ventas ENABLE ROW LEVEL SECURITY;
ALTER TABLE ventas_detalle ENABLE ROW LEVEL SECURITY;
ALTER TABLE productos ENABLE ROW LEVEL SECURITY;
ALTER TABLE materiales ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE pagos ENABLE ROW LEVEL SECURITY;
ALTER TABLE nomina ENABLE ROW LEVEL SECURITY;
ALTER TABLE ordenes_trabajo ENABLE ROW LEVEL SECURITY;

-- Políticas de seguridad (después de crear los roles)
-- CREATE POLICY "Usuarios ven solo sus datos" ON nomina FOR SELECT USING (usuario_id = auth.uid());

-- ============ TRIGGERS Y FUNCIONES AUTOMÁTICAS ============

-- Función para actualizar timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para timestamps automáticos
CREATE TRIGGER update_colegios_updated_at BEFORE UPDATE ON colegios FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_usuarios_updated_at BEFORE UPDATE ON usuarios FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_empresa_updated_at BEFORE UPDATE ON empresa FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_productos_updated_at BEFORE UPDATE ON productos FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_producto_variantes_updated_at BEFORE UPDATE ON producto_variantes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_materiales_updated_at BEFORE UPDATE ON materiales FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_proveedores_updated_at BEFORE UPDATE ON proveedores FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_precios_materiales_updated_at BEFORE UPDATE ON precios_materiales FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ordenes_compra_updated_at BEFORE UPDATE ON ordenes_compra FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ventas_updated_at BEFORE UPDATE ON ventas FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ordenes_trabajo_updated_at BEFORE UPDATE ON ordenes_trabajo FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_integraciones_updated_at BEFORE UPDATE ON integraciones FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_documentos_tributarios_updated_at BEFORE UPDATE ON documentos_tributarios FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Función para actualizar stock automáticamente
CREATE OR REPLACE FUNCTION actualizar_stock_movimiento()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.tipo_movimiento = 'entrada' THEN
        -- Aumentar stock
        IF NEW.producto_variante_id IS NOT NULL THEN
            UPDATE producto_variantes SET stock = stock + NEW.cantidad WHERE id = NEW.producto_variante_id;
        ELSIF NEW.material_id IS NOT NULL THEN
            UPDATE materiales SET stock_actual = stock_actual + NEW.cantidad WHERE id = NEW.material_id;
        END IF;
    ELSIF NEW.tipo_movimiento = 'salida' THEN
        -- Disminuir stock
        IF NEW.producto_variante_id IS NOT NULL THEN
            UPDATE producto_variantes SET stock = stock - NEW.cantidad WHERE id = NEW.producto_variante_id;
        ELSIF NEW.material_id IS NOT NULL THEN
            UPDATE materiales SET stock_actual = stock_actual - NEW.cantidad WHERE id = NEW.material_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_actualizar_stock AFTER INSERT ON movimientos_inventario FOR EACH ROW EXECUTE FUNCTION actualizar_stock_movimiento();

-- ============ VISTAS ÚTILES ============

-- Vista para dashboard de producción
CREATE VIEW dashboard_produccion AS
SELECT 
    ot.id,
    ot.numero,
    ot.tipo,
    ot.estado,
    ot.prioridad,
    u.nombre_usuario as asignado_a,
    pv.nombre as producto,
    ot.cantidad,
    ot.fecha_inicio,
    ot.fecha_fin,
    ot.tiempo_estimado_minutos,
    ot.tiempo_real_minutos,
    CASE 
        WHEN ot.estado = 'completado' THEN 'success'
        WHEN ot.estado = 'en_progreso' THEN 'warning'
        WHEN ot.estado = 'pendiente' THEN 'info'
        ELSE 'secondary'
    END as estado_css
FROM ordenes_trabajo ot
LEFT JOIN usuarios u ON ot.asignado_a = u.id
LEFT JOIN producto_variantes pv ON ot.producto_variante_id = pv.id;

-- Vista para dashboard financiero
CREATE VIEW dashboard_financiero AS
SELECT 
    EXTRACT(MONTH FROM v.fecha) as mes,
    EXTRACT(YEAR FROM v.fecha) as ano,
    COUNT(v.id) as total_ventas,
    SUM(v.total) as monto_total,
    SUM(v.subtotal) as subtotal,
    SUM(v.descuento_monto) as total_descuentos,
    SUM(v.iva) as total_iva,
    AVG(v.total) as ticket_promedio
FROM ventas v 
WHERE v.estado = 'pagada'
GROUP BY EXTRACT(MONTH FROM v.fecha), EXTRACT(YEAR FROM v.fecha)
ORDER BY ano, mes;

-- Vista para gestión de materiales
CREATE VIEW gestion_materiales AS
SELECT 
    m.id,
    m.codigo,
    m.nombre,
    m.descripcion,
    tm.nombre as tipo_material,
    m.unidad_medida,
    m.stock_actual,
    m.stock_minimo,
    m.precio_referencia,
    CASE 
        WHEN m.stock_actual <= m.stock_minimo * 0.5 THEN 'danger'
        WHEN m.stock_actual <= m.stock_minimo THEN 'warning'
        ELSE 'success'
    END as estado_stock,
    (m.stock_actual * m.precio_referencia) as valor_inventario
FROM materiales m
LEFT JOIN tipos_materiales tm ON m.tipo_material_id = tm.id
WHERE m.activo = true;

-- Insertar datos iniciales
INSERT INTO tipos_materiales (nombre, unidad_medida) VALUES 
('Tela', 'metros'),
('Hilo', 'conos'),
('Botones', 'unidades'),
('Cierres', 'unidades'),
('Etiquetas', 'unidades'),
('Hilos bordar', 'metros_lineales');

INSERT INTO tipos_gastos (nombre, cuenta_contable) VALUES 
('Electricidad', 'GASTOS_OPERATIVOS'),
('Agua', 'GASTOS_OPERATIVOS'),
('Arriendo local', 'GASTOS_OPERATIVOS'),
('Mantenimiento equipos', 'GASTOS_OPERATIVOS'),
('Internet', 'GASTOS_OPERATIVOS'),
('Teléfono', 'GASTOS_OPERATIVOS'),
('Seguros', 'GASTOS_OPERATIVOS'),
('Suministros de oficina', 'GASTOS_OPERATIVOS');

INSERT INTO integraciones (nombre, tipo, configuracion) VALUES 
('Getnet', 'pagos', '{"api_key": "", "environment": "sandbox"}'),
('MercadoLibre', 'marketplace', '{"app_id": "", "secret_key": "", "access_token": ""}'),
('Chatwoot', 'comunicacion', '{"base_url": "", "access_token": ""}'),
('LibreDTE', 'tributacion', '{"api_key": "", "ambiente": "certificacion"}');