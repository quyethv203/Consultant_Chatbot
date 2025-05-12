# app/rag/vector_storage_manager.py

import os
# Import Chroma tu langchain_community
from langchain_community.vectorstores import Chroma

# Import embedding model
# <-- SU DUNG HuggingFaceEmbeddings THAY VI SentenceTransformerEmbeddings -->
from langchain_huggingface import HuggingFaceEmbeddings # Import HuggingFaceEmbeddings

# Import Config de lay duong dan DB va ten model
from app.core.config import Config

# Import ham get_embedding_model tu document_processor
# Dam bao import dung duong dan
from app.rag.document_processor import get_embedding_model

# Lop quan ly VectorStore
class VectorStoreManager:
    # Su dung bien lop de luu tru instance VectorStore (Singleton pattern)
    # Dam bao chi co mot instance VectorStore duoc tai trong suot vong doi ung dung
    _vectorstore_instance = None
    _db_directory = None
    _embedding_model = None

    def __init__(self):
        print("Tao instance VectorStoreManager lan dau...") # <-- Them print
        # Khoi tao cac thuoc tinh cua instance
        self._db_directory = Config.VECTOR_DB_PATH # Lay duong dan DB tu Config
        # Khong khoi tao embedding model o day, chi lay thong tin ten model
        self._model_name = Config.SENTENCE_TRANSFORMER_MODEL_NAME # Lay ten model tu Config

        print("Khoi tao thuoc tinh cua VectorStoreManager...") # <-- Them print
        print(f"Su dung duong dan Vector DB tu Config: {self._db_directory}") # <-- Them print
        print(f"Su dung model embedding tu Config: {self._model_name}") # <-- Them print
        print("VectorStoreManager da khoi tao thuoc tinh.") # <-- Them print


    def load_vector_store(self) -> Chroma | None:
        """
        Tai VectorStore tu duong dan da cau hinh.
        Neu VectorStore da duoc tai truoc do, tra ve instance dang ton tai.
        """
        print("\n--- Dang tai VectorStore (load_vector_store) ---") # <-- Them print

        # Kiem tra neu instance VectorStore da ton tai
        if VectorStoreManager._vectorstore_instance is not None:
            print("VectorStore da duoc tai truoc do. Tra ve instance dang ton tai.") # <-- Them print
            print("load_vector_store hoan tat, tra ve VectorStore dang ton tai.") # <-- Them print
            return VectorStoreManager._vectorstore_instance # Tra ve instance dang co

        # Neu instance chua ton tai, thu tai tu dia
        print(f"VectorStore chua duoc tai. Thu tai tu '{self._db_directory}'...") # <-- Them print

        # Kiem tra su ton tai cua thu muc DB
        print(f"Dang kiem tra su ton tai cua thu muc DB: {self._db_directory}") # <-- Them print
        if not os.path.exists(self._db_directory) or not os.path.isdir(self._db_directory):
            print(f"WARNING: Thu muc Vector DB khong ton tai hoac khong hop le: {self._db_directory}") # <-- Print canh bao
            print("Vui long dam bao da chay script process_document.py de tao Vector DB.")
            print("load_vector_store hoan tat, tra ve None.") # <-- Them print
            return None # Tra ve None neu thu muc DB khong ton tai

        # Tai Embedding Model neu chua tai
        if VectorStoreManager._embedding_model is None:
            print("Dang khoi tao Embedding Model...") # <-- Them print
            VectorStoreManager._embedding_model = get_embedding_model() # Goi ham helper de lay model

            if VectorStoreManager._embedding_model is None:
                print("ERROR: Khong the khoi tao Embedding Model.") # <-- Print loi
                print("load_vector_store hoan tat, tra ve None do loi Embedding Model.") # <-- Them print
                return None # Tra ve None neu khong khoi tao duoc model

            print("Da khoi tao Embedding Model thanh cong.") # <-- Them print


        try:
            # Ket noi den VectorStore (Chroma) tu thu muc da luu tru
            print("Dang ket noi den VectorStore (Chroma)...") # <-- Them print
            # Su dung embedding_function de chi dinh model embedding
            vectorstore = Chroma(
                persist_directory=self._db_directory, # Duong dan luu tru DB
                embedding_function=VectorStoreManager._embedding_model # Embedding model
            )
            print("Da ket noi va tai VectorStore (Chroma) thanh cong.") # <-- Them print

            # Luu tru instance vao bien lop de su dung lai
            VectorStoreManager._vectorstore_instance = vectorstore
            print("load_vector_store hoan tat, tra ve VectorStore.") # <-- Them print
            return vectorstore # Tra ve instance VectorStore

        # <-- SUA CACH BAT NGOAI LE -->
        except Exception as e: # Bat bat ky loi nao xay ra trong qua trinh tai/ket noi DB
            print(f"ERROR: Loi khi tai hoac ket noi den VectorStore (Chroma) tai {self._db_directory}: {e}") # <-- IN RA LOI CU THE
            print("Kiem tra lai duong dan Vector DB va dinh dang du lieu.")
            print("load_vector_store hoan tat, tra ve None do loi.") # <-- Them print
            return None # Tra ve None neu co loi


    # Ham nay co the dung de xoa VectorStore (neu can)
    def delete_vector_store(self):
        """
        Xoa thu muc VectorStore.
        """
        print(f"\n--- Dang xoa thu muc VectorStore: {self._db_directory} ---") # <-- Them print
        try:
            if os.path.exists(self._db_directory):
                import shutil
                shutil.rmtree(self._db_directory)
                VectorStoreManager._vectorstore_instance = None # Reset instance
                print(f"Da xoa thu muc VectorStore: {self._db_directory} thanh cong.") # <-- Them print
            else:
                print(f"Thu muc VectorStore khong ton tai: {self._db_directory}. Khong can xoa.") # <-- Them print
        except Exception as e:
            print(f"ERROR: Loi khi xoa thu muc VectorStore {self._db_directory}: {e}") # <-- IN RA LOI CU THE


# Vi du su dung (co the bo hoac comment lai khi tich hop vao ung dung)
# if __name__ == "__main__":
#     # Dam bao Config da duoc cau hinh truoc khi chay
#     # Config.VECTOR_DB_PATH = 'path/to/your/chroma_db'
#     # Config.SENTENCE_TRANSFORMER_MODEL_NAME = 'all-MiniLM-L6-v2'

#     manager = VectorStoreManager()
#     vectorstore = manager.load_vector_store()

#     if vectorstore:
#         print("\nVectorStore da san sang.")
#         # Ban co the thuc hien cac thao tac tim kiem tai day de test
#         # query = "Pham vi dieu chinh cua quy che nay la gi?"
#         # docs = vectorstore.similarity_search(query)
#         # print(f"\nKet qua tim kiem cho '{query}':")
#         # for doc in docs:
#         #     print(doc.page_content[:200] + "...")
#     else:
#         print("\nKhong the tai VectorStore.")

#     # De xoa DB (can than khi su dung)
#     # manager.delete_vector_store()
