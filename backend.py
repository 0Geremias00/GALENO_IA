from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
import psycopg2
import bcrypt
from datetime import timedelta

app = Flask(__name__)

# CORS completo
CORS(app, 
     origins="*",
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "DELETE", "OPTIONS"],
     supports_credentials=False)

app.config['JWT_SECRET_KEY'] = 'neoia_secret_key_2024_segura_32bytes!'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
jwt = JWTManager(app)
@app.before_request
def log_request():
    import sys
    print(f">>> {request.method} {request.path} | Auth: {request.headers.get('Authorization','NONE')[:30] if request.headers.get('Authorization') else 'NONE'}", file=sys.stderr, flush=True)

DB = {'host':'localhost','database':'neoia','user':'neoia_user','password':'neoia1234'}

def get_db():
    return psycopg2.connect(**DB)

# ─── AUTH ────────────────────────────────────────────────

@app.route('/auth/registro', methods=['POST', 'OPTIONS'])
def registro():
    if request.method == 'OPTIONS':
        return jsonify({'ok': True}), 200
    data = request.json
    nombre = data.get('nombre')
    email = data.get('email')
    password = data.get('password')
    if not all([nombre, email, password]):
        return jsonify({'error': 'Faltan campos'}), 400
    hash_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO usuarios (nombre, email, password_hash) VALUES (%s, %s, %s) RETURNING id", (nombre, email, hash_pw))
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        token = create_access_token(identity=str(user_id))
        return jsonify({'token': token, 'nombre': nombre, 'email': email})
    except psycopg2.errors.UniqueViolation:
        return jsonify({'error': 'El email ya está registrado'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return jsonify({'ok': True}), 200
    data = request.json
    email = data.get('email')
    password = data.get('password')
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, password_hash, rol FROM usuarios WHERE email=%s AND activo=TRUE", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if not user or not bcrypt.checkpw(password.encode(), user[2].encode()):
            return jsonify({'error': 'Credenciales incorrectas'}), 401
        token = create_access_token(identity=str(user[0]))
        return jsonify({'token': token, 'nombre': user[1], 'email': email, 'rol': user[3]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─── CONVERSACIONES ──────────────────────────────────────

@app.route('/conversaciones', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_conversaciones():
    if request.method == 'OPTIONS':
        return jsonify({'ok': True}), 200
    user_id = get_jwt_identity()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, titulo, actualizado_en FROM conversaciones WHERE usuario_id=%s ORDER BY actualizado_en DESC", (user_id,))
    convs = [{'id': r[0], 'titulo': r[1], 'actualizado_en': str(r[2])} for r in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(convs)

@app.route('/conversaciones', methods=['POST', 'OPTIONS'])
@jwt_required()
def crear_conversacion():
    if request.method == 'OPTIONS':
        return jsonify({'ok': True}), 200
    user_id = get_jwt_identity()
    titulo = request.json.get('titulo', 'Nueva conversacion')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO conversaciones (usuario_id, titulo) VALUES (%s, %s) RETURNING id", (user_id, titulo))
    conv_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'id': conv_id, 'titulo': titulo})

@app.route('/conversaciones/<int:conv_id>/mensajes', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_mensajes(conv_id):
    if request.method == 'OPTIONS':
        return jsonify({'ok': True}), 200
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT rol, contenido, creado_en FROM mensajes WHERE conversacion_id=%s ORDER BY creado_en", (conv_id,))
    msgs = [{'rol': r[0], 'contenido': r[1], 'creado_en': str(r[2])} for r in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(msgs)

@app.route('/conversaciones/<int:conv_id>/mensajes', methods=['POST', 'OPTIONS'])
@jwt_required()
def guardar_mensaje(conv_id):
    if request.method == 'OPTIONS':
        return jsonify({'ok': True}), 200
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO mensajes (conversacion_id, rol, contenido) VALUES (%s, %s, %s)", (conv_id, data['rol'], data['contenido']))
    cur.execute("UPDATE conversaciones SET actualizado_en=CURRENT_TIMESTAMP WHERE id=%s", (conv_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'ok': True})

@app.route('/conversaciones/<int:conv_id>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def eliminar_conversacion(conv_id):
    if request.method == 'OPTIONS':
        return jsonify({'ok': True}), 200
    user_id = get_jwt_identity()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM mensajes WHERE conversacion_id=%s", (conv_id,))
    cur.execute("DELETE FROM conversaciones WHERE id=%s AND usuario_id=%s", (conv_id, user_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'ok': True})

# ─── USUARIOS (admin) ─────────────────────────────────────

@app.route('/auth/usuarios', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_usuarios():
    if request.method == 'OPTIONS':
        return jsonify({'ok': True}), 200
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, email, rol, activo, creado_en FROM usuarios ORDER BY creado_en DESC")
    users = [{'id': r[0], 'nombre': r[1], 'email': r[2], 'rol': r[3], 'activo': r[4], 'creado_en': str(r[5])} for r in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(users)

@app.route('/auth/usuarios/<int:user_id>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def eliminar_usuario(user_id):
    if request.method == 'OPTIONS':
        return jsonify({'ok': True}), 200
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM usuarios WHERE id=%s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'ok': True})

@app.route('/auth/usuarios/<int:user_id>/toggle', methods=['POST', 'OPTIONS'])
@jwt_required()
def toggle_usuario(user_id):
    if request.method == 'OPTIONS':
        return jsonify({'ok': True}), 200
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET activo = NOT activo WHERE id=%s RETURNING activo", (user_id,))
    activo = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'activo': activo})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)
