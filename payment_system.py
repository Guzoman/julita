# Sistema de Pagos a Proveedores y Empleados - Julia Confecciones

import sqlite3
from datetime import datetime, timedelta
import json

class PaymentSystem:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Inicializar base de datos para sistema de pagos"""
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

        # Tabla de Pagos a Empleados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pagos_empleados (
                id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
                id_empleado INTEGER,
                tipo_pago TEXT,
                monto REAL,
                cantidad_prendas INTEGER DEFAULT 0,
                periodo_pago TEXT,
                fecha_pago DATETIME DEFAULT CURRENT_TIMESTAMP,
                metodo_pago TEXT,
                estado TEXT DEFAULT 'pagado',
                comprobante TEXT,
                FOREIGN KEY (id_empleado) REFERENCES empleados (id_empleado)
            )
        ''')

        # Tabla de Proveedores de Materiales
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proveedores_materiales (
                id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
                rut TEXT UNIQUE,
                nombre TEXT,
                email TEXT,
                celular TEXT,
                direccion TEXT,
                tipo_material TEXT,
                forma_pago TEXT,
                credito_dias INTEGER DEFAULT 0,
                estado TEXT DEFAULT 'activo'
            )
        ''')

        # Tabla de Compras a Proveedores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compras_proveedores (
                id_compra INTEGER PRIMARY KEY AUTOINCREMENT,
                id_proveedor INTEGER,
                id_material INTEGER,
                cantidad REAL,
                precio_unitario REAL,
                total REAL,
                fecha_compra DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_pago DATETIME,
                fecha_vencimiento DATETIME,
                estado_pago TEXT DEFAULT 'pendiente',
                metodo_pago TEXT,
                comprobante TEXT,
                notas TEXT,
                FOREIGN KEY (id_proveedor) REFERENCES proveedores_materiales (id_proveedor)
            )
        ''')

        # Tabla de Cuentas por Pagar
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cuentas_por_pagar (
                id_cuenta INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_cuenta TEXT, -- 'empleado', 'proveedor'
                id_referencia INTEGER,
                monto REAL,
                fecha_vencimiento DATETIME,
                fecha_pago DATETIME,
                estado TEXT DEFAULT 'pendiente',
                prioridad TEXT DEFAULT 'normal',
                FOREIGN KEY (id_referencia) REFERENCES proveedores_materiales (id_proveedor)
            )
        ''')

        # Tabla de Configuración de Pagos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracion_pagos (
                id_config INTEGER PRIMARY KEY AUTOINCREMENT,
                concepto TEXT,
                tipo_empleado TEXT,
                tipo_pago TEXT, -- 'fijo', 'variable', 'mixto'
                valor REAL,
                periodicidad TEXT, -- 'mensual', 'quincenal', 'semanal', 'por_prenda'
                condiciones TEXT,
                estado TEXT DEFAULT 'activo'
            )
        ''')

        conn.commit()
        conn.close()

    def registrar_proveedor_material(self, rut, nombre, email, celular, direccion,
                                   tipo_material, forma_pago, credito_dias=0):
        """Registrar proveedor de materiales"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO proveedores_materiales
                (rut, nombre, email, celular, direccion, tipo_material, forma_pago, credito_dias)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (rut, nombre, email, celular, direccion, tipo_material, forma_pago, credito_dias))

            proveedor_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {"success": True, "proveedor_id": proveedor_id}

        except sqlite3.IntegrityError:
            conn.close()
            return {"success": False, "error": "RUT ya existe"}

    def registrar_compra_proveedor(self, id_proveedor, id_material, cantidad,
                                  precio_unitario, metodo_pago, comprobante="",
                                  credito_dias=0, notas=""):
        """Registrar compra a proveedor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            total = cantidad * precio_unitario
            fecha_vencimiento = None

            if credito_dias > 0:
                fecha_vencimiento = datetime.now() + timedelta(days=credito_dias)
                estado_pago = 'pendiente'
            else:
                estado_pago = 'pagado'

            cursor.execute('''
                INSERT INTO compras_proveedores
                (id_proveedor, id_material, cantidad, precio_unitario, total,
                 metodo_pago, comprobante, fecha_vencimiento, estado_pago, notas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (id_proveedor, id_material, cantidad, precio_unitario, total,
                  metodo_pago, comprobante, fecha_vencimiento, estado_pago, notas))

            compra_id = cursor.lastrowid

            # Si es a crédito, registrar en cuentas por pagar
            if estado_pago == 'pendiente':
                cursor.execute('''
                    INSERT INTO cuentas_por_pagar
                    (tipo_cuenta, id_referencia, monto, fecha_vencimiento, prioridad)
                    VALUES ('proveedor', ?, ?, ?, 'normal')
                ''', (id_proveedor, total, fecha_vencimiento))

            conn.commit()
            conn.close()

            return {"success": True, "compra_id": compra_id}

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

    def calcular_sueldo_empleado(self, id_empleado, periodo_inicio, periodo_fin):
        """Calcular sueldo de empleado incluyendo pago por prendas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Obtener información del empleado
        cursor.execute('SELECT * FROM empleados WHERE id_empleado = ?', (id_empleado,))
        empleado = cursor.fetchone()

        if not empleado:
            conn.close()
            return {"success": False, "error": "Empleado no encontrado"}

        # Calcular prendas completadas en el período
        cursor.execute('''
            SELECT COUNT(*) as total_prendas
            FROM produccion p
            WHERE (p.id_cortador = ? OR p.id_costurero = ?)
            AND ((p.estado_corte = 'completado' AND p.id_cortador = ?)
                 OR (p.estado_costura = 'completado' AND p.id_costurero = ?))
            AND p.fecha_entrega_corte BETWEEN ? AND ?
            AND p.estado_pago_corte = 'pendiente'
        ''', (id_empleado, id_empleado, id_empleado, id_empleado, periodo_inicio, periodo_fin))

        prendas_result = cursor.fetchone()
        total_prendas = prendas_result[0] if prendas_result else 0

        # Calcular montos
        sueldo_fijo = empleado[5] or 0
        precio_prenda = empleado[6] or 0
        pago_prendas = total_prendas * precio_prenda
        total_sueldo = sueldo_fijo + pago_prendas

        conn.close()

        return {
            "success": True,
            "empleado": empleado[2],
            "sueldo_fijo": sueldo_fijo,
            "total_prendas": total_prendas,
            "precio_prenda": precio_prenda,
            "pago_prendas": pago_prendas,
            "total_sueldo": total_sueldo
        }

    def generar_planilla_pagos(self, periodo_pago):
        """Generar planilla de pagos para empleados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Obtener todos los empleados activos
        cursor.execute('SELECT id_empleado FROM empleados WHERE estado = "activo"')
        empleados = cursor.fetchall()

        planilla = []

        for emp in empleados:
            id_empleado = emp[0]
            calculo = self.calcular_sueldo_empleado(id_empleado, periodo_inicio, periodo_fin)

            if calculo["success"]:
                planilla.append({
                    "id_empleado": id_empleado,
                    "nombre": calculo["empleado"],
                    "sueldo_fijo": calculo["sueldo_fijo"],
                    "total_prendas": calculo["total_prendas"],
                    "pago_prendas": calculo["pago_prendas"],
                    "total_sueldo": calculo["total_sueldo"],
                    "periodo_pago": periodo_pago
                })

        conn.close()
        return planilla

    def procesar_pago_empleado(self, id_empleado, monto, tipo_pago, periodo_pago,
                             metodo_pago="transferencia", comprobante=""):
        """Procesar pago a empleado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Registrar pago
            cursor.execute('''
                INSERT INTO pagos_empleados
                (id_empleado, tipo_pago, monto, periodo_pago, metodo_pago, comprobante)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (id_empleado, tipo_pago, monto, periodo_pago, metodo_pago, comprobante))

            # Actualizar estados de pago de producción si es pago por prendas
            if tipo_pago == 'prendas':
                cursor.execute('''
                    UPDATE produccion
                    SET estado_pago_corte = 'pagado'
                    WHERE id_cortador = ?
                    AND estado_pago_corte = 'pendiente'
                ''', (id_empleado,))

                cursor.execute('''
                    UPDATE produccion
                    SET estado_pago_costura = 'pagado'
                    WHERE id_costurero = ?
                    AND estado_pago_costura = 'pendiente'
                ''', (id_empleado,))

            conn.commit()
            conn.close()

            return {"success": True, "mensaje": "Pago procesado exitosamente"}

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

    def procesar_pago_proveedor(self, id_compra, metodo_pago, comprobante=""):
        """Procesar pago a proveedor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Actualizar estado de compra
            cursor.execute('''
                UPDATE compras_proveedores
                SET estado_pago = 'pagado', fecha_pago = datetime('now'),
                    metodo_pago = ?, comprobante = ?
                WHERE id_compra = ?
            ''', (metodo_pago, comprobante, id_compra))

            # Eliminar de cuentas por pagar
            cursor.execute('''
                DELETE FROM cuentas_por_pagar
                WHERE tipo_cuenta = 'proveedor' AND id_referencia IN (
                    SELECT id_proveedor FROM compras_proveedores WHERE id_compra = ?
                )
            ''', (id_compra,))

            conn.commit()
            conn.close()

            return {"success": True, "mensaje": "Pago a proveedor procesado exitosamente"}

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

    def obtener_cuentas_por_pagar(self, dias=7):
        """Obtener cuentas por pagar próximas a vencer"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        fecha_limite = datetime.now() + timedelta(days=dias)

        cursor.execute('''
            SELECT cpp.*, pm.nombre, pm.rut
            FROM cuentas_por_pagar cpp
            JOIN proveedores_materiales pm ON cpp.id_referencia = pm.id_proveedor
            WHERE cpp.estado = 'pendiente'
            AND cpp.fecha_vencimiento <= ?
            ORDER BY cpp.fecha_vencimiento ASC
        ''', (fecha_limite,))

        cuentas = cursor.fetchall()
        conn.close()

        return [
            {
                "id_cuenta": c[0],
                "tipo_cuenta": c[1],
                "proveedor": c[8],
                "rut_proveedor": c[9],
                "monto": c[3],
                "fecha_vencimiento": c[4],
                "prioridad": c[6]
            } for c in cuentas
        ]

    def generar_reporte_pagos(self, fecha_inicio, fecha_fin):
        """Generar reporte de pagos realizados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Pagos a empleados
        cursor.execute('''
            SELECT 'empleado' as tipo, e.nombre, pe.monto, pe.tipo_pago,
                   pe.fecha_pago, pe.metodo_pago
            FROM pagos_empleados pe
            JOIN empleados e ON pe.id_empleado = e.id_empleado
            WHERE pe.fecha_pago BETWEEN ? AND ?
        ''', (fecha_inicio, fecha_fin))

        pagos_empleados = cursor.fetchall()

        # Pagos a proveedores
        cursor.execute('''
            SELECT 'proveedor' as tipo, pm.nombre, cp.total, 'compra' as tipo_pago,
                   cp.fecha_pago, cp.metodo_pago
            FROM compras_proveedores cp
            JOIN proveedores_materiales pm ON cp.id_proveedor = pm.id_proveedor
            WHERE cp.fecha_pago BETWEEN ? AND ?
            AND cp.estado_pago = 'pagado'
        ''', (fecha_inicio, fecha_fin))

        pagos_proveedores = cursor.fetchall()

        conn.close()

        return {
            "pagos_empleados": [
                {
                    "tipo": p[0],
                    "nombre": p[1],
                    "monto": p[2],
                    "tipo_pago": p[3],
                    "fecha_pago": p[4],
                    "metodo_pago": p[5]
                } for p in pagos_empleados
            ],
            "pagos_proveedores": [
                {
                    "tipo": p[0],
                    "nombre": p[1],
                    "monto": p[2],
                    "tipo_pago": p[3],
                    "fecha_pago": p[4],
                    "metodo_pago": p[5]
                } for p in pagos_proveedores
            ]
        }

    def configurar_pago_automatico(self, concepto, tipo_empleado, tipo_pago,
                                  valor, periodicidad, condiciones=""):
        """Configurar pago automático"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO configuracion_pagos
                (concepto, tipo_empleado, tipo_pago, valor, periodicidad, condiciones)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (concepto, tipo_empleado, tipo_pago, valor, periodicidad, condiciones))

            conn.commit()
            conn.close()

            return {"success": True, "mensaje": "Configuración guardada exitosamente"}

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

    def verificar_pagos_pendientes(self):
        """Verificar pagos pendientes y generar alertas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        alertas = []

        # Verificar cuentas por pagar vencidas
        cursor.execute('''
            SELECT cpp.id_cuenta, pm.nombre, cpp.monto, cpp.fecha_vencimiento,
                   JULIANDAY('now') - JULIANDAY(cpp.fecha_vencimiento) as dias_vencido
            FROM cuentas_por_pagar cpp
            JOIN proveedores_materiales pm ON cpp.id_referencia = pm.id_proveedor
            WHERE cpp.estado = 'pendiente'
            AND cpp.fecha_vencimiento < datetime('now')
            ORDER BY dias_vencido DESC
        ''')

        vencidas = cursor.fetchall()
        for v in vencidas:
            alertas.append({
                "tipo": "cuenta_vencida",
                "id": v[0],
                "proveedor": v[1],
                "monto": v[2],
                "dias_vencido": int(v[4]),
                "prioridad": "alta"
            })

        # Verificar cuentas próximas a vencer
        cursor.execute('''
            SELECT cpp.id_cuenta, pm.nombre, cpp.monto, cpp.fecha_vencimiento,
                   JULIANDAY(cpp.fecha_vencimiento) - JULIANDAY('now') as dias_para_vencer
            FROM cuentas_por_pagar cpp
            JOIN proveedores_materiales pm ON cpp.id_referencia = pm.id_proveedor
            WHERE cpp.estado = 'pendiente'
            AND cpp.fecha_vencimiento BETWEEN datetime('now') AND datetime('now', '+7 days')
            ORDER BY dias_para_vencer ASC
        ''')

        proximas = cursor.fetchall()
        for p in proximas:
            alertas.append({
                "tipo": "cuenta_proxima_vencer",
                "id": p[0],
                "proveedor": p[1],
                "monto": p[2],
                "dias_para_vencer": int(p[4]),
                "prioridad": "media"
            })

        conn.close()
        return alertas

# Ejemplo de uso
if __name__ == "__main__":
    # Inicializar sistema
    sistema = PaymentSystem("julia_confecciones.db")

    # Registrar proveedor
    print("Registrando proveedor...")
    proveedor = sistema.registrar_proveedor_material(
        rut="33333333-3", nombre="Textiles ABC", email="abc@textiles.com",
        celular="933333333", direccion="Av. Principal 123",
        tipo_material="tela", forma_pago="transferencia", credito_dias=30
    )
    print("Proveedor registrado:", proveedor)

    # Registrar compra
    print("Registrando compra...")
    compra = sistema.registrar_compra_proveedor(
        id_proveedor=proveedor["proveedor_id"],
        id_material=1,
        cantidad=100,
        precio_unitario=4500,
        metodo_pago="credito",
        credito_dias=30,
        notas="Compra de tela algodón"
    )
    print("Compra registrada:", compra)

    # Calcular sueldo de empleado
    print("Calculando sueldo de empleado...")
    sueldo = sistema.calcular_sueldo_empleado(1, "2024-01-01", "2024-01-31")
    print("Sueldo calculado:", sueldo)

    # Verificar cuentas por pagar
    print("Cuentas por pagar:")
    cuentas = sistema.obtener_cuentas_por_pagar(dias=30)
    for cuenta in cuentas:
        print(f"{cuenta['proveedor']} - ${cuenta['monto']:.2f} - Vence: {cuenta['fecha_vencimiento']}")

    # Generar alertas
    print("Alertas de pagos:")
    alertas = sistema.verificar_pagos_pendientes()
    for alerta in alertas:
        print(f"{alerta['tipo']}: {alerta.get('proveedor', '')} - ${alerta['monto']:.2f}")