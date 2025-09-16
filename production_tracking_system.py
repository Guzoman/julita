# Sistema de Seguimiento de Producción y Materiales - Julia Confecciones

import sqlite3
from datetime import datetime, timedelta
import json
import uuid

class ProductionTrackingSystem:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Inicializar base de datos para seguimiento de producción"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabla de Empleados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS empleados (
                id_empleado INTEGER PRIMARY KEY AUTOINCREMENT,
                rut TEXT UNIQUE,
                nombre TEXT,
                email TEXT,
                celular TEXT,
                tipo_empleado TEXT,
                sueldo_fijo REAL,
                precio_prenda REAL,
                fecha_contratacion DATE,
                estado TEXT DEFAULT 'activo',
                codigo_acceso TEXT UNIQUE
            )
        ''')

        # Tabla de Materiales
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS materiales (
                id_material INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                tipo TEXT,
                unidad_medida TEXT,
                stock_actual REAL DEFAULT 0,
                stock_minimo REAL DEFAULT 0,
                costo_unitario REAL DEFAULT 0,
                proveedor TEXT,
                fecha_ultimo_ingreso DATETIME,
                estado TEXT DEFAULT 'activo'
            )
        ''')

        # Tabla de Producción
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produccion (
                id_produccion INTEGER PRIMARY KEY AUTOINCREMENT,
                id_orden INTEGER,
                tipo_orden TEXT,
                id_cortador INTEGER,
                id_costurero INTEGER,
                fecha_asignacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_entrega_corte DATETIME,
                fecha_entrega_costura DATETIME,
                estado_corte TEXT DEFAULT 'pendiente',
                estado_costura TEXT DEFAULT 'pendiente',
                pago_corte REAL DEFAULT 0,
                pago_costura REAL DEFAULT 0,
                estado_pago_corte TEXT DEFAULT 'pendiente',
                estado_pago_costura TEXT DEFAULT 'pendiente',
                notas TEXT,
                FOREIGN KEY (id_cortador) REFERENCES empleados (id_empleado),
                FOREIGN KEY (id_costurero) REFERENCES empleados (id_empleado)
            )
        ''')

        # Tabla de Detalle de Materiales por Producción
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detalle_produccion_materiales (
                id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
                id_produccion INTEGER,
                id_material INTEGER,
                cantidad_utilizada REAL,
                fecha_uso DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_produccion) REFERENCES produccion (id_produccion),
                FOREIGN KEY (id_material) REFERENCES materiales (id_material)
            )
        ''')

        # Tabla de Seguimiento de Producción
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS seguimiento_produccion (
                id_seguimiento INTEGER PRIMARY KEY AUTOINCREMENT,
                id_produccion INTEGER,
                id_empleado INTEGER,
                fecha_acceso DATETIME DEFAULT CURRENT_TIMESTAMP,
                accion TEXT,
                notas TEXT,
                FOREIGN KEY (id_produccion) REFERENCES produccion (id_produccion),
                FOREIGN KEY (id_empleado) REFERENCES empleados (id_empleado)
            )
        ''')

        # Tabla de Compras de Materiales
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compras_materiales (
                id_compra INTEGER PRIMARY KEY AUTOINCREMENT,
                id_material INTEGER,
                cantidad_comprada REAL,
                costo_total REAL,
                proveedor TEXT,
                fecha_compra DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_recepcion DATETIME,
                estado TEXT DEFAULT 'pendiente',
                comprobante TEXT
            )
        ''')

        # Tabla de Envíos a Proveedores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS envios_proveedores (
                id_envio INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_proveedor TEXT, -- 'cortador', 'costurero'
                id_proveedor INTEGER,
                id_produccion INTEGER,
                fecha_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_recepcion DATETIME,
                estado_envio TEXT DEFAULT 'enviado',
                estado_recepcion TEXT DEFAULT 'pendiente',
                notas TEXT,
                FOREIGN KEY (id_proveedor) REFERENCES empleados (id_empleado),
                FOREIGN KEY (id_produccion) REFERENCES produccion (id_produccion)
            )
        ''')

        conn.commit()
        conn.close()

    def generar_codigo_acceso(self):
        """Generar código de acceso único para empleados"""
        return str(uuid.uuid4())[:8].upper()

    def registrar_empleado(self, rut, nombre, email, celular, tipo_empleado,
                          sueldo_fijo=0, precio_prenda=0):
        """Registrar nuevo empleado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            codigo_acceso = self.generar_codigo_acceso()

            cursor.execute('''
                INSERT INTO empleados
                (rut, nombre, email, celular, tipo_empleado, sueldo_fijo, precio_prenda, codigo_acceso)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (rut, nombre, email, celular, tipo_empleado, sueldo_fijo, precio_prenda, codigo_acceso))

            empleado_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {
                "success": True,
                "empleado_id": empleado_id,
                "codigo_acceso": codigo_acceso
            }

        except sqlite3.IntegrityError:
            conn.close()
            return {"success": False, "error": "RUT ya existe"}

    def registrar_material(self, nombre, tipo, unidad_medida, stock_actual=0,
                          stock_minimo=0, costo_unitario=0, proveedor=""):
        """Registrar nuevo material"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO materiales
                (nombre, tipo, unidad_medida, stock_actual, stock_minimo, costo_unitario, proveedor)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (nombre, tipo, unidad_medida, stock_actual, stock_minimo, costo_unitario, proveedor))

            material_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {"success": True, "material_id": material_id}

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

    def crear_orden_produccion(self, id_orden, tipo_orden, detalles_productos,
                               id_cortador=None, id_costurero=None):
        """Crear orden de producción"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Crear orden principal
            cursor.execute('''
                INSERT INTO produccion
                (id_orden, tipo_orden, id_cortador, id_costurero)
                VALUES (?, ?, ?, ?)
            ''', (id_orden, tipo_orden, id_cortador, id_costurero))

            id_produccion = cursor.lastrowid

            # Registrar materiales requeridos
            for detalle in detalles_productos:
                id_material = detalle['id_material']
                cantidad = detalle['cantidad']

                # Verificar stock disponible
                cursor.execute('''
                    SELECT stock_actual FROM materiales WHERE id_material = ?
                ''', (id_material,))

                result = cursor.fetchone()
                if result and result[0] >= cantidad:
                    # Descontar del stock
                    cursor.execute('''
                        UPDATE materiales
                        SET stock_actual = stock_actual - ?
                        WHERE id_material = ?
                    ''', (cantidad, id_material))

                    # Registrar uso en producción
                    cursor.execute('''
                        INSERT INTO detalle_produccion_materiales
                        (id_produccion, id_material, cantidad_utilizada)
                        VALUES (?, ?, ?)
                    ''', (id_produccion, id_material, cantidad))
                else:
                    conn.rollback()
                    conn.close()
                    return {"success": False, "error": f"Stock insuficiente para material {id_material}"}

            conn.commit()
            conn.close()

            return {"success": True, "id_produccion": id_produccion}

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

    def enviar_a_corte(self, id_produccion, id_cortador):
        """Enviar orden a corte"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Actualizar producción
            cursor.execute('''
                UPDATE produccion
                SET id_cortador = ?, estado_corte = 'en_proceso'
                WHERE id_produccion = ?
            ''', (id_cortador, id_produccion))

            # Registrar envío
            cursor.execute('''
                INSERT INTO envios_proveedores
                (tipo_proveedor, id_proveedor, id_produccion, estado_envio)
                VALUES (?, ?, ?, 'enviado')
            ''', ('cortador', id_cortador, id_produccion))

            # Registrar seguimiento
            cursor.execute('''
                INSERT INTO seguimiento_produccion
                (id_produccion, id_empleado, accion)
                VALUES (?, ?, 'enviado_a_corte')
            ''', (id_produccion, id_cortador))

            conn.commit()
            conn.close()

            return {"success": True, "mensaje": "Enviado a corte exitosamente"}

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

    def confirmar_recepcion_corte(self, id_produccion, id_cortador, notas=""):
        """Confirmar recepción de corte por parte del cortador"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Actualizar producción
            cursor.execute('''
                UPDATE produccion
                SET estado_corte = 'completado', fecha_entrega_corte = datetime('now')
                WHERE id_produccion = ? AND id_cortador = ?
            ''', (id_produccion, id_cortador))

            # Actualizar envío
            cursor.execute('''
                UPDATE envios_proveedores
                SET estado_recepcion = 'recibido', fecha_recepcion = datetime('now')
                WHERE id_produccion = ? AND id_proveedor = ? AND tipo_proveedor = 'cortador'
            ''', (id_produccion, id_cortador))

            # Registrar seguimiento
            cursor.execute('''
                INSERT INTO seguimiento_produccion
                (id_produccion, id_empleado, accion, notas)
                VALUES (?, ?, 'corte_completado', ?)
            ''', (id_produccion, id_cortador, notas))

            conn.commit()
            conn.close()

            return {"success": True, "mensaje": "Corte completado exitosamente"}

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

    def enviar_a_costura(self, id_produccion, id_costurero):
        """Enviar orden a costura"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Actualizar producción
            cursor.execute('''
                UPDATE produccion
                SET id_costurero = ?, estado_costura = 'en_proceso'
                WHERE id_produccion = ?
            ''', (id_costurero, id_produccion))

            # Registrar envío
            cursor.execute('''
                INSERT INTO envios_proveedores
                (tipo_proveedor, id_proveedor, id_produccion, estado_envio)
                VALUES (?, ?, ?, 'enviado')
            ''', ('costurero', id_costurero, id_produccion))

            # Registrar seguimiento
            cursor.execute('''
                INSERT INTO seguimiento_produccion
                (id_produccion, id_empleado, accion)
                VALUES (?, ?, 'enviado_a_costura')
            ''', (id_produccion, id_costurero))

            conn.commit()
            conn.close()

            return {"success": True, "mensaje": "Enviado a costura exitosamente"}

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

    def confirmar_recepcion_costura(self, id_produccion, id_costurero, notas=""):
        """Confirmar recepción de costura por parte del costurero"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Actualizar producción
            cursor.execute('''
                UPDATE produccion
                SET estado_costura = 'completado', fecha_entrega_costura = datetime('now')
                WHERE id_produccion = ? AND id_costurero = ?
            ''', (id_produccion, id_costurero))

            # Actualizar envío
            cursor.execute('''
                UPDATE envios_proveedores
                SET estado_recepcion = 'recibido', fecha_recepcion = datetime('now')
                WHERE id_produccion = ? AND id_proveedor = ? AND tipo_proveedor = 'costurero'
            ''', (id_produccion, id_costurero))

            # Registrar seguimiento
            cursor.execute('''
                INSERT INTO seguimiento_produccion
                (id_produccion, id_empleado, accion, notas)
                VALUES (?, ?, 'costura_completada', ?)
            ''', (id_produccion, id_costurero, notas))

            conn.commit()
            conn.close()

            return {"success": True, "mensaje": "Costura completada exitosamente"}

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

    def registrar_pago_empleado(self, id_empleado, tipo_pago, monto, cantidad_prendas=0,
                               metodo_pago="efectivo", periodo_pago=""):
        """Registrar pago a empleado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO pagos_empleados
                (id_empleado, tipo_pago, monto, cantidad_prendas, periodo_pago, metodo_pago)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (id_empleado, tipo_pago, monto, cantidad_prendas, periodo_pago, metodo_pago))

            conn.commit()
            conn.close()

            return {"success": True, "mensaje": "Pago registrado exitosamente"}

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

    def obtener_tareas_pendientes_empleado(self, codigo_acceso):
        """Obtener tareas pendientes para un empleado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Verificar empleado
        cursor.execute('SELECT id_empleado, tipo_empleado FROM empleados WHERE codigo_acceso = ?', (codigo_acceso,))
        empleado = cursor.fetchone()

        if not empleado:
            conn.close()
            return {"success": False, "error": "Código de acceso inválido"}

        id_empleado, tipo_empleado = empleado

        if tipo_empleado == 'cortador':
            # Tareas de corte pendientes
            cursor.execute('''
                SELECT p.*, e.nombre as nombre_orden,
                       CASE WHEN p.estado_corte = 'pendiente' THEN 'Pendiente de recepción'
                            WHEN p.estado_corte = 'en_proceso' THEN 'En proceso'
                            ELSE 'Completado'
                       END as estado_descripcion
                FROM produccion p
                LEFT JOIN envios_proveedores ep ON p.id_produccion = ep.id_produccion
                WHERE p.id_cortador = ?
                AND p.estado_corte IN ('pendiente', 'en_proceso')
                ORDER BY p.fecha_asignacion
            ''', (id_empleado,))

        elif tipo_empleado == 'costurero':
            # Tareas de costura pendientes
            cursor.execute('''
                SELECT p.*, e.nombre as nombre_orden,
                       CASE WHEN p.estado_costura = 'pendiente' THEN 'Pendiente de recepción'
                            WHEN p.estado_costura = 'en_proceso' THEN 'En proceso'
                            ELSE 'Completado'
                       END as estado_descripcion
                FROM produccion p
                LEFT JOIN envios_proveedores ep ON p.id_produccion = ep.id_produccion
                WHERE p.id_costurero = ?
                AND p.estado_costura IN ('pendiente', 'en_proceso')
                ORDER BY p.fecha_asignacion
            ''', (id_empleado,))

        tareas = cursor.fetchall()
        conn.close()

        return {
            "success": True,
            "empleado_tipo": tipo_empleado,
            "tareas": [
                {
                    "id_produccion": t[0],
                    "id_orden": t[1],
                    "tipo_orden": t[2],
                    "fecha_asignacion": t[4],
                    "pago_corte": t[8],
                    "pago_costura": t[9],
                    "estado_pago_corte": t[10],
                    "estado_pago_costura": t[11],
                    "notas": t[12],
                    "estado_descripcion": t[13]
                } for t in tareas
            ]
        }

    def generar_reporte_produccion(self, fecha_inicio=None, fecha_fin=None):
        """Generar reporte de producción"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        where_clause = ""
        params = []

        if fecha_inicio and fecha_fin:
            where_clause = "WHERE p.fecha_asignacion BETWEEN ? AND ?"
            params = [fecha_inicio, fecha_fin]

        cursor.execute(f'''
            SELECT
                p.estado_corte,
                p.estado_costura,
                COUNT(*) as total_ordenes,
                SUM(p.pago_corte) as total_pago_corte,
                SUM(p.pago_costura) as total_pago_costura,
                ec.nombre as nombre_cortador,
                es.nombre as nombre_costurero
            FROM produccion p
            LEFT JOIN empleados ec ON p.id_cortador = ec.id_empleado
            LEFT JOIN empleados es ON p.id_costurero = es.id_empleado
            {where_clause}
            GROUP BY p.estado_corte, p.estado_costura, ec.nombre, es.nombre
            ORDER BY p.estado_corte, p.estado_costura
        ''', params)

        reporte = cursor.fetchall()
        conn.close()

        return [
            {
                "estado_corte": r[0],
                "estado_costura": r[1],
                "total_ordenes": r[2],
                "total_pago_corte": r[3],
                "total_pago_costura": r[4],
                "cortador": r[5],
                "costurero": r[6]
            } for r in reporte
        ]

    def verificar_materiales_bajos(self):
        """Verificar materiales con stock bajo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id_material, nombre, stock_actual, stock_minimo, unidad_medida
            FROM materiales
            WHERE stock_actual <= stock_minimo
            AND estado = 'activo'
            ORDER BY (stock_actual - stock_minimo) ASC
        ''')

        materiales = cursor.fetchall()
        conn.close()

        return [
            {
                "id_material": m[0],
                "nombre": m[1],
                "stock_actual": m[2],
                "stock_minimo": m[3],
                "unidad_medida": m[4],
                "diferencia": m[3] - m[2]
            } for m in materiales
        ]

# Ejemplo de uso
if __name__ == "__main__":
    # Inicializar sistema
    sistema = ProductionTrackingSystem("julia_confecciones.db")

    # Registrar empleados
    print("Registrando empleados...")
    cortador = sistema.registrar_empleado(
        rut="11111111-1", nombre="Carlos Cortez", email="carlos@email.com",
        celular="911111111", tipo_empleado="cortador", precio_prenda=5000
    )
    print("Cortador registrado:", cortador)

    costurero = sistema.registrar_empleado(
        rut="22222222-2", nombre="Ana Costura", email="ana@email.com",
        celular="922222222", tipo_empleado="costurero", precio_prenda=8000
    )
    print("Costurero registrada:", costurero)

    # Registrar materiales
    print("Registrando materiales...")
    sistema.registrar_material(
        nombre="Tela Algodón", tipo="tela", unidad_medida="metros",
        stock_actual=100, stock_minimo=20, costo_unitario=5000
    )
    sistema.registrar_material(
        nombre="Hilo Negro", tipo="hilo", unidad_medida="carretes",
        stock_actual=50, stock_minimo=10, costo_unitario=500
    )

    # Crear orden de producción
    print("Creando orden de producción...")
    materiales_requeridos = [
        {"id_material": 1, "cantidad": 5},  # 5 metros de tela
        {"id_material": 2, "cantidad": 2}   # 2 carretes de hilo
    ]

    orden = sistema.crear_orden_produccion(
        id_orden=1001, tipo_orden="venta",
        detalles_productos=materiales_requeridos,
        id_cortador=cortador["empleado_id"],
        id_costurero=costurero["empleado_id"]
    )
    print("Orden creada:", orden)

    # Enviar a corte
    if orden["success"]:
        envio_corte = sistema.enviar_a_corte(
            id_produccion=orden["id_produccion"],
            id_cortador=cortador["empleado_id"]
        )
        print("Envío a corte:", envio_corte)

    # Verificar tareas pendientes
    print("Tareas pendientes del cortador:")
    tareas = sistema.obtener_tareas_pendientes_empleado(cortador["codigo_acceso"])
    print(json.dumps(tareas, indent=2, default=str))

    # Verificar materiales bajos
    print("Materiales con stock bajo:")
    materiales_bajos = sistema.verificar_materiales_bajos()
    print(materiales_bajos)

    # Generar reporte de producción
    print("Reporte de producción:")
    reporte = sistema.generar_reporte_produccion()
    print(reporte)