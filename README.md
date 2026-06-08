# 🏥 Galeno IA — Asistente Médico Inteligente

<div align="center">

![Galeno IA](https://img.shields.io/badge/Galeno-IA-3d8ef8?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyek0xMSAxN3YtNkg5bDMtNCAzIDRoLTJ2NmgtMnoiLz48L3N2Zz4=)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=for-the-badge&logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-22c55e?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-a78bfa?style=for-the-badge)

**Asistente médico con IA local, RAG y historial privado por usuario.**  
Sin internet. Sin nube. 100% tuyo.

[🚀 Instalación](#-instalación) • [⚙️ Configuración](#️-configuración) • [📖 Uso](#-uso) • [🏗️ Arquitectura](#️-arquitectura)

</div>

---

## 📋 Tabla de Contenidos

- [¿Qué es Galeno IA?](#-qué-es-galeno-ia)
- [Características](#-características)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Configuración](#️-configuración)
- [Uso](#-uso)
- [Arquitectura](#️-arquitectura)
- [API Endpoints](#-api-endpoints)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Agregar Documentos Médicos](#-agregar-documentos-médicos)
- [Contribuir](#-contribuir)

---

## 🧠 ¿Qué es Galeno IA?

Galeno IA es un asistente médico inteligente que corre **completamente en local** usando modelos de lenguaje a través de Ollama. Permite consultar información médica en español e inglés, con historial privado por usuario y soporte para documentos clínicos mediante RAG (Retrieval Augmented Generation).

> ⚕️ *Galeno IA es solo un asistente orientativo. Siempre consulta con un médico de tu preferencia.*

---

## ✨ Características

- 🤖 **IA Local** — Usa Ollama con `qwen2.5:1.5b`, sin enviar datos a la nube
- 📚 **RAG Médico** — ChromaDB con guías clínicas oficiales (3,299+ chunks)
- 🔐 **Autenticación JWT** — Login seguro con tokens y contraseñas hasheadas
- 💬 **Historial** — Conversaciones guardadas por usuario en PostgreSQL
- 🌐 **Bilingüe** — Responde en español e inglés
- 📄 **Subida de PDFs** — Carga documentos médicos desde la interfaz
- 👥 **Roles** — Sistema de administrador y usuario
- 🌙 **Tema oscuro/claro** — Interfaz moderna y responsive

---

## 📦 Requisitos

### Hardware recomendado
| Componente | Mínimo | Recomendado |
|-----------|--------|-------------|
| RAM | 8 GB | 16 GB |
| Almacenamiento | 20 GB | 50 GB+ |
| CPU | 4 núcleos | 8 núcleos |

> Probado en **Orange Pi 5 Ultra** con Ubuntu 22.04 Jammy.  
> Compatible con cualquier Linux con Python 3.10+.

### Software
- Ubuntu 22.04+ (o cualquier Debian/Ubuntu)
- Python 3.10+
- PostgreSQL 14+
- Nginx
- Ollama
- Node.js (opcional, para desarrollo)

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/0Geremias00/GALENO_IA.git
cd GALENO_IA
```

### 2. Instalar dependencias del sistema

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv postgresql nginx curl
```

### 3. Instalar Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Descargar el modelo de lenguaje:

```bash
ollama pull qwen2.5:1.5b
```

Verificar que Ollama esté corriendo:

```bash
systemctl status ollama
ollama list
```

### 4. Instalar dependencias Python

```bash
pip3 install flask flask-jwt-extended flask-cors psycopg2-binary bcrypt \
             chromadb sentence-transformers pymupdf gunicorn
```

### 5. Configurar PostgreSQL

```bash
sudo -u postgres psql
```

Dentro de psql:

```sql
CREATE DATABASE neoia;
CREATE USER neoia_user WITH PASSWORD 'neoia1234';
GRANT ALL PRIVILEGES ON DATABASE neoia TO neoia_user;
\c neoia
GRANT ALL ON SCHEMA public TO neoia_user;
\q
```

Crear las tablas:

```bash
sudo -u postgres psql -d neoia
```

```sql
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol VARCHAR(20) DEFAULT 'usuario',
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE conversaciones (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    titulo VARCHAR(200) DEFAULT 'Nueva conversación',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE mensajes (
    id SERIAL PRIMARY KEY,
    conversacion_id INTEGER REFERENCES conversaciones(id) ON DELETE CASCADE,
    rol VARCHAR(20) NOT NULL,
    contenido TEXT NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
\q
```

### 6. Crear usuario administrador

```bash
python3 -c "
import psycopg2, bcrypt
conn = psycopg2.connect(host='localhost', database='neoia', user='neoia_user', password='neoia1234')
cur = conn.cursor()
hash_pw = bcrypt.hashpw('123456'.encode(), bcrypt.gensalt()).decode()
cur.execute(\"INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (%s, %s, %s, %s)\",
            ('Admin', 'admin@gmail.com', hash_pw, 'admin'))
conn.commit()
cur.close()
conn.close()
print('✅ Usuario admin creado')
"
```

### 7. Configurar Nginx

```bash
sudo nano /etc/nginx/sites-enabled/default
```

Reemplaza el contenido con:

```nginx
server {
    listen 80;
    server_name _;

    location / {
        root /var/www/html;
        try_files /index.html =404;
    }

    location /login {
        root /var/www/html;
        try_files /login.html =404;
    }

    location /api/ {
        proxy_pass http://localhost:11434/;
        proxy_set_header Host $host;
        proxy_pass_header Authorization;
    }

    location /rag/ {
        proxy_pass http://localhost:5000/;
        proxy_set_header Host $host;
        proxy_pass_header Authorization;
    }

    location ~ ^/(auth|conversaciones|admin) {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_pass_header Authorization;
    }
}
```

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 8. Copiar archivos del frontend

```bash
sudo cp index.html /var/www/html/index.html
sudo cp login.html /var/www/html/login.html
sudo chmod 644 /var/www/html/*.html
```

### 9. Cargar documentos médicos al RAG

Coloca tus PDFs médicos en el directorio del proyecto y ejecuta:

```bash
python3 cargar_pdfs.py
```

---

## ⚙️ Configuración

### Servicios systemd

Crear servicio para el backend:

```bash
sudo nano /etc/systemd/system/backend.service
```

```ini
[Unit]
Description=Galeno IA Backend
After=network.target postgresql.service

[Service]
User=orangepi
WorkingDirectory=/home/orangepi
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:8001 backend:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Crear servicio para el RAG:

```bash
sudo nano /etc/systemd/system/rag.service
```

```ini
[Unit]
Description=Galeno IA RAG Server
After=network.target

[Service]
User=orangepi
WorkingDirectory=/home/orangepi
ExecStart=/usr/bin/python3 rag.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Activar y arrancar los servicios:

```bash
sudo systemctl daemon-reload
sudo systemctl enable backend.service rag.service
sudo systemctl start backend.service rag.service
```

### Variables de entorno (opcional)

Para mayor seguridad, puedes crear un archivo `.env`:

```bash
nano .env
```

```env
DB_HOST=localhost
DB_NAME=neoia
DB_USER=neoia_user
DB_PASSWORD=neoia1234
JWT_SECRET=tu_clave_secreta_muy_segura
```

> ⚠️ **Nunca subas el archivo `.env` a Git.** Ya está incluido en `.gitignore`.

---

## 📖 Uso

### Acceder a la interfaz

Abre el navegador y ve a:

```
http://IP_DE_TU_SERVIDOR
```

Por ejemplo: `http://192.168.0.156`

### Credenciales por defecto

| Campo | Valor |
|-------|-------|
| Email | `admin@gmail.com` |
| Contraseña | `123456` |

> ⚠️ Cambia la contraseña después del primer inicio de sesión.

### Comandos útiles

```bash
# Ver estado de los servicios
systemctl status backend.service rag.service ollama.service nginx.service

# Ver logs en tiempo real
journalctl -u backend.service -f
journalctl -u rag.service -f

# Reiniciar servicios
sudo systemctl restart backend.service rag.service

# Ver modelos Ollama instalados
ollama list

# Ver chunks en ChromaDB
python3 -c "
import chromadb
c = chromadb.PersistentClient(path='/home/orangepi/vectordb')
col = c.get_collection('documentos_medicos')
print(f'Total chunks: {col.count()}')
"
```

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────┐
│           Navegador del Usuario          │
└──────────────────┬──────────────────────┘
                   │ HTTP :80
┌──────────────────▼──────────────────────┐
│               Nginx (Proxy)              │
│  /        → index.html                  │
│  /login   → login.html                  │
│  /api/    → Ollama :11434               │
│  /rag/    → RAG Server :5000            │
│  /auth/   → Backend :8001               │
└──────┬───────────┬───────────┬──────────┘
       │           │           │
┌──────▼──┐  ┌─────▼───┐  ┌───▼──────────┐
│ Ollama  │  │   RAG   │  │   Backend    │
│:11434   │  │ :5000   │  │   :8001      │
│qwen2.5  │  │ChromaDB │  │Flask+Gunicorn│
└─────────┘  └─────────┘  └──────┬───────┘
                                  │
                         ┌────────▼───────┐
                         │  PostgreSQL    │
                         │  :5432         │
                         └────────────────┘
```

---

## 🔌 API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| `POST` | `/auth/login` | Iniciar sesión | ❌ |
| `POST` | `/auth/registro` | Registrar usuario | ❌ |
| `GET` | `/conversaciones` | Listar conversaciones | ✅ |
| `POST` | `/conversaciones` | Crear conversación | ✅ |
| `GET` | `/conversaciones/<id>/mensajes` | Ver mensajes | ✅ |
| `POST` | `/conversaciones/<id>/mensajes` | Guardar mensaje | ✅ |
| `DELETE` | `/conversaciones/<id>` | Eliminar conversación | ✅ |
| `POST` | `/rag/preguntar` | Consultar RAG | ❌ |
| `POST` | `/rag/subir` | Subir PDF al RAG | ❌ |
| `GET` | `/auth/usuarios` | Listar usuarios (admin) | ✅ |
| `POST` | `/auth/usuarios/<id>/toggle` | Activar/desactivar usuario | ✅ |
| `DELETE` | `/auth/usuarios/<id>` | Eliminar usuario | ✅ |

---

## 📁 Estructura del Proyecto

```
GALENO_IA/
├── backend.py          # API Flask principal (auth, conversaciones)
├── rag.py              # Servidor RAG con ChromaDB
├── cargar_pdfs.py      # Script para indexar PDFs al RAG
├── index.html          # Frontend — Chat principal
├── login.html          # Frontend — Landing y login
├── .gitignore          # Archivos ignorados por Git
└── README.md           # Este archivo
```

---

## 📄 Agregar Documentos Médicos

1. Coloca los PDFs en el directorio del proyecto
2. Ejecuta el script de carga:

```bash
python3 cargar_pdfs.py
```

3. Reinicia el servicio RAG:

```bash
sudo systemctl restart rag.service
```

### Documentos incluidos por defecto

| Documento | Chunks |
|-----------|--------|
| Diabetes Mellitus Tipo 2 — MSP Ecuador | 428 |
| Cuadro Nacional de Medicamentos Básicos | 486 |
| Guía Clínica Influenza | 116 |
| Alerta Epidemiológica Influenza 2025 | 87 |
| Guía VIH/SIDA | 787 |
| Hipertensión Arterial | 319 |
| Infecciones Respiratorias (IRAS) | 307 |
| Enfermedades del Hígado | 298 |
| **Total** | **3,299** |

---

## 🤝 Contribuir

1. Haz fork del repositorio
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`
3. Haz tus cambios y commit: `git commit -m "Agrega nueva funcionalidad"`
4. Push a tu rama: `git push origin feature/nueva-funcionalidad`
5. Abre un Pull Request

---

## ⚠️ Disclaimer

> Galeno IA es un asistente informativo. **No reemplaza la consulta médica profesional.**  
> Siempre consulta con un médico certificado antes de tomar decisiones sobre tu salud.

---

<div align="center">

Hecho con ❤️ para la comunidad médica hispanohablante

**[⬆ Volver arriba](#-galeno-ia--asistente-médico-inteligente)**

</div>
