# En bot_control_ansv/app.py

import sqlite3
from flask import Flask, request, jsonify, render_template
import os
import logging
import datetime # Para manejar las fechas de forma más robusta

app = Flask(__name__)

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Silenciar logs de acceso de Werkzeug (peticiones HTTP) ---
# Esto ayuda a reducir el ruido de peticiones que no son relevantes para el debug de tu app
log = logging.getLogger('werkzeug')
# Puedes poner logging.ERROR, logging.WARNING o logging.CRITICAL según cuánto quieras silenciar
log.setLevel(logging.ERROR) 


# --- Configuración de la base de datos ---
# Ruta ajustada para la estructura:
# /tu_repositorio_git/
# ├── bot-ansv/
# │   └── data/
# │       └── soporte_db.db
# └── bot_control_ansv/
#     └── app.py

# Construye la ruta absoluta a la base de datos.
# os.path.abspath(__file__) -> /ruta/a/tu_repositorio_git/bot_control_ansv/app.py
# os.path.dirname(...)      -> /ruta/a/tu_repositorio_git/bot_control_ansv/
# os.path.join(..., "..")   -> /ruta/a/tu_repositorio_git/
# os.path.join(..., "bot-ansv", "data", "soporte_db.db") -> /ruta/a/tu_repositorio_git/bot-ansv/data/soporte_db.db
# DATABASE = os.path.abspath(os.path.join(
#     os.path.dirname(os.path.abspath(__file__)), "..", "bot-ansv", "data", "soporte_db.db"
# ))

DATABASE_RELATIVE_PATH = os.path.join(".", "data", "soporte_db.db")
DATABASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), DATABASE_RELATIVE_PATH))

# Mensaje de depuración para confirmar la ruta de la DB
logging.info(f"La base de datos se buscará en: {DATABASE}")


def get_db_connection():
    """Establece una conexión a la base de datos SQLite."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row  # Permite acceder a las columnas como diccionarios
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error al conectar con la base de datos: {e}")
        return None


# --- FUNCIÓN PARA ALTERAR LA TABLA (EJECUTAR UNA SOLA VEZ DE FORMA SEGURA) ---
def alter_parametros_seteos_table():
    conn = get_db_connection()
    if conn is None:
        logging.error("No se pudo conectar a la DB para alterar la tabla.")
        return

    cursor = conn.cursor()

    # Obtener información de las columnas existentes
    cursor.execute("PRAGMA table_info(parametros_seteos)")
    columns = [col[1] for col in cursor.fetchall()]

    changes_made = False

    if 'tipo_dato' not in columns:
        try:
            cursor.execute("ALTER TABLE parametros_seteos ADD COLUMN tipo_dato TEXT")
            logging.info("Columna 'tipo_dato' agregada a 'parametros_seteos'.")
            changes_made = True
        except sqlite3.Error as e:
            logging.error(f"Error al agregar columna 'tipo_dato': {e}")

    if 'descripcion' not in columns:
        try:
            cursor.execute("ALTER TABLE parametros_seteos ADD COLUMN descripcion TEXT")
            logging.info("Columna 'descripcion' agregada a 'parametros_seteos'.")
            changes_made = True
        except sqlite3.Error as e:
            logging.error(f"Error al agregar columna 'descripcion': {e}")

    if 'ultima_modificacion' not in columns:
        try:
            cursor.execute("ALTER TABLE parametros_seteos ADD COLUMN ultima_modificacion DATETIME")
            logging.info("Columna 'ultima_modificacion' agregada a 'parametros_seteos'.")
            # Actualizar las filas existentes con la fecha y hora actual
            cursor.execute("UPDATE parametros_seteos SET ultima_modificacion = ? WHERE ultima_modificacion IS NULL",
                           (datetime.datetime.now().isoformat(),))
            logging.info("Columna 'ultima_modificacion' actualizada para filas existentes.")
            changes_made = True
        except sqlite3.Error as e:
            logging.error(f"Error al agregar columna 'ultima_modificacion': {e}")

    if changes_made:
        conn.commit()
    conn.close()
    logging.info("Proceso de alteración de 'parametros_seteos' completado.")


# --- Rutas de la API CRUD para parametros_seteos ---

@app.route('/api/parametros_seteos', methods=['GET'])
def get_parametros():
    conn = get_db_connection()
    cursor = conn.cursor()
    # ¡CORRECCIÓN AQUÍ! Selecciona 'valor_parametro'
    cursor.execute("SELECT id, nombre_parametro, valor_parametro, tipo_dato, descripcion, ultima_modificacion FROM parametros_seteos")
    parametros = cursor.fetchall()
    conn.close()

    parametros_list = []
    for p in parametros:
        parametros_list.append({
            'id': p[0],
            'nombre_parametro': p[1],
            'valor_parametro': p[2], # p[2] ahora será el valor correcto de valor_parametro
            'tipo_dato': p[3],
            'descripcion': p[4],
            'ultima_modificacion': p[5]
        })
    return jsonify(parametros_list)

@app.route('/api/parametros_seteos/<int:param_id>', methods=['GET'])
def get_parametro_seteos(param_id):
    """Obtiene un parámetro específico por su ID."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
    try:
        parametro = conn.execute('SELECT * FROM parametros_seteos WHERE id = ?', (param_id,)).fetchone()
        if parametro is None:
            return jsonify({'error': 'Parámetro no encontrado'}), 404
        return jsonify(dict(parametro))
    except sqlite3.Error as e:
        logging.error(f"Error al obtener parámetro con ID {param_id}: {e}")
        return jsonify({'error': 'Error interno del servidor al obtener el parámetro'}), 500
    finally:
        conn.close()

@app.route('/api/parametros_seteos', methods=['POST'])
def create_parametro_seteos():
    """Crea un nuevo parámetro."""
    new_param = request.json
    if not new_param or not all(key in new_param for key in ['nombre_parametro', 'valor_parametro']):
        return jsonify({'error': 'Faltan campos obligatorios: nombre_parametro, valor_parametro'}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
    try:
        cursor = conn.cursor()
        
        # Insertar con las nuevas columnas
        cursor.execute(
            'INSERT INTO parametros_seteos (nombre_parametro, valor_parametro, tipo_dato, descripcion, ultima_modificacion) VALUES (?, ?, ?, ?, ?)',
            (new_param['nombre_parametro'], 
             new_param['valor_parametro'],
             new_param.get('tipo_dato', None),  # Usar .get() para valores opcionales
             new_param.get('descripcion', None),
             datetime.datetime.now().isoformat()) # Usar ISO format para almacenar
        )
        conn.commit()
        
        new_param_id = cursor.lastrowid
        parametro_creado = conn.execute('SELECT * FROM parametros_seteos WHERE id = ?', (new_param_id,)).fetchone()
        return jsonify(dict(parametro_creado)), 201
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({'error': 'El nombre del parámetro ya existe.'}), 409
    except Exception as e:
        conn.rollback()
        logging.error(f"Error al crear parámetro: {e}")
        return jsonify({'error': f'Error interno del servidor al crear parámetro: {e}'}), 500
    finally:
        conn.close()

@app.route('/api/parametros_seteos/<int:param_id>', methods=['PUT'])
def update_parametro_seteos(param_id):
    """Actualiza un parámetro existente."""
    updated_data = request.json
    if not updated_data:
        return jsonify({'error': 'No se proporcionaron datos para actualizar'}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
    try:
        cursor = conn.cursor()
        
        set_clauses = []
        values = []
        
        # Validar y construir las cláusulas SET dinámicamente
        for key, value in updated_data.items():
            if key in ['nombre_parametro', 'valor_parametro', 'tipo_dato', 'descripcion']:
                set_clauses.append(f"{key} = ?")
                values.append(value)
        
        if not set_clauses:
            return jsonify({'error': 'No hay campos válidos para actualizar'}), 400

        # Siempre actualizar la fecha de última_modificacion
        set_clauses.append("ultima_modificacion = ?")
        values.append(datetime.datetime.now().isoformat())

        query = f"UPDATE parametros_seteos SET {', '.join(set_clauses)} WHERE id = ?"
        values.append(param_id) # El ID va al final para el WHERE clause

        cursor.execute(query, tuple(values))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': 'Parámetro no encontrado o no se realizaron cambios'}), 404
        
        parametro_actualizado = conn.execute('SELECT * FROM parametros_seteos WHERE id = ?', (param_id,)).fetchone()
        return jsonify(dict(parametro_actualizado))
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({'error': 'El nombre del parámetro ya existe.'}), 409
    except Exception as e:
        conn.rollback()
        logging.error(f"Error al actualizar parámetro con ID {param_id}: {e}")
        return jsonify({'error': f'Error interno del servidor al actualizar parámetro: {e}'}), 500
    finally:
        conn.close()

@app.route('/api/parametros_seteos/<int:param_id>', methods=['DELETE'])
def delete_parametro_seteos(param_id):
    """Elimina un parámetro por su ID."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM parametros_seteos WHERE id = ?', (param_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Parámetro no encontrado'}), 404
        return jsonify({'message': 'Parámetro eliminado exitosamente'}), 200
    except Exception as e:
        conn.rollback()
        logging.error(f"Error al eliminar parámetro con ID {param_id}: {e}")
        return jsonify({'error': f'Error interno del servidor al eliminar parámetro: {e}'}), 500
    finally:
        conn.close()

# --- Ruta para la interfaz HTML ---

@app.route('/admin/parametros_seteos')
def admin_parametros_seteos_page():
    """Ruta para servir la página HTML de administración de parámetros."""
    return render_template('parametros_seteos.html')

if __name__ == '__main__':
    # --- Inicialización Segura de la DB y Alteración de Tabla ---
    
    # 1. Asegurarse de que el directorio 'data' exista para la DB
    data_dir = os.path.dirname(DATABASE)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        logging.info(f"Directorio 'data' creado en: {data_dir}")

    # 2. Conexión y creación de la tabla si no existe
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parametros_seteos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_parametro TEXT UNIQUE NOT NULL,
                valor_parametro TEXT NOT NULL,
                -- Las siguientes columnas se añadirán por alter_parametros_seteos_table()
                -- tipo_dato TEXT,
                -- descripcion TEXT,
                -- ultima_modificacion DATETIME
                valor TEXT -- Compatible con la estructura inicial de db_services.py si es necesario
            )
        ''')
        conn.commit()
        conn.close()
        logging.info("Tabla 'parametros_seteos' verificada/creada.")
    else:
        logging.critical("No se pudo establecer conexión inicial con la DB para verificar/crear la tabla.")
        # Podrías considerar salir o manejar el error de forma más robusta aquí

    # 3. Llamar a la función de alteración de tabla para añadir las nuevas columnas
    # Esta función verificará si las columnas ya existen antes de agregarlas.
    alter_parametros_seteos_table()
    
    # 4. Iniciar la aplicación Flask
    app.run(debug=True, port=5001) # Ejecutar en un puerto diferente al bot principal (5000)