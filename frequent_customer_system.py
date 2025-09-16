# Sistema de Gestión de Clientes Frecuentes - Julia Confecciones

import sqlite3
from datetime import datetime, timedelta
import json

class FrequentCustomerSystem:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Inicializar tablas de clientes frecuentes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabla de Clientes (si no existe en el sistema principal)
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

        # Tabla de Compras para seguimiento
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compras_cliente (
                id_compra INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER,
                monto_compra REAL,
                fecha_compra DATETIME DEFAULT CURRENT_TIMESTAMP,
                tipo_compra TEXT, -- 'directa', 'reserva'
                id_venta INTEGER, -- Referencia a venta original
                FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente)
            )
        ''')

        # Tabla de Beneficios de Clientes Frecuentes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS beneficios_frecuentes (
                id_beneficio INTEGER PRIMARY KEY AUTOINCREMENT,
                nivel_cliente TEXT,
                tipo_beneficio TEXT, -- 'descuento', 'cupon_exclusivo', 'prioridad'
                valor_beneficio REAL,
                descripcion TEXT,
                condiciones TEXT
            )
        ''')

        # Tabla de Canjeo de Beneficios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS canjeo_beneficios (
                id_canjeo INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER,
                id_beneficio INTEGER,
                fecha_canjeo DATETIME DEFAULT CURRENT_TIMESTAMP,
                estado TEXT DEFAULT 'activo',
                FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente),
                FOREIGN KEY (id_beneficio) REFERENCES beneficios_frecuentes (id_beneficio)
            )
        ''')

        # Insertar beneficios predeterminados
        self.insertar_beneficios_predeterminados(cursor)

        conn.commit()
        conn.close()

    def insertar_beneficios_predeterminados(self, cursor):
        """Insertar beneficios predeterminados si no existen"""
        beneficios = [
            ('regular', 'descuento', 5.0, '5% de descuento en compras', 'Mínimo $50.000 en compras'),
            ('frecuente', 'descuento', 10.0, '10% de descuento en compras', 'Mínimo $100.000 en compras'),
            ('frecuente', 'prioridad', 0, 'Prioridad en producción', 'Mínimo $100.000 en compras'),
            ('vip', 'descuento', 15.0, '15% de descuento en compras', 'Mínimo $200.000 en compras'),
            ('vip', 'prioridad', 0, 'Entrega prioritaria', 'Mínimo $200.000 en compras'),
            ('vip', 'cupon_exclusivo', 20.0, 'Cupón exclusivo 20%', 'Mínimo $200.000 en compras')
        ]

        cursor.executemany('''
            INSERT OR IGNORE INTO beneficios_frecuentes
            (nivel_cliente, tipo_beneficio, valor_beneficio, descripcion, condiciones)
            VALUES (?, ?, ?, ?, ?)
        ''', beneficios)

    def registrar_compra(self, id_cliente, monto_compra, tipo_compra='directa', id_venta=None):
        """Registrar una compra y actualizar estado de cliente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Registrar la compra
            cursor.execute('''
                INSERT INTO compras_cliente (id_cliente, monto_compra, tipo_compra, id_venta)
                VALUES (?, ?, ?, ?)
            ''', (id_cliente, monto_compra, tipo_compra, id_venta))

            # Actualizar total de compras del cliente
            cursor.execute('''
                UPDATE clientes
                SET total_compras = total_compras + ?,
                    ultima_compra = datetime('now')
                WHERE id_cliente = ?
            ''', (monto_compra, id_cliente))

            # Actualizar nivel de cliente frecuente
            self.actualizar_nivel_cliente(cursor, id_cliente)

            conn.commit()
            conn.close()

            return {"success": True, "message": "Compra registrada exitosamente"}

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

    def actualizar_nivel_cliente(self, cursor, id_cliente):
        """Actualizar el nivel de cliente basado en compras"""
        # Obtener total de compras
        cursor.execute('SELECT total_compras FROM clientes WHERE id_cliente = ?', (id_cliente,))
        result = cursor.fetchone()

        if result:
            total_compras = result[0]

            # Determinar nivel y descuento
            if total_compras >= 200000:  # VIP
                nivel = 'vip'
                descuento = 15.0
            elif total_compras >= 100000:  # Frecuente
                nivel = 'frecuente'
                descuento = 10.0
            elif total_compras >= 50000:   # Regular con descuento
                nivel = 'regular'
                descuento = 5.0
            else:
                nivel = 'regular'
                descuento = 0.0

            # Actualizar cliente
            cursor.execute('''
                UPDATE clientes
                SET tipo_cliente = ?, descuento_frecuente = ?
                WHERE id_cliente = ?
            ''', (nivel, descuento, id_cliente))

            # Enviar notificación de upgrade (simulado)
            if nivel in ['frecuente', 'vip']:
                self.enviar_notificacion_upgrade(id_cliente, nivel)

    def enviar_notificacion_upgrade(self, id_cliente, nuevo_nivel):
        """Simular envío de notificación de upgrade"""
        cursor = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT nombre, email FROM clientes WHERE id_cliente = ?', (id_cliente,))
            cliente = cursor.fetchone()

            if cliente:
                nombre, email = cliente

                # Aquí se integraría con un sistema real de email/SMS
                print(f"Notificación enviada a {nombre} ({email}):")
                print(f"¡Felicidades! Has ascendido a cliente {nuevo_nivel}")
                print(f"Ahora disfrutas de descuentos exclusivos y beneficios prioritarios")

        except Exception as e:
            print(f"Error al enviar notificación: {e}")
        finally:
            if cursor:
                conn.close()

    def obtener_beneficios_cliente(self, id_cliente):
        """Obtener beneficios disponibles para un cliente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Obtener nivel del cliente
        cursor.execute('SELECT tipo_cliente FROM clientes WHERE id_cliente = ?', (id_cliente,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return []

        nivel_cliente = result[0]

        # Obtener beneficios para ese nivel
        cursor.execute('''
            SELECT * FROM beneficios_frecuentes
            WHERE nivel_cliente = ?
            ORDER BY tipo_beneficio, valor_beneficio DESC
        ''', (nivel_cliente,))

        beneficios = cursor.fetchall()
        conn.close()

        return [
            {
                "id_beneficio": b[0],
                "nivel": b[1],
                "tipo": b[2],
                "valor": b[3],
                "descripcion": b[4],
                "condiciones": b[5]
            } for b in beneficios
        ]

    def canjear_beneficio(self, id_cliente, id_beneficio):
        """Canjear un beneficio para el cliente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Verificar que el cliente puede acceder a este beneficio
            cursor.execute('''
                SELECT b.*, c.tipo_cliente
                FROM beneficios_frecuentes b
                JOIN clientes c ON b.nivel_cliente = c.tipo_cliente
                WHERE b.id_beneficio = ? AND c.id_cliente = ?
            ''', (id_beneficio, id_cliente))

            beneficio = cursor.fetchone()
            if not beneficio:
                conn.close()
                return {"success": False, "error": "Beneficio no disponible para este cliente"}

            # Registrar canjeo
            cursor.execute('''
                INSERT INTO canjeo_beneficios (id_cliente, id_beneficio)
                VALUES (?, ?)
            ''', (id_cliente, id_beneficio))

            conn.commit()
            conn.close()

            return {
                "success": True,
                "message": f"Beneficio '{beneficio[4]}' canjeado exitosamente"
            }

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

    def obtener_estadisticas_cliente(self, id_cliente):
        """Obtener estadísticas completas del cliente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Información básica del cliente
        cursor.execute('SELECT * FROM clientes WHERE id_cliente = ?', (id_cliente,))
        cliente = cursor.fetchone()

        if not cliente:
            conn.close()
            return None

        # Estadísticas de compras
        cursor.execute('''
            SELECT COUNT(*) as total_compras, AVG(monto_compra) as promedio_compra,
                   MAX(fecha_compra) as ultima_compra
            FROM compras_cliente
            WHERE id_cliente = ?
        ''', (id_cliente,))

        stats = cursor.fetchone()

        # Compras por mes
        cursor.execute('''
            SELECT strftime('%Y-%m', fecha_compra) as mes,
                   SUM(monto_compra) as total_mes,
                   COUNT(*) as cantidad_compras
            FROM compras_cliente
            WHERE id_cliente = ?
            GROUP BY strftime('%Y-%m', fecha_compra)
            ORDER BY mes DESC
            LIMIT 6
        ''', (id_cliente,))

        compras_mensuales = cursor.fetchall()

        conn.close()

        return {
            "cliente": {
                "id": cliente[0],
                "rut": cliente[1],
                "nombre": cliente[2],
                "email": cliente[3],
                "tipo_cliente": cliente[5],
                "total_compras": cliente[8],
                "descuento_frecuente": cliente[9]
            },
            "estadisticas": {
                "total_compras": stats[0],
                "promedio_compra": stats[1],
                "ultima_compra": stats[2]
            },
            "compras_mensuales": [
                {
                    "mes": cm[0],
                    "total": cm[1],
                    "cantidad": cm[2]
                } for cm in compras_mensuales
            ]
        }

    def generar_reporte_clientes_frecuentes(self, fecha_inicio=None, fecha_fin=None):
        """Generar reporte de clientes frecuentes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        where_clause = ""
        params = []

        if fecha_inicio and fecha_fin:
            where_clause = "WHERE c.ultima_compra BETWEEN ? AND ?"
            params = [fecha_inicio, fecha_fin]

        cursor.execute(f'''
            SELECT
                c.tipo_cliente,
                COUNT(*) as cantidad_clientes,
                SUM(c.total_compras) as total_compras,
                AVG(c.total_compras) as promedio_compras,
                c.descuento_frecuente
            FROM clientes c
            {where_clause}
            GROUP BY c.tipo_cliente
            ORDER BY c.descuento_frecuente DESC
        ''', params)

        reporte = cursor.fetchall()
        conn.close()

        return [
            {
                "nivel": r[0],
                "cantidad_clientes": r[1],
                "total_compras": r[2],
                "promedio_compras": r[3],
                "descuento": r[4]
            } for r in reporte
        ]

    def proximos_clientes_upgrade(self):
        """Identificar clientes próximos a subir de nivel"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                id_cliente, nombre, email, total_compras, tipo_cliente,
                CASE
                    WHEN total_compras >= 50000 AND total_compras < 100000 THEN 100000 - total_compras
                    WHEN total_compras >= 100000 AND total_compras < 200000 THEN 200000 - total_compras
                    ELSE NULL
                END as monto_para_siguiente_nivel
            FROM clientes
            WHERE total_compras < 200000
            AND estado = 'activo'
            ORDER BY total_compras DESC
            LIMIT 10
        ''')

        clientes = cursor.fetchall()
        conn.close()

        return [
            {
                "id_cliente": c[0],
                "nombre": c[1],
                "email": c[2],
                "total_compras": c[3],
                "nivel_actual": c[4],
                "monto_para_siguiente_nivel": c[5]
            } for c in clientes if c[5] is not None
        ]

# Ejemplo de uso
if __name__ == "__main__":
    # Inicializar sistema
    sistema = FrequentCustomerSystem("julia_confecciones.db")

    # Crear cliente de ejemplo
    conn = sqlite3.connect("julia_confecciones.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO clientes (rut, nombre, email, celular)
        VALUES (?, ?, ?, ?)
    ''', ("98765432-1", "Ana Pérez", "ana@email.com", "912345678"))
    conn.commit()
    conn.close()

    # Registrar compras
    print("Registrando compras...")
    sistema.registrar_compra(1, 60000)  # $60,000
    sistema.registrar_compra(1, 45000)  # $45,000 (total: $105,000 - Frecuente)
    sistema.registrar_compra(1, 120000) # $120,000 (total: $225,000 - VIP)

    # Obtener beneficios del cliente
    beneficios = sistema.obtener_beneficios_cliente(1)
    print("Beneficios disponibles:", beneficios)

    # Obtener estadísticas
    stats = sistema.obtener_estadisticas_cliente(1)
    print("Estadísticas del cliente:", json.dumps(stats, indent=2, default=str))

    # Generar reporte
    reporte = sistema.generar_reporte_clientes_frecuentes()
    print("Reporte de clientes frecuentes:", reporte)

    # Identificar próximos a upgrade
    proximos = sistema.proximos_clientes_upgrade()
    print("Próximos a subir de nivel:", proximos)