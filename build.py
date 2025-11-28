import os
import glob
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_DIR = os.path.join(os.path.dirname(__file__), "db")

def load_all_documents():
    pdf_files = glob.glob(os.path.join(DATA_DIR, "*.pdf"))
    docs = []

    for pdf in pdf_files:
        print(f"📄 Loading PDF: {pdf}")
        loader = PyPDFLoader(pdf)
        docs.extend(loader.load())

    return docs

def split_docs(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
    )
    return splitter.split_documents(docs)

def build_embeddings():
    print("🚀 Starting RAG index rebuild...")
    docs = load_all_documents()
    print(f"📚 Loaded {len(docs)} pages from PDFs")

    chunks = split_docs(docs)
    print(f"🔍 Split into {len(chunks)} chunks")

    if os.path.exists(DB_DIR):
        print("🗑️ Removing old DB...")
        import shutil
        shutil.rmtree(DB_DIR)

    print("🧠 Building new vector DB...")
    Chroma.from_documents(
        chunks,
        OpenAIEmbeddings(),
        persist_directory=DB_DIR
    )

    print("✅ DONE! Embedding database rebuilt.")

if __name__ == "__main__":
    build_embeddings()
