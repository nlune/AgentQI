import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import os
import sys
from pathlib import Path
import numpy as np
from utils.chunking import split_into_chunks


def concatenate_documents(hit_dict_list):
    added_docs = set()
    context = ""
    for hit_dict in hit_dict_list:
        for id, hit in zip(hit_dict['ids'][0], hit_dict["documents"][0]):
            if id not in added_docs:
                context += hit
                added_docs.add(id)
    return context

class VecDB:
    def __init__(self, settings: "BaseSettings", dbpath: str, collection_name: str, embedding_model: str):
        self.model = SentenceTransformer(embedding_model, device=settings.device)
        self.embedding_model = embedding_model
        self.chroma_client = chromadb.PersistentClient(path=dbpath)
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
        )

    def document_exists(self, doc_name: str) -> bool:
        """Check if a document is already in the collection."""
        try:
            results = self.collection.get(where={"source": doc_name}, limit=1)
            return len(results['ids']) > 0
        except Exception:
            return False

    def add_document(self, doc_name: str, doc_text: str):
        # Check if document already exists
        if self.document_exists(doc_name):
            print(f"Document '{doc_name}' already exists in the collection. Skipping.")
            return
            
        chunks, headers = split_into_chunks(doc_text)
        embeddings = self.model.encode(
            chunks, convert_to_numpy=True, show_progress_bar=True, batch_size=5
        )
        ids = [f"{doc_name}_{i}" for i in range(len(chunks))]
        metadatas = [
            {"source": doc_name, "chunk_idx": i, "header": headers[i]}
            for i in range(len(chunks))
        ]
        self.collection.upsert(
            ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas
        )

    def get_query_embedding(self, query: str):
        return self.model.encode(query, convert_to_numpy=True)

    def query(
        self,
        doc_name: str,
        query_embedding: np.ndarray,
        n_results: int = 5,
        where_filter: dict = None,
    ):
        if where_filter is None:
            where_filter = {"source": doc_name}

        hits = self.collection.query(
            query_embeddings=query_embedding,
            where=where_filter,
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        return hits

    def query_by_keyword(
        self,
        doc_name: str,
        query_embedding: np.ndarray,
        keywords: list,
        n_results: int = 5,
        where_filter: dict = None,
    ):
        if where_filter is None:
            where_filter = {"source": doc_name}

        search_list = [{"$contains": keyword} for keyword in keywords]

        where_doc = {"$or": search_list} if len(search_list) > 1 else search_list[0]

        hits = self.collection.query(
            query_embeddings=query_embedding,
            where=where_filter,
            n_results=n_results,
            where_document=where_doc,
            include=["documents", "metadatas", "distances"],
        )
        return hits
    
    def get_context(self, query:str, doc_name: str, keywords: list = None):
        q_emb = self.get_query_embedding(query)
        hit_dicts = []

        if keywords:
            hits = self.query_by_keyword(
                doc_name=doc_name, query_embedding=q_emb, keywords=keywords
            )
            hit_dicts.append(hits)

        hit_dicts.append(self.query(doc_name=doc_name, query_embedding=q_emb))

        return concatenate_documents(hit_dicts)
