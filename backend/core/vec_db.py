import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import os
import sys
from pathlib import Path
import numpy as np
from utils.chunking import split_wordboxes_chunks
import ast  # Add this import at the top


def concatenate_documents(hit_dicts_list):
    """
    Concatenate documents from hit dictionaries and return metadata.
    Returns: (concatenated_text, list_of_metadata)
    Each chunk now formatted as:
    DOC_NAME <source> CHUNK_ID <chunk_idx>:
    <text>
    ---
    """
    documents = []
    all_metadata = []
    
    for hit_dict in hit_dicts_list:
        if hit_dict and 'documents' in hit_dict:
            docs = hit_dict['documents'][0] if hit_dict['documents'] else []
            metadatas = hit_dict['metadatas'][0] if hit_dict['metadatas'] else []
            
            for doc, metadata in zip(docs, metadatas):
                chunk_idx = metadata.get('chunk_idx', 'Unknown')
                header = metadata.get('header', '')
                source = metadata.get('source', 'Unknown')
                
                # Convert bbox string back to list
                bbox_str = metadata.get('bbox', '[]')
                try:
                    bbox = ast.literal_eval(bbox_str)
                except (ValueError, SyntaxError):
                    bbox = []
                
                # Build standardized prefix
                prefix = f"DOC_NAME {source} CHUNK_ID {chunk_idx}:"
                header_text = f" (Header: {header})" if header else ""
                body = f"{doc}".strip()
                formatted_doc = f"{prefix}\n{body}{header_text}\n---\n"
                documents.append(formatted_doc)
                
                metadata_copy = metadata.copy()
                metadata_copy['bbox'] = bbox
                all_metadata.append(metadata_copy)
    
    return ''.join(documents), all_metadata

class VecDB:
    def __init__(self, settings: "BaseSettings", dbpath: str = None, collection_name: str = "documents", embedding_model: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(embedding_model)
        self.embedding_model = embedding_model
        
        # Use path from settings if not provided
        db_path = dbpath or settings.db_path
        
        self.chroma_client = chromadb.PersistentClient(path=str(db_path))
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

    def add_document(self, doc_name: str, line_boxes: list):
        # Check if document already exists
        if self.document_exists(doc_name):
            print(f"Document '{doc_name}' already exists in the collection. Skipping.")
            return

        chunks, headers = split_wordboxes_chunks(line_boxes)
        embeddings = self.model.encode(
            chunks['chunk_text'], convert_to_numpy=True, show_progress_bar=True, batch_size=5
        )
        ids = [f"{doc_name}_{i}" for i in range(len(chunks['chunk_text']))]
        metadatas = [
            {"source": doc_name, "chunk_idx": i, "header": headers[i], "bbox": str(chunks['bboxes'][i]), "page": chunks['pages'][i]}
            for i in range(len(chunks["chunk_text"]))
        ]
        self.collection.upsert(
            ids=ids, documents=chunks['chunk_text'], embeddings=embeddings, metadatas=metadatas
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
    
    def get_context(self, query: str, doc_name: str, keywords: list = None):
        q_emb = self.get_query_embedding(query)
        hit_dicts = []

        if keywords:
            hits = self.query_by_keyword(
                doc_name=doc_name, query_embedding=q_emb, keywords=keywords
            )
            hit_dicts.append(hits)

        hit_dicts.append(self.query(doc_name=doc_name, query_embedding=q_emb))

        context, metadata = concatenate_documents(hit_dicts)
        return context, metadata
