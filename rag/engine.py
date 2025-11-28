import os
from dotenv import load_dotenv
load_dotenv()  # ← KLUCZOWE! Ładuje OPENAI_API_KEY zanim powstaną embeddingi

import json
from pathlib import Path
from typing import List, Literal, Dict, Any

import chromadb
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ---------------------------------------------------------
# 🔹 ŚCIEŻKI
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
PARSED_DIR = BASE_DIR / "rag" / "parsed"
VECTOR_DB_DIR = BASE_DIR / "vectorstore"
VECTOR_DB_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------
# 🔹 CHROMADB (persistent)
# ---------------------------------------------------------
chroma_client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))

collection = chroma_client.get_or_create_collection(
    name="korepetytor_materials",
    metadata={"purpose": "rag-materials"},
    embedding_function=None  # używamy embeddingów LangChain, nie Chroma
)

# ---------------------------------------------------------
# 🔹 EMBEDDER (tworzony JEDEN RAZ!)
# ---------------------------------------------------------
_embedder = OpenAIEmbeddings(model="text-embedding-3-large")


# ---------------------------------------------------------
# 🔹 Chunkowanie tekstu (uniwersalne, do JSON/tekstów)
# ---------------------------------------------------------
def chunk_text(text: str) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1100,
        chunk_overlap=180,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    return splitter.split_text(text)


# ---------------------------------------------------------
# 🔹 Rebuild RAG z jednego JSON
# ---------------------------------------------------------
def rebuild_rag_from_json(json_filename: str) -> int:
    """
    Czyści kolekcję i buduje embeddingi z jednego JSON-a w rag/parsed/.
    JSON musi mieć format:
        {"id": "...", "type": "...", "content": "..."}
    """
    json_path = PARSED_DIR / json_filename

    if not json_path.exists():
        raise FileNotFoundError(f"Brak pliku JSON: {json_path}")

    # Wczytaj JSON
    print(f"[RAG] Ładuję JSON: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        elements = json.load(f)

    # Czyścimy poprzednie rekordy
    try:
        collection.delete(where={"source": {"$exists": True}})
    except Exception as e:
        print("[WARN] Czyszczenie kolekcji:", e)

    all_chunks = []
    metadatas = []

    # Przerabiamy każdy element JSON na chunk-i
    for el in elements:
        content = el.get("content", "")
        if not content.strip():
            continue

        chunks = chunk_text(content)

        for c in chunks:
            all_chunks.append(c)
            metadatas.append({
                "source": json_filename,
                "id": el.get("id"),
                "type": el.get("type")
            })

    if not all_chunks:
        print("[RAG] Brak chunków do zapisania.")
        return 0

    # Generujemy embeddingi
    vectors = _embedder.embed_documents(all_chunks)

    # Zapisujemy do Chroma
    ids = [f"{json_filename}-{i}" for i in range(len(all_chunks))]

    collection.add(
        ids=ids,
        documents=all_chunks,
        embeddings=vectors,
        metadatas=metadatas
    )

    print(f"[RAG] OK — zapisano {len(all_chunks)} chunków z JSON.")
    return len(all_chunks)


# ---------------------------------------------------------
# 🔹 Rebuild RAG ze WSZYSTKICH JSON-ów (multi-PDF mode)
# ---------------------------------------------------------
def rebuild_rag_all() -> int:
    """
    Buduje RAG z wszystkich JSON-ów znajdujących się w rag/parsed/.
    """
    files = list(PARSED_DIR.glob("*.json"))
    if not files:
        raise RuntimeError("Brak JSON-ów w rag/parsed/!")

    try:
        collection.delete(where={"source": {"$exists": True}})
    except Exception:
        pass

    total_chunks = 0

    for file in files:
        print(f"[RAG] → {file.name}")
        total_chunks += rebuild_rag_from_json(file.name)

    print(f"[RAG] Całość gotowa — {total_chunks} chunków.")
    return total_chunks


# ---------------------------------------------------------
# 🔹 Zapytanie RAG
# ---------------------------------------------------------
def query_rag(question: str) -> List[str]:
    """
    Zwraca listę tekstowych chunków najbardziej dopasowanych do pytania.
    """
    q = _embedder.embed_query(question)

    results = collection.query(
        query_embeddings=[q],
        n_results=5
    )

    if not results or not results.get("documents"):
        return []

    return results["documents"][0]
