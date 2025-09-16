-- Esquema de base de datos para Julia Confecciones basado en datos de Access

-- Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tabla de Colegios (Clientes principales)
CREATE TABLE colegios (
    id SERIAL PRIMARY KEY,
    codigo INTEGER NOT NULL UNIQUE,
    descripcion VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de Productos
CREATE TABLE productos (
    id SERIAL PRIMARY KEY,
    codigo NUMERIC NOT NULL UNIQUE,
    descripcion TEXT NOT NULL,
    precio_costo NUMERIC(10,2) DEFAULT 0,
    precio_venta NUMERIC(10,2) NOT NULL,
    cod_cole INTEGER REFERENCES colegios(codigo),
    articulo VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de Artículos por Colegio
CREATE TABLE articulos_colegio (
    id SERIAL PRIMARY KEY,
    colegio_id INTEGER REFERENCES colegios(id),
    articulo_codigo INTEGER NOT NULL,
    descripcion TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de Ventas (Cabecera)
CREATE TABLE ventas (
    id SERIAL PRIMARY KEY,
    nro_doc INTEGER NOT NULL UNIQUE,
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(50),
    fecha DATE NOT NULL,
    celular VARCHAR(50),
    porce NUMERIC(5,2) DEFAULT 0,
    descuento NUMERIC(10,2) DEFAULT 0,
    abono NUMERIC(10,2) DEFAULT 0,
    saldo NUMERIC(10,2) DEFAULT 0,
    total NUMERIC(10,2) NOT NULL,
    boleta_ant VARCHAR(50),
    bordado TEXT,
    tpag1 VARCHAR(50),
    mont1 NUMERIC(10,2) DEFAULT 0,
    tpag2 VARCHAR(50),
    mont2 NUMERIC(10,2) DEFAULT 0,
    estado_reg VARCHAR(1) DEFAULT 'V',
    usuario_ing_reg VARCHAR(100),
    usuario_ult_mod VARCHAR(100),
    fecha_ing_reg TIMESTAMPTZ DEFAULT NOW(),
    fecha_ult_mod TIMESTAMPTZ DEFAULT NOW(),
    nro_cpa VARCHAR(50)
);

-- Tabla de Detalle de Ventas
CREATE TABLE detalle_ventas (
    id SERIAL PRIMARY KEY,
    venta_id INTEGER REFERENCES ventas(id),
    nro_doc INTEGER NOT NULL,
    fecha DATE NOT NULL,
    item INTEGER NOT NULL,
    codigo INTEGER REFERENCES productos(codigo),
    cantidad INTEGER NOT NULL,
    precio NUMERIC(10,2) NOT NULL,
    estado_reg VARCHAR(1) DEFAULT 'V',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de Inventario
CREATE TABLE inventario (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER REFERENCES productos(codigo),
    fecha DATE NOT NULL,
    stock INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de Producción
CREATE TABLE produccion (
    id SERIAL PRIMARY KEY,
    documento VARCHAR(50),
    producto_id INTEGER REFERENCES productos(codigo),
    fecha DATE NOT NULL,
    stock INTEGER NOT NULL,
    origen VARCHAR(255),
    tipo_mov VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de Movimientos de Inventario
CREATE TABLE movimientos_inventario (
    id SERIAL PRIMARY KEY,
    documento VARCHAR(50),
    producto_id INTEGER REFERENCES productos(codigo),
    fecha DATE NOT NULL,
    stock INTEGER NOT NULL,
    origen VARCHAR(255),
    tipo_mov VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de Usuarios
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL UNIQUE,
    nombre_usuario VARCHAR(255) NOT NULL UNIQUE,
    clave_usuario VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de Empresa
CREATE TABLE empresa (
    id SERIAL PRIMARY KEY,
    nreg INTEGER,
    rut VARCHAR(20),
    nombre VARCHAR(255),
    email VARCHAR(255),
    servidor VARCHAR(255),
    puerto INTEGER,
    email_desde VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de Parámetros
CREATE TABLE parametros (
    id SERIAL PRIMARY KEY,
    mes INTEGER,
    ano INTEGER,
    ficha VARCHAR(50),
    email VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de Caja Chica
CREATE TABLE caja_chica (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    b20 INTEGER DEFAULT 0,
    b10 INTEGER DEFAULT 0,
    b5 INTEGER DEFAULT 0,
    b2 INTEGER DEFAULT 0,
    b1 INTEGER DEFAULT 0,
    m500 INTEGER DEFAULT 0,
    m100 INTEGER DEFAULT 0,
    m50 INTEGER DEFAULT 0,
    m10 INTEGER DEFAULT 0,
    total NUMERIC(12,2) GENERATED ALWAYS AS (
        (b20 * 20000) + (b10 * 10000) + (b5 * 5000) + (b2 * 2000) + (b1 * 1000) +
        (m500 * 500) + (m100 * 100) + (m50 * 50) + (m10 * 10)
    ) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de Retiros/Ingresos
CREATE TABLE retiros_ingresos (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    item INTEGER,
    hora TIME,
    concepto TEXT,
    monto NUMERIC(10,2),
    responsable VARCHAR(255),
    tipo VARCHAR(20) CHECK (tipo IN ('retiro', 'ingreso')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de Tipos de Venta
CREATE TABLE tipos_venta (
    id SERIAL PRIMARY KEY,
    codigo INTEGER NOT NULL UNIQUE,
    descripcion VARCHAR(255) NOT NULL,
    monto NUMERIC(10,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de Correlativos
CREATE TABLE correlativos (
    id SERIAL PRIMARY KEY,
    caja VARCHAR(10) NOT NULL,
    ult_num INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de Entregas
CREATE TABLE entregas (
    id SERIAL PRIMARY KEY,
    num_doc VARCHAR(50),
    pedido VARCHAR(50),
    fecha DATE NOT NULL,
    cliente VARCHAR(255),
    celular VARCHAR(50),
    alumno VARCHAR(255),
    colegio_id INTEGER REFERENCES colegios(id),
    prendas TEXT,
    trabajo TEXT,
    pago NUMERIC(10,2),
    saldo NUMERIC(10,2),
    ubicacion TEXT,
    fec_entrega DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de Planes de Movimientos
CREATE TABLE planes_mov (
    id SERIAL PRIMARY KEY,
    codigo INTEGER NOT NULL UNIQUE,
    glosa TEXT,
    cargo_fijo NUMERIC(10,2) DEFAULT 0,
    descue NUMERIC(10,2) DEFAULT 0,
    descripcion TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de Correos Enviados
CREATE TABLE correos_enviados (
    id SERIAL PRIMARY KEY,
    numreg INTEGER,
    mes INTEGER,
    ano INTEGER,
    convenio VARCHAR(50),
    ficha VARCHAR(50),
    rut VARCHAR(20),
    nombre VARCHAR(255),
    email VARCHAR(255),
    fecha DATE NOT NULL,
    tipo VARCHAR(50),
    estado VARCHAR(50),
    hora TIME,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Crear índices para mejor rendimiento
CREATE INDEX idx_productos_codigo ON productos(codigo);
CREATE INDEX idx_ventas_fecha ON ventas(fecha);
CREATE INDEX idx_ventas_nro_doc ON ventas(nro_doc);
CREATE INDEX idx_detalle_ventas_nro_doc ON detalle_ventas(nro_doc);
CREATE INDEX idx_detalle_ventas_codigo ON detalle_ventas(codigo);
CREATE INDEX idx_inventario_producto_id ON inventario(producto_id);
CREATE INDEX idx_produccion_producto_id ON produccion(producto_id);
CREATE INDEX idx_movimientos_producto_id ON movimientos_inventario(producto_id);
CREATE INDEX idx_colegios_codigo ON colegios(codigo);
CREATE INDEX idx_articulos_colegio_colegio_id ON articulos_colegio(colegio_id);

-- Crear políticas de seguridad (RLS)
ALTER TABLE productos ENABLE ROW LEVEL SECURITY;
ALTER TABLE ventas ENABLE ROW LEVEL SECURITY;
ALTER TABLE detalle_ventas ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventario ENABLE ROW LEVEL SECURITY;
ALTER TABLE produccion ENABLE ROW LEVEL SECURITY;
ALTER TABLE movimientos_inventario ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE caja_chica ENABLE ROW LEVEL SECURITY;
ALTER TABLE retiros_ingresos ENABLE ROW LEVEL SECURITY;
ALTER TABLE entregas ENABLE ROW LEVEL SECURITY;

-- Política básica para desarrollo (ajustar en producción)
CREATE POLICY "Allow all access" ON ALL TABLES FOR ALL USING (true) WITH CHECK (true);

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Crear triggers para tablas que tienen updated_at
CREATE TRIGGER update_colegios_updated_at BEFORE UPDATE ON colegios FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_productos_updated_at BEFORE UPDATE ON productos FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_usuarios_updated_at BEFORE UPDATE ON usuarios FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_empresa_updated_at BEFORE UPDATE ON empresa FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_correlativos_updated_at BEFORE UPDATE ON correlativos FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insertar datos iniciales de empresa (si existen)
-- Esto se debe completar con los datos reales del archivo empresa.csv