from flask import Flask, request, jsonify
import chromadb
import ollama

app = Flask(__name__)

chroma = chromadb.PersistentClient(path="/home/orangepi/vectordb")
collection = chroma.get_or_create_collection("documentos_medicos")

@app.route('/preguntar', methods=['POST'])
def preguntar():
    data = request.json
    pregunta = data.get('pregunta', '')
    resultados = collection.query(query_texts=[pregunta], n_results=3)
    documentos = resultados['documents'][0] if resultados['documents'] else []
    if not documentos or all(doc.strip() == '' for doc in documentos):
        return jsonify({"respuesta": "No tengo informacion sobre eso en mis documentos medicos. Por favor consulta a un profesional de salud."})
    contexto = "\n\n".join(documentos)
    prompt = "Eres Neo IA, asistente medico estricto.\nINSTRUCCIONES:\n- Responde UNICAMENTE usando la informacion del contexto.\n- Si la pregunta no esta en el contexto responde: No tengo informacion sobre eso en mis documentos medicos.\n- NUNCA uses conocimiento propio.\n- Responde en espanol.\n\nContexto:\n" + contexto + "\n\nPregunta: " + pregunta + "\nRespuesta:"
    respuesta = ollama.chat(model="qwen2.5:1.5b", messages=[{"role":"user","content":prompt}])
    return jsonify({"respuesta": respuesta['message']['content']})

@app.route('/cargar', methods=['POST'])
def cargar():
    data = request.json
    texto = data.get('texto', '')
    nombre = data.get('nombre', 'documento')
    doc_id = data.get('id', nombre)
    if not texto.strip():
        return jsonify({"error": "Texto vacio"}), 400
    chunks = [texto[i:i+500] for i in range(0, len(texto), 500)]
    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    collection.upsert(documents=chunks, ids=ids)
    return jsonify({"ok": True, "chunks": len(chunks)})

@app.route('/documentos', methods=['GET'])
def listar_documentos():
    resultado = collection.get()
    total = len(resultado['ids']) if resultado['ids'] else 0
    return jsonify({"total_chunks": total})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
