# Julia Confecciones - Database Mapping Analysis

## Field-Level Mapping: Access to Supabase

### 1. Schools Management (Colegios)

#### Access: Colegios
| Access Field | Type | Supabase Field | Type | Notes |
|-------------|------|----------------|------|-------|
| codigo | INT(10) | codigo | INTEGER NOT NULL UNIQUE | Direct mapping |
| descripcion | VARCHAR(255) | descripcion | VARCHAR(255) NOT NULL | Direct mapping |
| | | direccion | TEXT | New field |
| | | telefono | VARCHAR(50) | New field |
| | | email | VARCHAR(255) | New field |
| | | created_at | TIMESTAMPTZ | Audit field |
| | | updated_at | TIMESTAMPTZ | Audit field |

**Business Rules**:
- Schools are primary B2B customers
- Each school has unique code
- Schools drive product catalogs and pricing

### 2. Product Management

#### Access: productos → Supabase: productos + producto_variantes

**Main Products Table**:
| Access Field | Type | Supabase Field | Type | Notes |
|-------------|------|----------------|------|-------|
| codigo | FLOAT | codigo | VARCHAR(50) UNIQUE | Changed to string for flexibility |
| descripcion | VARCHAR(255) | nombre | VARCHAR(255) NOT NULL | Renamed for clarity |
| | | descripcion | TEXT | Extended description |
| | | categoria | VARCHAR(100) | New field for categorization |
| precio_costo | INT | precio_costo | NUMERIC(12,2) | Decimal precision |
| Precio_venta | FLOAT | precio_venta | NUMERIC(12,2) NOT NULL | Decimal precision |
| cod_cole | INT | colegio_id | INTEGER REFERENCES colegios(id) | Foreign key relationship |
| articulo | VARCHAR(255) | | | Merged into descripcion |
| | | activo | BOOLEAN DEFAULT true | New field |
| | | medusa_id | VARCHAR(100) UNIQUE | E-commerce integration |
| | | created_at | TIMESTAMPTZ | Audit field |
| | | updated_at | TIMESTAMPTZ | Audit field |

**Product Variants Table**:
| Access Field | Type | Supabase Field | Type | Notes |
|-------------|------|----------------|------|-------|
| descripcion (contains size) | VARCHAR(255) | nombre | VARCHAR(255) NOT NULL | Extracted size info |
| | | talla | VARCHAR(20) | Normalized size field |
| | | color | VARCHAR(50) | New field |
| | | sku | VARCHAR(100) | New field for inventory |
| precio_costo | INT | precio_costo | NUMERIC(12,2) | Decimal precision |
| Precio_venta | FLOAT | precio_venta | NUMERIC(12,2) NOT NULL | Decimal precision |
| | | stock | INTEGER DEFAULT 0 | Real-time stock tracking |
| | | medusa_variant_id | VARCHAR(100) UNIQUE | E-commerce integration |
| | | created_at | TIMESTAMPTZ | Audit field |
| | | updated_at | TIMESTAMPTZ | Audit field |

**Business Rules**:
- Products belong to schools
- Size variants have individual pricing
- Stock managed at variant level
- Integration with e-commerce platform

### 3. Sales Management

#### Access: Ventas → Supabase: ventas

| Access Field | Type | Supabase Field | Type | Notes |
|-------------|------|----------------|------|-------|
| Nro_doc | FLOAT | nro_documento | INTEGER UNIQUE NOT NULL | Changed to integer |
| | | tipo_documento | VARCHAR(20) DEFAULT 'boleta' | New field |
| Fecha | DATETIME | fecha | DATE NOT NULL | Changed to date only |
| Nombre | VARCHAR(255) | cliente_nombre | VARCHAR(255) NOT NULL | Renamed |
| | | cliente_rut | VARCHAR(20) | New field |
| | | cliente_telefono | VARCHAR(50) | New field |
| | | cliente_email | VARCHAR(255) | New field |
| | | colegio_id | INTEGER REFERENCES colegios(id) | Foreign key relationship |
| | | subtotal | NUMERIC(12,2) DEFAULT 0 | Calculated field |
| porce | DECIMAL | descuento_porcentaje | NUMERIC(5,2) DEFAULT 0 | Renamed |
| Descuento | INT | descuento_monto | NUMERIC(12,2) DEFAULT 0 | Decimal precision |
| | | iva | NUMERIC(12,2) DEFAULT 0 | New field for tax |
| Total | INT | total | NUMERIC(12,2) NOT NULL | Decimal precision |
| | | estado | VARCHAR(20) DEFAULT 'pagada' | New field |
| | | canal_venta | VARCHAR(20) DEFAULT 'tienda' | New field |
| | | medusa_order_id | VARCHAR(100) | E-commerce integration |
| | | created_at | TIMESTAMPTZ | Audit field |
| | | updated_at | TIMESTAMPTZ | Audit field |

**Payment Fields Mapping**:
| Access Field | Type | Supabase Field | Type | Notes |
|-------------|------|----------------|------|-------|
| Tipo | VARCHAR(255) | | | Moved to pagos table |
| Abono | INT | | | Moved to pagos table |
| Saldo | INT | | | Calculated from pagos |
| tpag1, mont1, tpag2, mont2 | Various | | | Normalized to pagos table |

**Business Rules**:
- Split payments supported
- Discount management
- Multiple payment channels
- Tax calculation support
- Order status tracking

#### Access: Detalle_vta → Supabase: ventas_detalle

| Access Field | Type | Supabase Field | Type | Notes |
|-------------|------|----------------|------|-------|
| Nro_doc | FLOAT | venta_id | INTEGER REFERENCES ventas(id) | Foreign key relationship |
| fecha | DATETIME | | | Use ventas.fecha |
| Item | FLOAT | item | INTEGER NOT NULL | Direct mapping |
| Codigo | INT | producto_variante_id | INTEGER REFERENCES producto_variantes(id) | Foreign key relationship |
| Cantidad | INT | cantidad | INTEGER NOT NULL | Direct mapping |
| Precio | INT | precio_unitario | NUMERIC(12,2) NOT NULL | Decimal precision |
| Estado_reg | VARCHAR(255) | | | Status managed at header level |
| | | subtotal | NUMERIC(12,2) | Calculated field |
| | | texto_bordado | TEXT | New field for customization |
| | | diseno_bordado_id | INTEGER REFERENCES disenos_bordado(id) | New relationship |
| | | created_at | TIMESTAMPTZ | Audit field |

**Business Rules**:
- Line items reference product variants
- Embroidery customization support
- Price preservation at time of sale
- Automatic subtotal calculation

### 4. Inventory Management

#### Access: Inventarios → Supabase: stock_actual (materialized view)

| Access Field | Type | Supabase Field | Type | Notes |
|-------------|------|----------------|------|-------|
| codigo | INT | codigo | VARCHAR(50) | Reference to product/material |
| fecha | DATETIME | | | Real-time tracking |
| stock | INT | stock_actual | INTEGER | Real-time calculation |

**Business Rules**:
- Real-time stock calculation
- Combined view of products and materials
- Automatic stock updates from movements

#### Access: EntradasSalidas → Supabase: movimientos_inventario

| Access Field | Type | Supabase Field | Type | Notes |
|-------------|------|----------------|------|-------|
| Documento | INT | documento_referencia | VARCHAR(100) | Reference field |
| codigo | INT | producto_variante_id OR material_id | INTEGER | Foreign key relationship |
| fecha | DATETIME | created_at | TIMESTAMPTZ | Timestamp |
| stock | INT | cantidad | NUMERIC(12,3) NOT NULL | Decimal precision |
| Origen | VARCHAR(255) | motivo | TEXT | Purpose description |
| Tipo_mov | VARCHAR(255) | tipo_movimiento | VARCHAR(20) NOT NULL | Normalized types |
| | | usuario_id | INTEGER REFERENCES usuarios(id) | Audit trail |

**Business Rules**:
- Automatic stock updates
- Comprehensive audit trail
- Support for both products and materials
- User responsibility tracking

### 5. Production Management

#### Access: Produccion → Supabase: ordenes_trabajo + produccion_operario

**Work Orders**:
| Access Field | Type | Supabase Field | Type | Notes |
|-------------|------|----------------|------|-------|
| Documento | INT | numero | VARCHAR(50) UNIQUE NOT NULL | Changed to string |
| codigo | INT | producto_variante_id | INTEGER REFERENCES producto_variantes(id) | Foreign key relationship |
| fecha | DATETIME | | | Use created_at |
| stock | INT | cantidad | INTEGER NOT NULL | Direct mapping |
| Origen | VARCHAR(255) | | | Use venta_detalle_id reference |
| Tipo_mov | VARCHAR(255) | tipo | VARCHAR(50) NOT NULL | Normalized types |
| | | venta_detalle_id | INTEGER REFERENCES ventas_detalle(id) | Source reference |
| | | estado | VARCHAR(20) DEFAULT 'pendiente' | Workflow management |
| | | prioridad | VARCHAR(20) DEFAULT 'normal' | Priority management |
| | | asignado_a | INTEGER REFERENCES usuarios(id) | Worker assignment |
| | | fecha_inicio | TIMESTAMPTZ | Workflow tracking |
| | | fecha_fin | TIMESTAMPTZ | Workflow tracking |
| | | tiempo_estimado_minutos | INTEGER | Planning field |
| | | tiempo_real_minutos | INTEGER | Performance tracking |
| | | observaciones | TEXT | Notes field |
| | | created_at | TIMESTAMPTZ | Audit field |
| | | updated_at | TIMESTAMPTZ | Audit field |

**Worker Production**:
| Access Field | Type | Supabase Field | Type | Notes |
|-------------|------|----------------|------|-------|
| Origen | VARCHAR(255) | operario_id | INTEGER REFERENCES usuarios(id) | Worker reference |
| | | fecha | DATE NOT NULL | Date tracking |
| | | horas_trabajadas | NUMERIC(5,2) DEFAULT 0 | Time tracking |
| stock | INT | piezas_producidas | INTEGER DEFAULT 0 | Production output |
| | | pago_por_pieza | NUMERIC(10,2) | Piece rate calculation |
| | | pago_total | NUMERIC(10,2) | Total payment |
| | | created_at | TIMESTAMPTZ | Audit field |

**Business Rules**:
- Comprehensive workflow management
- Worker performance tracking
- Time and piece rate payment
- Priority-based scheduling

### 6. Cash Management

#### Access: Caja_Chica → Supabase: arqueo_caja + caja_denominaciones

**Cash Count**:
| Access Field | Type | Supabase Field | Type | Notes |
|-------------|------|----------------|------|-------|
| Fecha | DATETIME | fecha | DATE NOT NULL | Changed to date |
| | | usuario_id | INTEGER REFERENCES usuarios(id) | Responsibility |
| | | hora_inicio | TIME | Time tracking |
| | | hora_termino | TIME | Time tracking |
| | | monto_inicial | NUMERIC(12,2) NOT NULL | Opening balance |
| | | monto_final | NUMERIC(12,2) NOT NULL | Closing balance |
| | | diferencia | NUMERIC(12,2) | Calculated field |
| | | observaciones | TEXT | Notes field |
| | | created_at | TIMESTAMPTZ | Audit field |

**Denominations**:
| Access Field | Type | Supabase Field | Type | Notes |
|-------------|------|----------------|------|-------|
| B20, B10, B5, B2, B1 | Various | billete_20000, billete_10000, etc. | INTEGER | Normalized naming |
| M500, M100, M50, M10 | Various | moneda_500, moneda_100, etc. | INTEGER | Normalized naming |
| | | total_calculado | NUMERIC(12,2) | Calculated field |
| | | created_at | TIMESTAMPTZ | Audit field |

**Business Rules**:
- Daily cash reconciliation
- Denomination-level tracking
- User responsibility assignment
- Automatic difference calculation

### 7. User Management

#### Access: Usuarios → Supabase: usuarios

| Access Field | Type | Supabase Field | Type | Notes |
|-------------|------|----------------|------|-------|
| id_usuario | VARCHAR(255) | id_usuario | INTEGER NOT NULL UNIQUE | Changed to integer |
| nombre_usuario | VARCHAR(255) | nombre_usuario | VARCHAR(255) NOT NULL UNIQUE | Direct mapping |
| clave_usuario | VARCHAR(255) | clave_usuario | VARCHAR(255) | Password field |
| | | rol | VARCHAR(50) DEFAULT 'usuario' | Role-based access |
| | | activo | BOOLEAN DEFAULT true | Account status |
| | | created_at | TIMESTAMPTZ | Audit field |
| | | updated_at | TIMESTAMPTZ | Audit field |

**Business Rules**:
- Role-based access control
- User activation/deactivation
- Comprehensive audit trail

### 8. Company Configuration

#### Access: Empresa → Supabase: empresa

| Access Field | Type | Supabase Field | Type | Notes |
|-------------|------|----------------|------|-------|
| Rut | VARCHAR(15) | rut | VARCHAR(20) UNIQUE NOT NULL | Direct mapping |
| Nombre | VARCHAR(50) | nombre | VARCHAR(255) NOT NULL | Extended length |
| | | giro | VARCHAR(255) | Business activity |
| | | direccion | TEXT | Address field |
| | | telefono | VARCHAR(50) | Contact field |
| Email | VARCHAR(50) | email | VARCHAR(255) | Contact field |
| Servidor | VARCHAR(255) | servidor_smtp | VARCHAR(255) | SMTP configuration |
| Puerto | INT | puerto_smtp | INTEGER | SMTP configuration |
| EmailDesde | VARCHAR(255) | email_from | VARCHAR(255) | Email configuration |
| | | created_at | TIMESTAMPTZ | Audit field |
| | | updated_at | TIMESTAMPTZ | Audit field |

**Business Rules**:
- Company-wide configuration
- Email server setup
- Contact information management

### 9. New Tables in Supabase (No Access Equivalent)

#### Materials Management
- **tipos_materiales**: Material categories
- **materiales**: Raw materials inventory
- **proveedores**: Supplier management
- **precios_materiales**: Supplier pricing
- **ordenes_compra**: Purchase orders
- **ordenes_compra_detalle**: Purchase order details

#### Embroidery Management
- **disenos_bordado**: Embroidery designs
- **fuentes_bordado**: Font configurations

#### Bill of Materials
- **bill_of_materials**: Production recipes

#### Quality Control
- **control_calidad**: Quality inspections

#### Financial Management
- **pagos**: Payment processing
- **documentos_tributarios**: Tax documents
- **tipos_gastos**: Expense categories
- **gastos_operativos**: Operating expenses
- **nomina**: Payroll management

#### Integration
- **integraciones**: Third-party integrations
- **sincronizacion_logs**: Integration logs

#### Enhanced Features
- **movimientos_caja**: Cash movements
- **produccion_operario**: Worker performance
- **ordenes_trabajo_materiales**: Material assignment

## Business Logic Migration

### 1. School-Specific Pricing
**Access Logic**: Products linked to schools via `cod_cole` field
**Supabase Implementation**: Foreign key relationship with proper validation

### 2. Size-Based Variants
**Access Logic**: Size embedded in product description
**Supabase Implementation**: Normalized variant structure with separate size field

### 3. Embroidery Customization
**Access Logic**: Text stored in memo field
**Supabase Implementation**: Structured embroidery tracking with design references

### 4. Multi-Payment Support
**Access Logic**: Multiple payment fields in sales header
**Supabase Implementation**: Normalized payment table supporting unlimited payment methods

### 5. Inventory Tracking
**Access Logic**: Periodic inventory snapshots
**Supabase Implementation**: Real-time stock calculation with movement tracking

### 6. Production Workflow
**Access Logic**: Basic production logging
**Supabase Implementation**: Comprehensive workflow management with worker assignment

### 7. Cash Management
**Access Logic**: Daily denomination counting
**Supabase Implementation**: Enhanced cash reconciliation with responsibility tracking

## Data Migration Strategy

### Phase 1: Core Data
1. **colegios**: Direct migration with contact info enhancement
2. **productos**: Split into main products and variants
3. **ventas**: Migrate header data with proper normalization
4. **detalle_vta**: Migrate line items with foreign key relationships

### Phase 2: Operational Data
1. **inventarios**: Convert to real-time stock calculation
2. **produccion**: Migrate to work order system
3. **caja_chica**: Convert to cash management system
4. **usuarios**: Migrate with role assignment

### Phase 3: Historical Data
1. **respaldo_ventas**: Archive historical sales data
2. **correoenviado**: Archive email history
3. **creditos/ctascorr**: Migrate to modern credit management
4. **parametros**: Convert to system configuration

### Data Quality Improvements
1. **Code Standardization**: Ensure consistent product/school codes
2. **Data Validation**: Implement proper data type constraints
3. **Relationship Integrity**: Establish proper foreign key relationships
4. **Audit Trail**: Implement comprehensive change tracking

## Migration Success Metrics

### Technical Metrics
- **Data Integrity**: 100% referential integrity
- **Performance**: Sub-second response times
- **Uptime**: 99.9% availability
- **Data Loss**: Zero data loss during migration

### Business Metrics
- **User Adoption**: 90% user satisfaction
- **Process Efficiency**: 30% reduction in manual processes
- **Reporting**: Real-time dashboard access
- **Integration**: Successful connection with e-commerce platform

### Risk Mitigation
- **Data Backup**: Comprehensive backup before migration
- **Rollback Plan**: Immediate rollback capability
- **Parallel Running**: Old system available during transition
- **User Training**: Comprehensive training program

This mapping provides a comprehensive blueprint for migrating from the legacy Access system to the modern Supabase architecture while preserving all business logic and enhancing system capabilities.