# Galeno IA 🏥
Asistente médico inteligente con IA local.

## Stack
- Ollama + qwen2.5:1.5b
- Flask + Gunicorn
- ChromaDB + RAG
- PostgreSQL
- Nginx
- Orange Pi 5 Ultra

## Archivos principales
- `backend.py` — API Flask (auth, conversaciones)
- `rag.py` — Servidor RAG con ChromaDB
- `cargar_pdfs.py` — Script carga de PDFs al RAG
