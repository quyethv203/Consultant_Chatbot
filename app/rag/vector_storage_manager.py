import os
from typing import Callable, Optional

import chromadb
from chromadb.api.models.Collection import Collection
from langchain_core.documents import Document

from app.core.config import Config
from app.rag.document_processor import get_embedding_model


class VectorStoreManager:
    _client_instance = None
    _collection_instance = None
    _embedding_model = None
    _db_directory = None
    _collection_name = "document_collection"

    def __init__(self):
        print("Tao instance VectorStoreManager lan dau...")
        self._db_directory = Config.VECTOR_DB_PATH
        self._model_name = Config.SENTENCE_TRANSFORMER_MODEL_NAME

        print("Khoi tao thuoc tinh cua VectorStoreManager...")
        print(f"Su dung duong dan Vector DB tu Config: {self._db_directory}")
        print(f"Su dung model embedding tu Config: {self._model_name}")
        print(f"Su dung ten collection: {self._collection_name}")
        print("VectorStoreManager da khoi tao thuoc tinh.")

    def load_vector_store(self) -> Collection | None:
        """
        Tai VectorStore (Chroma Collection) tu duong dan da cau hinh.
        Neu Collection da duoc tai truoc do, tra ve instance dang ton tai.
        """
        print("\n--- Dang tai VectorStore (load_vector_store) ---")

        if VectorStoreManager._collection_instance is not None:
            print("VectorStore Collection da duoc tai truoc do. Tra ve instance dang ton tai.")
            print("load_vector_store hoan tat, tra ve VectorStore Collection dang ton tai.")
            return VectorStoreManager._collection_instance

        print(f"VectorStore Collection chua duoc tai. Thu tai tu '{self._db_directory}'...")

        print(f"Dang kiem tra su ton tai cua thu muc DB: {self._db_directory}")
        if not os.path.exists(self._db_directory) or not os.path.isdir(self._db_directory):
            print(f"WARNING: Thu muc Vector DB khong ton tai hoac khong hop le: {self._db_directory}")
            print("Vui long dam bao da chay script process_document.py de tao Vector DB.")
            print("load_vector_store hoan tat, tra ve None.")
            return None

        if VectorStoreManager._client_instance is None:
            print("Dang khoi tao Chroma client persistent...")
            try:
                VectorStoreManager._client_instance = chromadb.PersistentClient(path=self._db_directory)
                print("Da khoi tao Chroma client persistent.")
            except Exception as e:
                print(f"ERROR: Loi khi khoi tao Chroma client persistent tai {self._db_directory}: {e}")
                print("load_vector_store hoan tat, tra ve None do loi client.")
                return None

        if VectorStoreManager._embedding_model is None:
            print("Dang khoi tao Embedding Model...")
            VectorStoreManager._embedding_model = get_embedding_model()

            if VectorStoreManager._embedding_model is None:
                print("ERROR: Khong the khoi tao Embedding Model.")
                print("load_vector_store hoan tat, tra ve None do loi Embedding Model.")
                return None

            print("Da khoi tao Embedding Model thanh cong.")

        try:

            print(f"Dang lay collection '{self._collection_name}' tu client...")

            collection_list = [c.name for c in VectorStoreManager._client_instance.list_collections()]
            if self._collection_name not in collection_list:
                print(f"ERROR: Collection '{self._collection_name}' khong ton tai.")
                print("Vui long dam bao da chay script process_document.py de tao collection.")
                print("load_vector_store hoan tat, tra ve None.")
                return None

            collection = VectorStoreManager._client_instance.get_collection(
                name=self._collection_name,
            )
            print(f"Da lay collection '{self._collection_name}' thanh cong.")

            print(f"--- DEBUG: So luong items trong Vector Store (sau khi load): {collection.count()} ---")

            VectorStoreManager._collection_instance = collection
            print("load_vector_store hoan tat, tra ve VectorStore Collection.")
            return collection

        except Exception as e:
            print(
                f"ERROR: Loi khi tai hoac ket noi den VectorStore Collection '{self._collection_name}' tai {self._db_directory}: {e}")
            print("Kiem tra lai duong dan Vector DB va ten collection.")
            print("load_vector_store hoan tat, tra ve None do loi.")
            return None

    def delete_vector_store(self):
        """
        Xoa thu muc VectorStore.
        """
        print(f"\n--- Dang xoa thu muc VectorStore: {self._db_directory} ---")
        try:
            if os.path.exists(self._db_directory):
                import shutil
                shutil.rmtree(self._db_directory)
                VectorStoreManager._client_instance = None
                VectorStoreManager._collection_instance = None
                print(f"Da xoa thu muc VectorStore: {self._db_directory} thanh cong.")
            else:
                print(f"Thu muc VectorStore khong ton tai: {self._db_directory}. Khong can xoa.")
        except Exception as e:
            print(f"ERROR: Loi khi xoa thu muc VectorStore {self._db_directory}: {e}")

    def get_retriever_from_collection(self, collection: Collection, embeddings) -> Optional[Callable]:
        """
        Tao mot ham retriever tu Chroma Collection.
        Ham retriever nay se nhan vao query string va tra ve list of Document.
        """
        print("\n--- Dang tao Retriever tu Collection ---")
        if collection is None:
            print("ERROR: Collection la None. Khong the tao Retriever.")
            return None
        if embeddings is None:
            print("ERROR: Embedding Model la None. Khong the tao Retriever.")
            return None

        def retriever_function(query: str, k: int = 10) -> list[Document]:
            print(f"\n--- DEBUG TEST: Dang thuc hien retrieval cho query: '{query}' (k={k}) ---")
            try:
                query_embedding = embeddings.embed_query(query)
                print("Da tao embedding cho query.")

                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=k,
                    include=['documents', 'metadatas', 'distances']
                )
                print(
                    f"Tim kiem trong collection hoan tat. Tim thay {len(results.get('documents', [])[0]) if results.get('documents') and results.get('documents')[0] else 0} ket qua.")

                retrieved_docs = []
                if results and results.get('documents') and results.get('documents')[0]:
                    for i in range(len(results['documents'][0])):
                        doc_content = results['documents'][0][i]
                        doc_metadata = results['metadatas'][0][i] if results.get('metadatas') and \
                                                                     results.get('metadatas')[0] else {}
                        doc_distance = results['distances'][0][i] if results.get('distances') and \
                                                                     results.get('distances')[0] else None

                        doc = Document(page_content=doc_content, metadata=doc_metadata)
                        retrieved_docs.append(doc)

                print(f"Da chuyen doi {len(retrieved_docs)} ket qua sang Document objects.")
                return retrieved_docs

            except Exception as e:
                print(f"ERROR: Loi khi thuc hien retrieval: {e}")
                return []

        print("Da tao ham Retriever thanh cong.")
        return retriever_function
