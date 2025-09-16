# Sistema de Reservas con Pagos Parciales - Julia Confecciones

import sqlite3
from datetime import datetime, timedelta
import hashlib
import random
import string

class ReservationSystem:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Inicializar la base de datos con el esquema de reservas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabla de Clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
                rut TEXT UNIQUE,
                nombre TEXT,
                email TEXT,
                celular TEXT,
                direccion TEXT,
                tipo_cliente TEXT DEFAULT 'regular',
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                ultima_compra DATETIME,
                total_compras REAL DEFAULT 0,
                descuento_frecuente REAL DEFAULT 0,
                estado TEXT DEFAULT 'activo'
            )
        ''')

        # Tabla de Reservas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reservas (
                id_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER,
                id_producto INTEGER,
                fecha_reserva DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_vencimiento DATETIME,
                monto_total REAL,
                monto_reserva REAL,
                monto_pendiente REAL,
                estado TEXT DEFAULT 'pendiente',
                codigo_cupon TEXT,
                descuento_aplicado REAL,
                notas TEXT,
                FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente)
            )
        ''')

        # Tabla de Pagos de Reservas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pagos_reservas (
                id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
                id_reserva INTEGER,
                monto REAL,
                metodo_pago TEXT,
                fecha_pago DATETIME DEFAULT CURRENT_TIMESTAMP,
                comprobante TEXT,
                estado TEXT DEFAULT 'confirmado',
                FOREIGN KEY (id_reserva) REFERENCES reservas (id_reserva)
            )
        ''')

        # Tabla de Cupones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cupones (
                id_cupon INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE,
                tipo_descuento TEXT,
                valor_descuento REAL,
                tipo_cupon TEXT,
                fecha_inicio DATETIME,
                fecha_vencimiento DATETIME,
                usos_maximos INTEGER,
                usos_actuales INTEGER DEFAULT 0,
                estado TEXT DEFAULT 'activo'
            )
        ''')

        conn.commit()
        conn.close()

    def generar_codigo_cupon(self, longitud=8):
        """Generar código de cupón aleatorio"""
        caracteres = string.ascii_uppercase + string.digits
        return ''.join(random.choice(caracteres) for _ in range(longitud))

    def crear_cliente(self, rut, nombre, email, celular, direccion=""):
        """Crear nuevo cliente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO clientes (rut, nombre, email, celular, direccion)
                VALUES (?, ?, ?, ?, ?)
            ''', (rut, nombre, email, celular, direccion))

            conn.commit()
            cliente_id = cursor.lastrowid
            conn.close()
            return {"success": True, "cliente_id": cliente_id}
        except sqlite3.IntegrityError:
            conn.close()
            return {"success": False, "error": "RUT ya existe"}

    def crear_reserva(self, id_cliente, id_producto, monto_total,
                     porcentaje_reserva=50, codigo_cupon=None, notas=""):
        """Crear nueva reserva con pago parcial"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calcular montos
        monto_reserva = monto_total * (porcentaje_reserva / 100)
        descuento = 0

        # Aplicar cupón si existe
        if codigo_cupon:
            cupon_info = self.validar_cupon(codigo_cupon)
            if cupon_info["valid"]:
                if cupon_info["tipo"] == "porcentaje":
                    descuento = monto_total * (cupon_info["valor"] / 100)
                else:
                    descuento = cupon_info["valor"]

        # Aplicar descuento de cliente frecuente
        cliente_info = self.obtener_cliente(id_cliente)
        if cliente_info and cliente_info["descuento_frecuente"] > 0:
            descuento_frecuente = monto_total * (cliente_info["descuento_frecuente"] / 100)
            descuento += descuento_frecuente

        monto_final = max(0, monto_total - descuento)
        monto_reserva_final = monto_final * (porcentaje_reserva / 100)
        monto_pendiente = monto_final - monto_reserva_final

        # Fecha de vencimiento (7 días)
        fecha_vencimiento = datetime.now() + timedelta(days=7)

        try:
            cursor.execute('''
                INSERT INTO reservas
                (id_cliente, id_producto, fecha_vencimiento, monto_total,
                 monto_reserva, monto_pendiente, estado, codigo_cupon,
                 descuento_aplicado, notas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (id_cliente, id_producto, fecha_vencimiento, monto_total,
                  monto_reserva_final, monto_pendiente, 'pendiente',
                  codigo_cupon, descuento, notas))

            reserva_id = cursor.lastrowid

            # Si se usó cupón, actualizar usos
            if codigo_cupon and cupon_info["valid"]:
                cursor.execute('''
                    UPDATE cupones SET usos_actuales = usos_actuales + 1
                    WHERE codigo = ?
                ''', (codigo_cupon,))

            conn.commit()
            conn.close()

            return {
                "success": True,
                "reserva_id": reserva_id,
                "monto_reserva": monto_reserva_final,
                "monto_pendiente": monto_pendiente,
                "descuento_total": descuento,
                "fecha_vencimiento": fecha_vencimiento
            }

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

    def registrar_pago_reserva(self, id_reserva, monto, metodo_pago, comprobante=""):
        """Registrar pago de reserva"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Registrar pago
            cursor.execute('''
                INSERT INTO pagos_reservas (id_reserva, monto, metodo_pago, comprobante)
                VALUES (?, ?, ?, ?)
            ''', (id_reserva, monto, metodo_pago, comprobante))

            # Actualizar estado de reserva
            cursor.execute('''
                UPDATE reservas
                SET monto_pendiente = monto_pendiente - ?,
                    estado = CASE
                        WHEN monto_pendiente - ? <= 0 THEN 'completada'
                        ELSE 'confirmada'
                    END
                WHERE id_reserva = ?
            ''', (monto, monto, id_reserva))

            conn.commit()
            conn.close()
            return {"success": True}

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

    def validar_cupon(self, codigo):
        """Validar cupón de descuento"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM cupones
            WHERE codigo = ? AND estado = 'activo'
            AND fecha_inicio <= datetime('now')
            AND fecha_vencimiento >= datetime('now')
            AND usos_actuales < usos_maximos
        ''', (codigo,))

        cupon = cursor.fetchone()
        conn.close()

        if cupon:
            return {
                "valid": True,
                "tipo": cupon[2],  # tipo_descuento
                "valor": cupon[3],  # valor_descuento
                "tipo_cupon": cupon[4]  # tipo_cupon
            }
        return {"valid": False}

    def obtener_cliente(self, id_cliente):
        """Obtener información del cliente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM clientes WHERE id_cliente = ?', (id_cliente,))
        cliente = cursor.fetchone()
        conn.close()

        if cliente:
            return {
                "id_cliente": cliente[0],
                "rut": cliente[1],
                "nombre": cliente[2],
                "email": cliente[3],
                "celular": cliente[4],
                "tipo_cliente": cliente[5],
                "total_compras": cliente[8],
                "descuento_frecuente": cliente[9]
            }
        return None

    def actualizar_cliente_frecuente(self, id_cliente):
        """Actualizar a cliente frecuente basado en compras"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Obtener total de compras
        cursor.execute('SELECT total_compras FROM clientes WHERE id_cliente = ?', (id_cliente,))
        result = cursor.fetchone()

        if result:
            total_compras = result[0]

            # Determinar tipo de cliente y descuento
            if total_compras >= 200000:  # VIP
                tipo_cliente = 'vip'
                descuento = 15.0
            elif total_compras >= 100000:  # Frecuente
                tipo_cliente = 'frecuente'
                descuento = 10.0
            elif total_compras >= 50000:   # Regular con descuento
                tipo_cliente = 'regular'
                descuento = 5.0
            else:
                tipo_cliente = 'regular'
                descuento = 0.0

            # Actualizar cliente
            cursor.execute('''
                UPDATE clientes
                SET tipo_cliente = ?, descuento_frecuente = ?
                WHERE id_cliente = ?
            ''', (tipo_cliente, descuento, id_cliente))

            conn.commit()

        conn.close()

    def listar_reservas_activas(self, id_cliente=None):
        """Listar reservas activas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if id_cliente:
            cursor.execute('''
                SELECT r.*, c.nombre
                FROM reservas r
                JOIN clientes c ON r.id_cliente = c.id_cliente
                WHERE r.id_cliente = ? AND r.estado IN ('pendiente', 'confirmada')
                ORDER BY r.fecha_reserva DESC
            ''', (id_cliente,))
        else:
            cursor.execute('''
                SELECT r.*, c.nombre
                FROM reservas r
                JOIN clientes c ON r.id_cliente = c.id_cliente
                WHERE r.estado IN ('pendiente', 'confirmada')
                ORDER BY r.fecha_reserva DESC
            ''')

        reservas = cursor.fetchall()
        conn.close()

        return [
            {
                "id_reserva": r[0],
                "cliente": r[11],
                "monto_total": r[4],
                "monto_reserva": r[5],
                "monto_pendiente": r[6],
                "estado": r[7],
                "fecha_vencimiento": r[3]
            } for r in reservas
        ]

    def verificar_reservas_vencidas(self):
        """Verificar y actualizar reservas vencidas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE reservas
            SET estado = 'cancelada'
            WHERE estado = 'pendiente'
            AND fecha_vencimiento < datetime('now')
        ''')

        count = cursor.rowcount
        conn.commit()
        conn.close()

        return {"reservas_canceladas": count}

# Ejemplo de uso
if __name__ == "__main__":
    # Inicializar sistema
    sistema = ReservationSystem("julia_confecciones.db")

    # Crear cliente de ejemplo
    resultado = sistema.crear_cliente(
        rut="12345678-9",
        nombre="María González",
        email="maria@email.com",
        celular="987654321"
    )
    print("Cliente creado:", resultado)

    # Crear cupón de ejemplo
    conn = sqlite3.connect("julia_confecciones.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO cupones (codigo, tipo_descuento, valor_descuento, tipo_cupon,
                             fecha_inicio, fecha_vencimiento, usos_maximos)
        VALUES (?, ?, ?, ?, datetime('now'), datetime('now', '+30 days'), ?)
    ''', ("RESERVA10", "porcentaje", 10.0, "reserva", 100))
    conn.commit()
    conn.close()

    # Crear reserva
    reserva = sistema.crear_reserva(
        id_cliente=1,
        id_producto=1001,
        monto_total=50000,
        porcentaje_reserva=50,
        codigo_cupon="RESERVA10"
    )
    print("Reserva creada:", reserva)

    # Registrar pago de reserva
    if reserva["success"]:
        pago = sistema.registrar_pago_reserva(
            id_reserva=reserva["reserva_id"],
            monto=reserva["monto_reserva"],
            metodo_pago="transferencia"
        )
        print("Pago registrado:", pago)

    # Listar reservas activas
    activas = sistema.listar_reservas_activas()
    print("Reservas activas:", activas)