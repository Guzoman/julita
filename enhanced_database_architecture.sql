# Enhanced Architecture for Julia Confecciones Management System

## Overview
Enhanced database architecture designed to support the complete business workflow including reservations, frequent customer management, production tracking, material management, and provider payments.

## Core Tables Structure

### 1. Clientes (Enhanced Customer Management)
```sql
CREATE TABLE Clientes (
    id_cliente INT PRIMARY KEY AUTO_INCREMENT,
    rut VARCHAR(15) UNIQUE,
    nombre VARCHAR(100),
    email VARCHAR(100),
    celular VARCHAR(20),
    direccion TEXT,
    tipo_cliente ENUM('regular', 'frecuente', 'vip') DEFAULT 'regular',
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    ultima_compra DATETIME,
    total_compras DECIMAL(12,2) DEFAULT 0,
    descuento_frecuente DECIMAL(5,2) DEFAULT 0,
    estado ENUM('activo', 'inactivo') DEFAULT 'activo'
);
```

### 2. Reservas (Reservation System)
```sql
CREATE TABLE Reservas (
    id_reserva INT PRIMARY KEY AUTO_INCREMENT,
    id_cliente INT,
    id_producto INT,
    fecha_reserva DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_vencimiento DATETIME,
    monto_total DECIMAL(12,2),
    monto_reserva DECIMAL(12,2),
    monto_pendiente DECIMAL(12,2),
    estado ENUM('pendiente', 'confirmada', 'cancelada', 'completada') DEFAULT 'pendiente',
    codigo_cupon VARCHAR(20),
    descuento_aplicado DECIMAL(5,2),
    notas TEXT,
    FOREIGN KEY (id_cliente) REFERENCES Clientes(id_cliente),
    FOREIGN KEY (id_producto) REFERENCES Productos(id_producto)
);
```

### 3. Pagos_Reservas (Reservation Payments)
```sql
CREATE TABLE Pagos_Reservas (
    id_pago INT PRIMARY KEY AUTO_INCREMENT,
    id_reserva INT,
    monto DECIMAL(12,2),
    metodo_pago ENUM('efectivo', 'transferencia', 'tarjeta', 'getnet'),
    fecha_pago DATETIME DEFAULT CURRENT_TIMESTAMP,
    comprobante VARCHAR(100),
    estado ENUM('confirmado', 'pendiente') DEFAULT 'confirmado',
    FOREIGN KEY (id_reserva) REFERENCES Reservas(id_reserva)
);
```

### 4. Materiales (Materials Management)
```sql
CREATE TABLE Materiales (
    id_material INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100),
    tipo ENUM('tela', 'hilo', 'boton', 'elastico', 'otro'),
    unidad_medida VARCHAR(20),
    stock_actual DECIMAL(10,2),
    stock_minimo DECIMAL(10,2),
    costo_unitario DECIMAL(10,2),
    proveedor VARCHAR(100),
    fecha_ultimo_ingreso DATETIME,
    estado ENUM('activo', 'inactivo') DEFAULT 'activo'
);
```

### 5. Produccion (Enhanced Production Tracking)
```sql
CREATE TABLE Produccion (
    id_produccion INT PRIMARY KEY AUTO_INCREMENT,
    id_orden INT, -- Referencia a venta o reserva
    tipo_orden ENUM('venta', 'reserva'),
    id_cortador INT,
    id_costurero INT,
    fecha_asignacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_entrega_corte DATETIME,
    fecha_entrega_costura DATETIME,
    estado_corte ENUM('pendiente', 'en_proceso', 'completado', 'entregado'),
    estado_costura ENUM('pendiente', 'en_proceso', 'completado', 'entregado'),
    pago_corte DECIMAL(10,2),
    pago_costura DECIMAL(10,2),
    estado_pago_corte ENUM('pendiente', 'pagado'),
    estado_pago_costura ENUM('pendiente', 'pagado'),
    notas TEXT,
    FOREIGN KEY (id_cortador) REFERENCES Empleados(id_empleado),
    FOREIGN KEY (id_costurero) REFERENCES Empleados(id_empleado)
);
```

### 6. Detalle_Produccion_Materiales (Production Material Usage)
```sql
CREATE TABLE Detalle_Produccion_Materiales (
    id_detalle INT PRIMARY KEY AUTO_INCREMENT,
    id_produccion INT,
    id_material INT,
    cantidad_utilizada DECIMAL(10,2),
    fecha_uso DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_produccion) REFERENCES Produccion(id_produccion),
    FOREIGN KEY (id_material) REFERENCES Materiales(id_material)
);
```

### 7. Empleados (Enhanced Employee Management)
```sql
CREATE TABLE Empleados (
    id_empleado INT PRIMARY KEY AUTO_INCREMENT,
    rut VARCHAR(15) UNIQUE,
    nombre VARCHAR(100),
    email VARCHAR(100),
    celular VARCHAR(20),
    tipo_empleado ENUM('vendedor', 'cortador', 'costurero', 'administrativo'),
    sueldo_fijo DECIMAL(10,2),
    precio_prenda DECIMAL(10,2), -- Para cortadores y costureros
    fecha_contratacion DATE,
    estado ENUM('activo', 'inactivo') DEFAULT 'activo',
    codigo_acceso VARCHAR(50) UNIQUE -- Para páginas de seguimiento
);
```

### 8. Pagos_Empleados (Employee Payment Tracking)
```sql
CREATE TABLE Pagos_Empleados (
    id_pago_empleado INT PRIMARY KEY AUTO_INCREMENT,
    id_empleado INT,
    tipo_pago ENUM('sueldo', 'prendas'),
    monto DECIMAL(10,2),
    cantidad_prendas INT DEFAULT 0,
    periodo_pago VARCHAR(20), -- Ej: "2024-01"
    fecha_pago DATETIME DEFAULT CURRENT_TIMESTAMP,
    metodo_pago ENUM('efectivo', 'transferencia'),
    estado ENUM('pagado', 'pendiente') DEFAULT 'pagado',
    FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
);
```

### 9. Cupones (Discount Coupons)
```sql
CREATE TABLE Cupones (
    id_cupon INT PRIMARY KEY AUTO_INCREMENT,
    codigo VARCHAR(20) UNIQUE,
    tipo_descuento ENUM('porcentaje', 'monto_fijo'),
    valor_descuento DECIMAL(10,2),
    tipo_cupon ENUM('reserva', 'frecuente', 'promocion'),
    fecha_inicio DATETIME,
    fecha_vencimiento DATETIME,
    usos_maximos INT,
    usos_actuales INT DEFAULT 0,
    estado ENUM('activo', 'inactivo') DEFAULT 'activo'
);
```

### 10. Seguimiento_Produccion (Production Tracking Portal)
```sql
CREATE TABLE Seguimiento_Produccion (
    id_seguimiento INT PRIMARY KEY AUTO_INCREMENT,
    id_produccion INT,
    id_empleado INT,
    fecha_acceso DATETIME DEFAULT CURRENT_TIMESTAMP,
    accion ENUM('visualizado', 'iniciado', 'completado', 'entregado'),
    notas TEXT,
    FOREIGN KEY (id_produccion) REFERENCES Produccion(id_produccion),
    FOREIGN KEY (id_empleado) REFERENCES Empleados(id_empleado)
);
```

## Enhanced Existing Tables

### Productos (Enhanced)
```sql
ALTER TABLE Productos
ADD COLUMN (
    materiales_requeridos TEXT, -- JSON con detalles de materiales needed
    tiempo_produccion_estimado INT, -- minutos
    requiere_corte BOOLEAN DEFAULT TRUE,
    requiere_costura BOOLEAN DEFAULT TRUE,
    costo_produccion DECIMAL(10,2),
    estado ENUM('activo', 'descontinuado') DEFAULT 'activo'
);
```

### Ventas (Enhanced)
```sql
ALTER TABLE Ventas
ADD COLUMN (
    id_reserva INT NULL, -- Para vincular con reservas
    tipo_venta ENUM('directa', 'reserva') DEFAULT 'directa',
    id_produccion INT NULL,
    FOREIGN KEY (id_reserva) REFERENCES Reservas(id_reserva),
    FOREIGN KEY (id_produccion) REFERENCES Produccion(id_produccion)
);
```

## Key Features Implemented

1. **Reservation System**: 50% payment option with coupon support
2. **Frequent Customer Management**: Automatic upgrades and discounts
3. **Production Tracking**: Complete workflow from materials to finished products
4. **Material Management**: Track consumption and reordering
5. **Employee Payment System**: Fixed salary + per-garment payments
6. **Production Portal**: Individual tracking pages for workers
7. **Comprehensive Reporting**: Full business analytics

## Security Considerations

- Employee access codes for tracking portals
- Secure payment processing integration
- Role-based access control
- Audit trail for all transactions

## Integration Points

- Payment gateway integration (GetNet, Transbank)
- Email notification system
- SMS notifications for production status
- Inventory management system
- Accounting system integration