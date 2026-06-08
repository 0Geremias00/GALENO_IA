import fitz
import chromadb
import os

chroma = chromadb.PersistentClient(path="/home/orangepi/vectordb")
col = chroma.get_or_create_collection("documentos_medicos")

# Cargar todos los PDFs en /home/orangepi/ automáticamente
pdf_dir = "/home/orangepi/"
pdfs = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.endswith(".pdf")]

if not pdfs:
    print("No se encontraron PDFs en", pdf_dir)
else:
    for pdf_path in pdfs:
        nombre = os.path.basename(pdf_path).replace(".pdf", "")
        print(f"Cargando: {nombre}")
        try:
            doc = fitz.open(pdf_path)
            texto_completo = ""
            for page in doc:
                texto_completo += page.get_text()
            doc.close()
            if not texto_completo.strip():
                print(f"  ⚠️ Sin texto (PDF escaneado o vacío): {nombre}")
                continue
            chunks = [texto_completo[i:i+500] for i in range(0, len(texto_completo), 500)]
            ids = [f"{nombre}_chunk_{i}" for i in range(len(chunks))]
            col.upsert(documents=chunks, ids=ids)
            print(f"  ✅ Cargado: {len(chunks)} chunks")
        except Exception as e:
            print(f"  ❌ Error en {nombre}: {e}")

print("\n✅ Proceso terminado!")
print(f"Total documentos en RAG: {col.count()}")
