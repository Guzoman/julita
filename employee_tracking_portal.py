# Portal de Seguimiento para Cortadores y Costureros - Julia Confecciones

from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import sqlite3
from datetime import datetime, timedelta
import json
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

class EmployeeTrackingPortal:
    def __init__(self, db_path):
        self.db_path = db_path

    def init_database(self):
        """Inicializar tablas necesarias para el portal"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabla de Sesiones de Empleados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sesiones_empleados (
                id_sesion INTEGER PRIMARY KEY AUTOINCREMENT,
                id_empleado INTEGER,
                token_sesion TEXT UNIQUE,
                fecha_inicio DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_ultimo_acceso DATETIME,
                estado TEXT DEFAULT 'activa',
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (id_empleado) REFERENCES empleados (id_empleado)
            )
        ''')

        # Tabla de Notificaciones de Producción
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notificaciones_produccion (
                id_notificacion INTEGER PRIMARY KEY AUTOINCREMENT,
                id_empleado INTEGER,
                id_produccion INTEGER,
                tipo_notificacion TEXT, -- 'nueva_tarea', 'recordatorio', 'actualizacion'
                mensaje TEXT,
                fecha_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_leida DATETIME,
                estado TEXT DEFAULT 'no_leida',
                FOREIGN KEY (id_empleado) REFERENCES empleados (id_empleado),
                FOREIGN KEY (id_produccion) REFERENCES produccion (id_produccion)
            )
        ''')

        # Tabla de Registro de Actividad
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS registro_actividad (
                id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
                id_empleado INTEGER,
                id_produccion INTEGER,
                tipo_actividad TEXT,
                descripcion TEXT,
                fecha_actividad DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                FOREIGN KEY (id_empleado) REFERENCES empleados (id_empleado),
                FOREIGN KEY (id_produccion) REFERENCES produccion (id_produccion)
            )
        ''')

        conn.commit()
        conn.close()

    def validar_acceso_empleado(self, codigo_acceso, password=None):
        """Validar acceso de empleado al portal"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id_empleado, nombre, tipo_empleado, estado
            FROM empleados
            WHERE codigo_acceso = ? AND estado = 'activo'
        ''', (codigo_acceso,))

        empleado = cursor.fetchone()
        conn.close()

        if empleado:
            return {
                "success": True,
                "id_empleado": empleado[0],
                "nombre": empleado[1],
                "tipo_empleado": empleado[2]
            }
        return {"success": False, "error": "Código de acceso inválido"}

    def crear_sesion(self, id_empleado, ip_address="", user_agent=""):
        """Crear nueva sesión para empleado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        token_sesion = secrets.token_urlsafe(32)

        try:
            cursor.execute('''
                INSERT INTO sesiones_empleados
                (id_empleado, token_sesion, ip_address, user_agent)
                VALUES (?, ?, ?, ?)
            ''', (id_empleado, token_sesion, ip_address, user_agent))

            conn.commit()
            conn.close()

            return {"success": True, "token_sesion": token_sesion}

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

    def validar_sesion(self, token_sesion):
        """Validar sesión activa"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT se.id_empleado, e.nombre, e.tipo_empleado
            FROM sesiones_empleados se
            JOIN empleados e ON se.id_empleado = e.id_empleado
            WHERE se.token_sesion = ? AND se.estado = 'activa'
        ''', (token_sesion,))

        sesion = cursor.fetchone()

        if sesion:
            # Actualizar último acceso
            cursor.execute('''
                UPDATE sesiones_empleados
                SET fecha_ultimo_acceso = datetime('now')
                WHERE token_sesion = ?
            ''', (token_sesion,))

            conn.commit()
            conn.close()

            return {
                "success": True,
                "id_empleado": sesion[0],
                "nombre": sesion[1],
                "tipo_empleado": sesion[2]
            }

        conn.close()
        return {"success": False, "error": "Sesión inválida o expirada"}

    def obtener_tareas_pendientes(self, id_empleado, tipo_empleado):
        """Obtener tareas pendientes para el empleado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if tipo_empleado == 'cortador':
            cursor.execute('''
                SELECT p.id_produccion, p.id_orden, p.tipo_orden,
                       p.fecha_asignacion, p.estado_corte,
                       p.pago_corte, p.estado_pago_corte,
                       p.notas, ep.estado_envio, ep.fecha_envio
                FROM produccion p
                LEFT JOIN envios_proveedores ep ON p.id_produccion = ep.id_produccion
                WHERE p.id_cortador = ?
                AND p.estado_corte IN ('pendiente', 'en_proceso')
                ORDER BY p.fecha_asignacion DESC
            ''', (id_empleado,))
        else:  # costurero
            cursor.execute('''
                SELECT p.id_produccion, p.id_orden, p.tipo_orden,
                       p.fecha_asignacion, p.estado_costura,
                       p.pago_costura, p.estado_pago_costura,
                       p.notas, ep.estado_envio, ep.fecha_envio
                FROM produccion p
                LEFT JOIN envios_proveedores ep ON p.id_produccion = ep.id_produccion
                WHERE p.id_costurero = ?
                AND p.estado_costura IN ('pendiente', 'en_proceso')
                ORDER BY p.fecha_asignacion DESC
            ''', (id_empleado,))

        tareas = cursor.fetchall()
        conn.close()

        return [
            {
                "id_produccion": t[0],
                "id_orden": t[1],
                "tipo_orden": t[2],
                "fecha_asignacion": t[3],
                "estado": t[4],
                "pago": t[5],
                "estado_pago": t[6],
                "notas": t[7],
                "estado_envio": t[8],
                "fecha_envio": t[9]
            } for t in tareas
        ]

    def obtener_tareas_completadas(self, id_empleado, tipo_empleado, limite=10):
        """Obtener tareas completadas recientemente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if tipo_empleado == 'cortador':
            cursor.execute('''
                SELECT p.id_produccion, p.id_orden, p.tipo_orden,
                       p.fecha_entrega_corte, p.pago_corte, p.estado_pago_corte
                FROM produccion p
                WHERE p.id_cortador = ? AND p.estado_corte = 'completado'
                ORDER BY p.fecha_entrega_corte DESC
                LIMIT ?
            ''', (id_empleado, limite))
        else:  # costurero
            cursor.execute('''
                SELECT p.id_produccion, p.id_orden, p.tipo_orden,
                       p.fecha_entrega_costura, p.pago_costura, p.estado_pago_costura
                FROM produccion p
                WHERE p.id_costurero = ? AND p.estado_costura = 'completado'
                ORDER BY p.fecha_entrega_costura DESC
                LIMIT ?
            ''', (id_empleado, limite))

        tareas = cursor.fetchall()
        conn.close()

        return [
            {
                "id_produccion": t[0],
                "id_orden": t[1],
                "tipo_orden": t[2],
                "fecha_entrega": t[3],
                "pago": t[4],
                "estado_pago": t[5]
            } for t in tareas
        ]

    def obtener_detalle_tarea(self, id_produccion, id_empleado, tipo_empleado):
        """Obtener detalles completos de una tarea"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Obtener información de la producción
        cursor.execute('''
            SELECT p.*,
                   GROUP_CONCAT(m.nombre || ':' || dpm.cantidad_utilizada || ' ' || m.unidad_medida, ', ') as materiales
            FROM produccion p
            LEFT JOIN detalle_produccion_materiales dpm ON p.id_produccion = dpm.id_produccion
            LEFT JOIN materiales m ON dpm.id_material = m.id_material
            WHERE p.id_produccion = ?
            GROUP BY p.id_produccion
        ''', (id_produccion,))

        produccion = cursor.fetchone()
        conn.close()

        if not produccion:
            return None

        return {
            "id_produccion": produccion[0],
            "id_orden": produccion[1],
            "tipo_orden": produccion[2],
            "fecha_asignacion": produccion[4],
            "fecha_entrega_corte": produccion[6],
            "fecha_entrega_costura": produccion[7],
            "estado_corte": produccion[8],
            "estado_costura": produccion[9],
            "pago_corte": produccion[10],
            "pago_costura": produccion[11],
            "estado_pago_corte": produccion[12],
            "estado_pago_costura": produccion[13],
            "notas": produccion[14],
            "materiales": produccion[15] or ""
        }

    def actualizar_estado_tarea(self, id_produccion, id_empleado, tipo_empleado,
                               nuevo_estado, notas=""):
        """Actualizar estado de una tarea"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if tipo_empleado == 'cortador':
                campo_estado = 'estado_corte'
                campo_fecha = 'fecha_entrega_corte'
            else:
                campo_estado = 'estado_costura'
                campo_fecha = 'fecha_entrega_costura'

            if nuevo_estado == 'completado':
                cursor.execute(f'''
                    UPDATE produccion
                    SET {campo_estado} = ?, {campo_fecha} = datetime('now')
                    WHERE id_produccion = ? AND id_{"cortador" if tipo_empleado == "cortador" else "costurero"} = ?
                ''', (nuevo_estado, id_produccion, id_empleado))
            else:
                cursor.execute(f'''
                    UPDATE produccion
                    SET {campo_estado} = ?
                    WHERE id_produccion = ? AND id_{"cortador" if tipo_empleado == "cortador" else "costurero"} = ?
                ''', (nuevo_estado, id_produccion, id_empleado))

            # Registrar actividad
            cursor.execute('''
                INSERT INTO registro_actividad
                (id_empleado, id_produccion, tipo_actividad, descripcion)
                VALUES (?, ?, 'cambio_estado', ?)
            ''', (id_empleado, id_produccion, f'Cambio estado a {nuevo_estado}: {notas}'))

            conn.commit()
            conn.close()

            return {"success": True, "mensaje": "Estado actualizado exitosamente"}

        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}

    def obtener_resumen_pagos(self, id_empleado, tipo_empleado):
        """Obtener resumen de pagos del empleado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total de prendas completadas
        if tipo_empleado == 'cortador':
            cursor.execute('''
                SELECT COUNT(*) as total_prendas,
                       SUM(pago_corte) as total_pendiente_pago,
                       SUM(CASE WHEN estado_pago_corte = 'pagado' THEN pago_corte ELSE 0 END) as total_pagado
                FROM produccion
                WHERE id_cortador = ? AND estado_corte = 'completado'
            ''', (id_empleado,))
        else:
            cursor.execute('''
                SELECT COUNT(*) as total_prendas,
                       SUM(pago_costura) as total_pendiente_pago,
                       SUM(CASE WHEN estado_pago_costura = 'pagado' THEN pago_costura ELSE 0 END) as total_pagado
                FROM produccion
                WHERE id_costurero = ? AND estado_costura = 'completado'
            ''', (id_empleado,))

        pagos = cursor.fetchone()
        conn.close()

        if pagos:
            return {
                "total_prendas": pagos[0] or 0,
                "total_pendiente_pago": pagos[1] or 0,
                "total_pagado": pagos[2] or 0,
                "saldo_pendiente": (pagos[1] or 0) - (pagos[2] or 0)
            }
        return {"total_prendas": 0, "total_pendiente_pago": 0, "total_pagado": 0, "saldo_pendiente": 0}

    def obtener_notificaciones(self, id_empleado, no_leidas=True):
        """Obtener notificaciones para el empleado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if no_leidas:
            cursor.execute('''
                SELECT id_notificacion, id_produccion, tipo_notificacion,
                       mensaje, fecha_envio
                FROM notificaciones_produccion
                WHERE id_empleado = ? AND estado = 'no_leida'
                ORDER BY fecha_envio DESC
            ''', (id_empleado,))
        else:
            cursor.execute('''
                SELECT id_notificacion, id_produccion, tipo_notificacion,
                       mensaje, fecha_envio, estado
                FROM notificaciones_produccion
                WHERE id_empleado = ?
                ORDER BY fecha_envio DESC
                LIMIT 20
            ''', (id_empleado,))

        notificaciones = cursor.fetchall()
        conn.close()

        return [
            {
                "id_notificacion": n[0],
                "id_produccion": n[1],
                "tipo": n[2],
                "mensaje": n[3],
                "fecha_envio": n[4],
                "estado": n[5] if len(n) > 5 else 'no_leida'
            } for n in notificaciones
        ]

    def marcar_notificacion_leida(self, id_notificacion, id_empleado):
        """Marcar notificación como leída"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE notificaciones_produccion
            SET estado = 'leida', fecha_leida = datetime('now')
            WHERE id_notificacion = ? AND id_empleado = ?
        ''', (id_notificacion, id_empleado))

        conn.commit()
        conn.close()

    def enviar_notificacion(self, id_empleado, id_produccion, tipo_notificacion, mensaje):
        """Enviar notificación a empleado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO notificaciones_produccion
            (id_empleado, id_produccion, tipo_notificacion, mensaje)
            VALUES (?, ?, ?, ?)
        ''', (id_empleado, id_produccion, tipo_notificacion, mensaje))

        conn.commit()
        conn.close()

# Instancia del portal
portal = EmployeeTrackingPortal("julia_confecciones.db")

# Template HTML para el portal
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portal de Seguimiento - Julia Confecciones</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .login-form { max-width: 300px; margin: 0 auto; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #0056b3; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #1e7e34; }
        .btn-warning { background: #ffc107; color: #212529; }
        .btn-warning:hover { background: #e0a800; }
        .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { border: 1px solid #ddd; border-radius: 8px; padding: 15px; }
        .card h3 { margin-top: 0; color: #333; }
        .tarea { border-bottom: 1px solid #eee; padding: 10px 0; }
        .tarea:last-child { border-bottom: none; }
        .estado { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .estado-pendiente { background: #fff3cd; color: #856404; }
        .estado-proceso { background: #d1ecf1; color: #0c5460; }
        .estado-completado { background: #d4edda; color: #155724; }
        .notificacion { background: #f8f9fa; border-left: 4px solid #007bff; padding: 10px; margin-bottom: 10px; }
        .resumen { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
        .resumen-item { background: #007bff; color: white; padding: 15px; border-radius: 8px; text-align: center; }
        .resumen-item h4 { margin: 0 0 10px 0; }
        .resumen-item .valor { font-size: 24px; font-weight: bold; }
        .logout { float: right; }
        .hidden { display: none; }
        @media (max-width: 768px) { .dashboard { grid-template-columns: 1fr; } .resumen { grid-template-columns: repeat(2, 1fr); } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Portal de Seguimiento</h1>
            <p>Julia Confecciones - Sistema de Producción</p>
        </div>

        <!-- Login Form -->
        <div id="login-section">
            <div class="login-form">
                <h2>Iniciar Sesión</h2>
                <form id="login-form">
                    <div class="form-group">
                        <label for="codigo_acceso">Código de Acceso:</label>
                        <input type="text" id="codigo_acceso" required>
                    </div>
                    <button type="submit" class="btn">Ingresar</button>
                </form>
            </div>
        </div>

        <!-- Dashboard -->
        <div id="dashboard-section" class="hidden">
            <div class="logout">
                <button class="btn" onclick="logout()">Cerrar Sesión</button>
            </div>
            <h2 id="welcome-message"></h2>

            <!-- Resumen -->
            <div class="resumen">
                <div class="resumen-item">
                    <h4>Total Prendas</h4>
                    <div class="valor" id="total-prendas">0</div>
                </div>
                <div class="resumen-item">
                    <h4>Pendientes</h4>
                    <div class="valor" id="tareas-pendientes">0</div>
                </div>
                <div class="resumen-item">
                    <h4>Pagado</h4>
                    <div class="valor" id="total-pagado">$0</div>
                </div>
                <div class="resumen-item">
                    <h4>Por Pagar</h4>
                    <div class="valor" id="saldo-pendiente">$0</div>
                </div>
            </div>

            <!-- Notificaciones -->
            <div class="card">
                <h3>Notificaciones</h3>
                <div id="notificaciones-container">
                    <p>No hay notificaciones nuevas</p>
                </div>
            </div>

            <!-- Dashboard -->
            <div class="dashboard">
                <div class="card">
                    <h3>Tareas Pendientes</h3>
                    <div id="tareas-pendientes-container">
                        <p>No hay tareas pendientes</p>
                    </div>
                </div>

                <div class="card">
                    <h3>Tareas Completadas</h3>
                    <div id="tareas-completadas-container">
                        <p>No hay tareas completadas recientemente</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentSession = null;

        // Login functionality
        document.getElementById('login-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            const codigo = document.getElementById('codigo_acceso').value;

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({codigo_acceso: codigo})
                });

                const data = await response.json();

                if (data.success) {
                    currentSession = data.token_sesion;
                    showDashboard(data);
                } else {
                    alert('Código de acceso inválido');
                }
            } catch (error) {
                alert('Error al iniciar sesión');
            }
        });

        function showDashboard(userData) {
            document.getElementById('login-section').classList.add('hidden');
            document.getElementById('dashboard-section').classList.remove('hidden');
            document.getElementById('welcome-message').textContent = `Bienvenido, ${userData.nombre}`;

            loadDashboardData();
        }

        async function loadDashboardData() {
            try {
                const response = await fetch('/api/dashboard', {
                    headers: {'Authorization': 'Bearer ' + currentSession}
                });

                const data = await response.json();

                if (data.success) {
                    updateResumen(data.resumen);
                    updateTareasPendientes(data.tareas_pendientes);
                    updateTareasCompletadas(data.tareas_completadas);
                    updateNotificaciones(data.notificaciones);
                }
            } catch (error) {
                console.error('Error cargando dashboard:', error);
            }
        }

        function updateResumen(resumen) {
            document.getElementById('total-prendas').textContent = resumen.total_prendas;
            document.getElementById('total-pagado').textContent = '$' + resumen.total_pagado;
            document.getElementById('saldo-pendiente').textContent = '$' + resumen.saldo_pendiente;
            document.getElementById('tareas-pendientes').textContent = resumen.tareas_pendientes_count;
        }

        function updateTareasPendientes(tareas) {
            const container = document.getElementById('tareas-pendientes-container');

            if (tareas.length === 0) {
                container.innerHTML = '<p>No hay tareas pendientes</p>';
                return;
            }

            container.innerHTML = tareas.map(tarea => `
                <div class="tarea">
                    <div><strong>Orden #${tarea.id_orden}</strong> (${tarea.tipo_orden})</div>
                    <div>Estado: <span class="estado estado-${tarea.estado === 'pendiente' ? 'pendiente' : 'proceso'}">${tarea.estado}</span></div>
                    <div>Pago: $${tarea.pago}</div>
                    <div>Asignado: ${new Date(tarea.fecha_asignacion).toLocaleDateString()}</div>
                    ${tarea.estado === 'pendiente' ? `<button class="btn btn-success" onclick="iniciarTarea(${tarea.id_produccion})">Iniciar</button>` : ''}
                    ${tarea.estado === 'en_proceso' ? `<button class="btn btn-warning" onclick="completarTarea(${tarea.id_produccion})">Completar</button>` : ''}
                </div>
            `).join('');
        }

        function updateTareasCompletadas(tareas) {
            const container = document.getElementById('tareas-completadas-container');

            if (tareas.length === 0) {
                container.innerHTML = '<p>No hay tareas completadas recientemente</p>';
                return;
            }

            container.innerHTML = tareas.map(tarea => `
                <div class="tarea">
                    <div><strong>Orden #${tarea.id_orden}</strong> (${tarea.tipo_orden})</div>
                    <div>Completado: ${new Date(tarea.fecha_entrega).toLocaleDateString()}</div>
                    <div>Pago: $${tarea.pago} <span class="estado estado-${tarea.estado_pago === 'pagado' ? 'completado' : 'pendiente'}">${tarea.estado_pago}</span></div>
                </div>
            `).join('');
        }

        function updateNotificaciones(notificaciones) {
            const container = document.getElementById('notificaciones-container');

            if (notificaciones.length === 0) {
                container.innerHTML = '<p>No hay notificaciones nuevas</p>';
                return;
            }

            container.innerHTML = notificaciones.map(notif => `
                <div class="notificacion">
                    <div><strong>${notif.tipo}:</strong> ${notif.mensaje}</div>
                    <small>${new Date(notif.fecha_envio).toLocaleString()}</small>
                </div>
            `).join('');
        }

        async function iniciarTarea(idProduccion) {
            await actualizarEstadoTarea(idProduccion, 'en_proceso');
        }

        async function completarTarea(idProduccion) {
            await actualizarEstadoTarea(idProduccion, 'completado');
        }

        async function actualizarEstadoTarea(idProduccion, nuevoEstado) {
            try {
                const response = await fetch('/api/tarea/actualizar', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + currentSession
                    },
                    body: JSON.stringify({
                        id_produccion: idProduccion,
                        nuevo_estado: nuevoEstado
                    })
                });

                const data = await response.json();

                if (data.success) {
                    loadDashboardData();
                } else {
                    alert('Error al actualizar tarea: ' + data.error);
                }
            } catch (error) {
                alert('Error al actualizar tarea');
            }
        }

        function logout() {
            currentSession = null;
            document.getElementById('login-section').classList.remove('hidden');
            document.getElementById('dashboard-section').classList.add('hidden');
            document.getElementById('codigo_acceso').value = '';
        }
    </script>
</body>
</html>
"""

# Routes
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    codigo_acceso = data.get('codigo_acceso')

    result = portal.validar_acceso_empleado(codigo_acceso)

    if result['success']:
        session_result = portal.crear_sesion(
            result['id_empleado'],
            request.remote_addr,
            request.headers.get('User-Agent', '')
        )

        if session_result['success']:
            return jsonify({
                'success': True,
                'token_sesion': session_result['token_sesion'],
                'nombre': result['nombre'],
                'tipo_empleado': result['tipo_empleado']
            })

    return jsonify({'success': False, 'error': 'Código de acceso inválido'})

@app.route('/api/dashboard')
def dashboard():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    sesion = portal.validar_sesion(token)

    if not sesion['success']:
        return jsonify({'success': False, 'error': 'Sesión inválida'}), 401

    id_empleado = sesion['id_empleado']
    tipo_empleado = sesion['tipo_empleado']

    # Obtener datos del dashboard
    tareas_pendientes = portal.obtener_tareas_pendientes(id_empleado, tipo_empleado)
    tareas_completadas = portal.obtener_tareas_completadas(id_empleado, tipo_empleado)
    resumen = portal.obtener_resumen_pagos(id_empleado, tipo_empleado)
    notificaciones = portal.obtener_notificaciones(id_empleado, no_leidas=True)

    return jsonify({
        'success': True,
        'tareas_pendientes': tareas_pendientes,
        'tareas_completadas': tareas_completadas,
        'resumen': resumen,
        'notificaciones': notificaciones,
        'tareas_pendientes_count': len(tareas_pendientes)
    })

@app.route('/api/tarea/actualizar', methods=['POST'])
def actualizar_tarea():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    sesion = portal.validar_sesion(token)

    if not sesion['success']:
        return jsonify({'success': False, 'error': 'Sesión inválida'}), 401

    data = request.get_json()
    id_produccion = data.get('id_produccion')
    nuevo_estado = data.get('nuevo_estado')

    result = portal.actualizar_estado_tarea(
        id_produccion,
        sesion['id_empleado'],
        sesion['tipo_empleado'],
        nuevo_estado
    )

    return jsonify(result)

@app.route('/api/notificaciones/<int:id_notificacion>/leida', methods=['POST'])
def marcar_notificacion_leida(id_notificacion):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    sesion = portal.validar_sesion(token)

    if not sesion['success']:
        return jsonify({'success': False, 'error': 'Sesión inválida'}), 401

    portal.marcar_notificacion_leida(id_notificacion, sesion['id_empleado'])
    return jsonify({'success': True})

if __name__ == '__main__':
    portal.init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)