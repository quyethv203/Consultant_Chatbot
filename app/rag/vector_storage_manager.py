# app/rag/vector_storage_manager.py

import os
from typing import Callable, Optional # <-- Them import nay

# <-- IMPORT CHROMA CLIENT TRUC TIEP THAY VI LANGCHAIN WRAPPER -->
import chromadb
from chromadb.api.models.Collection import Collection # Import Collection type hint
from langchain_community.vectorstores import Chroma # Import Chroma tu langchain_community.vectorstores
from langchain_core.documents import Document # Import Document cho ham retriever

# Import Config de lay duong dan DB va ten model
from app.core.config import Config

# Import ham get_embedding_model tu document_processor
# Dam bao import dung duong dan
from app.rag.document_processor import get_embedding_model

# Lop quan ly VectorStore
class VectorStoreManager:
    # Su dung bien lop de luu tru instance Chroma Client va Collection (Singleton pattern)
    _client_instance = None # Giu Chroma client persistent
    _collection_instance = None # Giu Chroma Collection instance
    _embedding_model = None # Van can luu tru embedding model instance
    _db_directory = None
    _collection_name = "document_collection" # Ten collection (dat mac dinh)

    def __init__(self):
        print("Tao instance VectorStoreManager lan dau...")
        self._db_directory = Config.VECTOR_DB_PATH
        self._model_name = Config.SENTENCE_TRANSFORMER_MODEL_NAME

        print("Khoi tao thuoc tinh cua VectorStoreManager...")
        print(f"Su dung duong dan Vector DB tu Config: {self._db_directory}")
        print(f"Su dung model embedding tu Config: {self._model_name}")
        print(f"Su dung ten collection: {self._collection_name}")
        print("VectorStoreManager da khoi tao thuoc tinh.")


    def load_vector_store(self) -> Collection | None: # Thay doi kieu tra ve thanh Collection
        """
        Tai VectorStore (Chroma Collection) tu duong dan da cau hinh.
        Neu Collection da duoc tai truoc do, tra ve instance dang ton tai.
        """
        print("\n--- Dang tai VectorStore (load_vector_store) ---")

        # Kiem tra neu instance Collection da ton tai
        if VectorStoreManager._collection_instance is not None:
            print("VectorStore Collection da duoc tai truoc do. Tra ve instance dang ton tai.")
            print("load_vector_store hoan tat, tra ve VectorStore Collection dang ton tai.")
            return VectorStoreManager._collection_instance

        # Neu instance chua ton tai, thu tai tu dia
        print(f"VectorStore Collection chua duoc tai. Thu tai tu '{self._db_directory}'...")

        # Kiem tra su ton tai cua thu muc DB
        print(f"Dang kiem tra su ton tai cua thu muc DB: {self._db_directory}")
        if not os.path.exists(self._db_directory) or not os.path.isdir(self._db_directory):
            print(f"WARNING: Thu muc Vector DB khong ton tai hoac khong hop le: {self._db_directory}")
            print("Vui long dam bao da chay script process_document.py de tao Vector DB.")
            print("load_vector_store hoan tat, tra ve None.")
            return None

        # Khoi tao Chroma client persistent neu chua co
        if VectorStoreManager._client_instance is None:
            print("Dang khoi tao Chroma client persistent...")
            try:
                VectorStoreManager._client_instance = chromadb.PersistentClient(path=self._db_directory)
                print("Da khoi tao Chroma client persistent.")
            except Exception as e:
                print(f"ERROR: Loi khi khoi tao Chroma client persistent tai {self._db_directory}: {e}")
                print("load_vector_store hoan tat, tra ve None do loi client.")
                return None

        # Tai Embedding Model neu chua tai
        if VectorStoreManager._embedding_model is None:
            print("Dang khoi tao Embedding Model...")
            VectorStoreManager._embedding_model = get_embedding_model()

            if VectorStoreManager._embedding_model is None:
                print("ERROR: Khong the khoi tao Embedding Model.")
                print("load_vector_store hoan tat, tra ve None do loi Embedding Model.")
                return None

            print("Da khoi tao Embedding Model thanh cong.")


        try:
            # Lay collection tu client.
            print(f"Dang lay collection '{self._collection_name}' tu client...")
            # Kiem tra collection co ton tai khong truoc khi get
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

            # DEBUG: In so luong items trong collection vua load
            print(f"--- DEBUG: So luong items trong Vector Store (sau khi load): {collection.count()} ---")


            # Luu tru instance Collection vao bien lop de su dung lai
            VectorStoreManager._collection_instance = collection
            print("load_vector_store hoan tat, tra ve VectorStore Collection.")
            return collection # Tra ve instance Collection

        except Exception as e:
            print(f"ERROR: Loi khi tai hoac ket noi den VectorStore Collection '{self._collection_name}' tai {self._db_directory}: {e}")
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
                VectorStoreManager._client_instance = None # Reset client instance
                VectorStoreManager._collection_instance = None # Reset collection instance
                print(f"Da xoa thu muc VectorStore: {self._db_directory} thanh cong.")
            else:
                print(f"Thu muc VectorStore khong ton tai: {self._db_directory}. Khong can xoa.")
        except Exception as e:
            print(f"ERROR: Loi khi xoa thu muc VectorStore {self._db_directory}: {e}")

    # Ham helper de lay Retriever tu Collection
    # Ham nay se duoc goi tu get_rag_chain
    def get_retriever_from_collection(self, collection: Collection, embeddings) -> Optional[Callable]: # <-- SUA DONG NAY
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
                       query_embeddings=[query_embedding], # Chroma query nhan list of embeddings
                       n_results=k, # So luong ket qua
                       include=['documents', 'metadatas', 'distances'] # Lay noi dung, metadata, khoang cach
                   )
                   print(f"Tim kiem trong collection hoan tat. Tim thay {len(results.get('documents', [])[0]) if results.get('documents') and results.get('documents')[0] else 0} ket qua.")

                   retrieved_docs = []
                   if results and results.get('documents') and results.get('documents')[0]:
                       for i in range(len(results['documents'][0])):
                           doc_content = results['documents'][0][i]
                           doc_metadata = results['metadatas'][0][i] if results.get('metadatas') and results.get('metadatas')[0] else {}
                           doc_distance = results['distances'][0][i] if results.get('distances') and results.get('distances')[0] else None

                           doc = Document(page_content=doc_content, metadata=doc_metadata)
                           retrieved_docs.append(doc)

                   print(f"Da chuyen doi {len(retrieved_docs)} ket qua sang Document objects.")
                   return retrieved_docs

              except Exception as e:
                   print(f"ERROR: Loi khi thuc hien retrieval: {e}")
                   return []

         print("Da tao ham Retriever thanh cong.")
         return retriever_function

