import re
import uuid
from typing import List, Dict

import chromadb
from chromadb.utils import embedding_functions


class DatabaseService:
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50  
    def __init__(self, persist_dir: str = "./chroma_store",
                 collection_name: str = "knowledge_base"):
        
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn,
        )

    def _chunk_text(self, text: str) -> List[str]:
        cleaned = re.sub(r"\s+", " ", text).strip()

        if not cleaned:
            return [] 

        chunks: List[str] = []
        start = 0
        text_len = len(cleaned)

        while start < text_len:
            end = start + self.CHUNK_SIZE
            chunks.append(cleaned[start:end])
            start += max(self.CHUNK_SIZE - self.CHUNK_OVERLAP, 1)
        return chunks

    def add_document(self, text: str, source: str = "unknown") -> int:
        chunks = self._chunk_text(text)
        if not chunks:
            return 0
        ids = [str(uuid.uuid4()) for _ in chunks]

        metadatas: List[Dict] = [
            {"source": source, "chunk_index": i} for i in range(len(chunks))
        ]

        self.collection.add(documents=chunks, ids=ids, metadatas=metadatas)
        return len(chunks)

    def query(self, question: str, n_results: int = 3) -> List[Dict]:

        if self.collection.count() == 0:
            return []


        n = min(n_results, self.collection.count())

        results = self.collection.query(query_texts=[question], n_results=n)

        documents = (results.get("documents") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]


        return [
            {
                "text": doc,
                "source": (meta or {}).get("source", "unknown"),
                "distance": dist,
            }
            for doc, meta, dist in zip(documents, metadatas, distances)
        ]
