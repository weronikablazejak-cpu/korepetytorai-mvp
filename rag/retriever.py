from typing import List
from rag.engine import query_rag


def retrieve_chunks(question: str, k: int = 4) -> List[str]:
    """
    Zwraca listę tekstowych chunków z RAG — najwyżej dopasowanych do pytania.
    """
    try:
        chunks = query_rag(question)
    except Exception as e:
        print("[Retriever] Error:", e)
        return []

    # query_rag zwraca listę stringów — przycinamy do k
    return chunks[:k]
