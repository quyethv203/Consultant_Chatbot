import os
import random
import re
import time
from typing import List

import chromadb
from chromadb.api.models.Collection import Collection

from langchain_core.documents import Document

from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import Config
from app.rag.document_loaders_factory import get_document_loader_factory
from app.rag.text_splitting_strategies import TextSplitterContext, StructuredTextSplitterStrategy, \
    UnstructuredTextSplitterStrategy

try:
    import pytesseract
    from PIL import Image
    import fitz

    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    PYTESSERACT_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: Khong the import cac thu vien can thiet cho xu ly PDF voi pytesseract: {e}")
    print("Dam bao da cai dat: pip install pytesseract Pillow PyMuPDF")
    PYTESSERACT_AVAILABLE = False
except Exception as e:
    print(f"WARNING: Loi khi cau hinh pytesseract.pytesseract.tesseract_cmd: {e}")
    print("Dam bao duong dan Tesseract CLI la chinh xac.")
    PYTESSERACT_AVAILABLE = False

print(f"--- DEBUG TEST: PYTESSERACT_AVAILABLE = {PYTESSERACT_AVAILABLE} ---")


def load_and_process_pdf_with_pytesseract(file_path: str) -> List[Document]:
    """
    Loads a PDF, converts each page to an image, and extracts text using pytesseract.
    Returns a list of Documents, where each Document corresponds to the text of a page.
    """
    print(f"--- Dang xu ly file PDF: {file_path} bang PyMuPDF va pytesseract ---")
    if not PYTESSERACT_AVAILABLE:
        print(
            "Loi: pytesseract, Pillow hoac PyMuPDF chua duoc cai dat hoac cau hinh sai. Khong the xu ly PDF theo cach nay.")
        return []

    processed_documents = []
    try:
        doc = fitz.open(file_path)
        for i in range(doc.page_count):
            page = doc.load_page(i)

            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            print(f"--- Dang OCR trang {i + 1}/{doc.page_count} cua PDF ---")
            try:

                text = pytesseract.image_to_string(img, lang='vie', config='--oem 1')

                text = re.sub(r'\s+', ' ', text).strip()

                if text:
                    metadata = {
                        "source_file": os.path.basename(file_path),
                        "original_type": ".pdf",
                        "page_number": i + 1,
                        "file_path": file_path
                    }
                    processed_documents.append(Document(page_content=text, metadata=metadata))
                else:
                    print(f"Warning: Trang {i + 1} cua PDF khong co van ban sau OCR.")

            except Exception as e:
                print(f"ERROR: Loi OCR trang {i + 1} cua PDF: {e}")

        if not processed_documents:
            print(f"WARNING: Khong co van ban nao duoc trich xuat tu file PDF '{file_path}'.")
        return processed_documents

    except Exception as e:
        print(f"ERROR: Loi khi tai va xu ly PDF voi PyMuPDF va pytesseract: {e}")
        return []


def get_embedding_model():
    """
    Khoi tao va cau hinh Embedding Model.
    """
    print("\n--- Dang khoi tao Embedding Model (get_embedding_model) ---")
    if not hasattr(Config, 'SENTENCE_TRANSFORMER_MODEL_NAME') or not Config.SENTENCE_TRANSFORMER_MODEL_NAME:
        print("ERROR: Config.SENTENCE_TRANSFORMER_MODEL_NAME khong duoc tim thay.")
        print("Dam bao SENTENCE_TRANSFORMER_MODEL_NAME duoc dinh nghia trong config.py.")
        print("get_embedding_model hoan tat, tra ve None.")
        return None

    model_name = Config.SENTENCE_TRANSFORMER_MODEL_NAME
    print(f"Dang khoi tao HuggingFaceEmbeddings voi model: '{model_name}'")

    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print(f"Da khoi tao HuggingFaceEmbeddings voi model '{model_name}' thanh cong.")
        print("get_embedding_model hoan tat, tra ve Embedding Model.")
        return embeddings

    except Exception as e:
        print(f"ERROR: Loi khi khoi tao HuggingFaceEmbeddings voi model '{model_name}': {e}")
        print("Dam bao da cai dat thu vien langchain-huggingface, transformers va torch.")
        print("Kiem tra ket noi mang va ten model co chinh xac khong tren Hugging Face Hub.")
        print("get_embedding_model hoan tat, tra ve None do loi.")
        return None


def manually_store_chunks_in_vector_db(chunks: list[Document], embeddings) -> Collection | None:
    print("\n--- Dang tao Vector Database va luu tru Embeddings (manually_store_chunks_in_vector_db) ---")
    if not chunks:
        print("WARNING: Danh sach chunks dau vao rong. Khong the luu vao Vector DB.")
        print("manually_store_chunks_in_vector_db hoan tat, tra ve None.")
        return None

    if embeddings is None:
        print("ERROR: Embedding Model la None. Khong the luu vao Vector DB.")
        print("manually_store_chunks_in_vector_db hoan tat, tra ve None.")
        return None

    db_directory = Config.VECTOR_DB_PATH
    collection_name = "document_collection"
    print(f"Dang luu tru embeddings vao thu muc: {db_directory} voi collection '{collection_name}'")

    if not os.path.exists(db_directory):
        os.makedirs(db_directory)
        print(f"Da tao thu muc Vector DB: {db_directory}")

    try:
        print("Dang khoi tao Chroma client persistent...")
        client = chromadb.PersistentClient(path=db_directory)
        print("Da khoi tao Chroma client persistent.")

        print(f"Dang lay hoac tao collection '{collection_name}'...")
        collection = client.get_or_create_collection(
            name=collection_name,
        )
        print(f"Da lay hoac tao collection '{collection_name}'.")

        print("\n--- DEBUG TEST: Thong tin collection truoc khi add ---")
        print(f"Ten collection: {collection.name}")
        print(f"So luong items trong collection: {collection.count()}")
        print("--- KET THUC DEBUG TRUOC ADD ---")

        print(f"\nDang tao embeddings cho {len(chunks)} chunks...")
        chunk_texts = [chunk.page_content for chunk in chunks]

        chunk_ids = []
        for i, chunk in enumerate(chunks):
            source_info = chunk.metadata.get("source_file", "unknown_source").replace("\\", "_").replace("/",
                                                                                                         "_").replace(
                ":", "").replace(".", "_")

            page_number_info = chunk.metadata.get("page_number", "no_page")
            chunk_ids.append(f"{source_info}_page_{page_number_info}_chunk_{i}")

        chunk_metadatas = [chunk.metadata for chunk in chunks]

        print(
            f"Kiem tra chunk_texts: {len(chunk_texts)} items. Kieu item dau tien: {type(chunk_texts[0]) if chunk_texts else 'None'}")
        if chunk_texts:
            print(f"Noi dung 500 ky tu dau cua chunk_texts[0]: {chunk_texts[0][:500]}...")
        print("--- END DEBUG TRUOC EMBEDDING ---")

        start_time = time.time()
        chunk_embeddings = embeddings.embed_documents(chunk_texts)
        end_time = time.time()
        print(f"Da tao embeddings cho {len(chunk_embeddings)} chunks trong {end_time - start_time:.2f} giay.")

        print("\n--- DEBUG TEST: Thong tin embeddings sau khi tao ---")
        print(f"So luong embeddings tao ra: {len(chunk_embeddings)}")
        if chunk_embeddings:
            print(f"Kieu cua phan tu dau tien trong embeddings: {type(chunk_embeddings[0])}")
            if hasattr(chunk_embeddings[0], '__len__'):
                print(f"Kich thuoc (dimension) cua embedding dau tien: {len(chunk_embeddings[0])}")
            else:
                print("WARNING: Phan tu dau tien cua embeddings khong co thuoc tinh __len__.")
            print(f"Mot phan gia tri cua embedding dau tien: {chunk_embeddings[0][:10]}...")
        else:
            print("WARNING: Danh sach embeddings rong.")
        print("--- KET THUC DEBUG SAU EMBEDDING ---")

        print(f"\nDang them {len(chunks)} chunks va embeddings vao collection '{collection_name}'...")
        start_time = time.time()

        collection.add(
            embeddings=chunk_embeddings,
            documents=chunk_texts,
            metadatas=chunk_metadatas,
            ids=chunk_ids
        )
        end_time = time.time()
        print(f"Da them {len(chunks)} items vao collection trong {end_time - start_time:.2f} giay.")

        print("manually_store_chunks_in_vector_db hoan tat, tra ve Collection.")
        return collection

    except Exception as e:
        print(f"ERROR: Loi khi tao VectorStore (Chroma) hoac luu tru embeddings (Manual Add): {e}")
        print("Kiem tra lai duong dan Vector DB, dinh dang du lieu, va su tuong thich thu vien.")
        print("manually_store_chunks_in_vector_db hoan tat, tra ve None do loi.")
        return None


def process_document_pipeline():
    print("\n--- Bat dau pipeline xu ly tai lieu ---")

    print("Dang kiem tra cac cau hinh can thiet...")
    required_configs = [
        'DATA_DIRECTORY',
        'VECTOR_DB_PATH',
        'SENTENCE_TRANSFORMER_MODEL_NAME',
        'CHUNK_SIZE',
        'CHUNK_OVERLAP'
    ]
    missing_configs = [cfg for cfg in required_configs if not hasattr(Config, cfg) or getattr(Config, cfg) is None]

    if missing_configs:
        print("ERROR: Chua dap ung dieu kien tien quyet de chay pipeline xu ly tai lieu.")
        print("Cac cau hinh sau dang thieu hoac la None trong config.py:")
        for cfg in missing_configs:
            print(f"- Config.{cfg}")
        print("Pipeline xu ly tai lieu ket thuc som.")
        return

    print("Cac cau hinh can thiet da duoc tim thay.")

    all_processed_chunks = []

    data_dir = Config.DATA_DIRECTORY
    if not os.path.exists(data_dir):
        print(f"ERROR: Thu muc du lieu '{data_dir}' khong ton tai.")
        print("Pipeline xu ly tai lieu ket thuc som.")
        return

    files_to_process = [f for f in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, f))]

    if not files_to_process:
        print(f"WARNING: Khong tim thay file nao de xu ly trong thu muc '{data_dir}'.")
        print("Pipeline xu ly tai lieu ket thuc som.")
        return

    for file_name in files_to_process:
        file_path = os.path.join(data_dir, file_name)
        file_extension = os.path.splitext(file_name)[1].lower()
        print(f"\n--- Dang xu ly file: {file_name} ---")

        documents = []
        if file_extension == '.pdf':
            documents = load_and_process_pdf_with_pytesseract(file_path)
        else:

            try:
                loader_factory = get_document_loader_factory(file_path)
                document_loader = loader_factory.create_loader(file_path)
                print(f"Dang tai tai lieu tu: {file_path} bang docling...")
                documents = document_loader.load()

                if not documents:
                    print(f"ERROR: Khong the tai tai lieu '{file_name}' hoac tai lieu rong sau khi load bang docling.")
                    continue

                print(
                    f"Da tai tai lieu '{file_name}' thanh cong. Tong so ky tu: {sum(len(doc.page_content) for doc in documents)}")

            except Exception as e:
                print(f"ERROR: Loi khi tai tai lieu '{file_name}' bang docling: {e}")
                continue

        if not documents:
            print(f"ERROR: Khong co tai lieu nao duoc tai tu file '{file_name}'. Khong the chia chunk.")
            continue

        print(f"--- DEBUG TEST: Dang chia chunk cho file: {file_name} ---")
        chunk_size = Config.CHUNK_SIZE
        chunk_overlap = Config.CHUNK_OVERLAP

        text_splitter_strategy = None
        if file_extension in ['.txt', '.docx']:
            text_splitter_strategy = UnstructuredTextSplitterStrategy()
        elif file_extension == '.pdf':
            text_splitter_strategy = StructuredTextSplitterStrategy()
        else:
            print(
                f"WARNING: Khong co chien luoc chia van ban cu the cho dinh dang '{file_extension}'. Su dung chien luoc khong co cau truc.")
            text_splitter_strategy = UnstructuredTextSplitterStrategy()

        text_splitter_context = TextSplitterContext(text_splitter_strategy)

        full_document_content = "\n\n".join([doc.page_content for doc in documents])

        current_file_chunks = text_splitter_context.split_document_text(
            full_document_content,
            chunk_size,
            chunk_overlap
        )

        for chunk in current_file_chunks:
            chunk.metadata["source_file"] = file_name
            chunk.metadata["original_type"] = file_extension

            if file_extension == '.pdf' and documents:

                if "page_number" in documents[0].metadata:
                    chunk.metadata["page_number"] = documents[0].metadata["page_number"]

        if current_file_chunks is None or not current_file_chunks:
            print(f"WARNING: Chia chunk cho file '{file_name}' hoan tat nhung khong tao ra chunk nào.")
            continue

        all_processed_chunks.extend(current_file_chunks)

        if current_file_chunks:
            print(f"\n--- DEBUG TEST: NOI DUNG CUA MOT VAI CHUNK TU FILE {file_name} ---")
            if hasattr(current_file_chunks[0], 'page_content'):
                print(f"--- Chunk dau tien (do dai: {len(current_file_chunks[0].page_content)}) ---")
                print(f"Noi dung (500 ky tu dau): {current_file_chunks[0].page_content[:500]}...")
                print(f"Metadata: {current_file_chunks[0].metadata}")
                print("---------------------")

            if len(current_file_chunks) > 1:
                if hasattr(current_file_chunks[-1], 'page_content'):
                    print(f"--- Chunk cuoi cung (do dai: {len(current_file_chunks[-1].page_content)}) ---")
                    print(f"Noi dung (500 ky tu dau): {current_file_chunks[-1].page_content[:500]}...")
                    print(f"Metadata: {current_file_chunks[-1].metadata}")
                    print("---------------------")

            if len(current_file_chunks) > 3:
                print("--- Noi dung 3 chunk ngau nhien ---")
                random_chunks = random.sample(current_file_chunks, min(len(current_file_chunks), 3))
                for i, chunk in enumerate(random_chunks):
                    if hasattr(chunk, 'page_content'):
                        print(f"--- Chunk ngau nhien {i + 1} (do dai: {len(chunk.page_content)}) ---")
                        print(f"Noi dung (500 ky tu dau): {chunk.page_content[:500]}...")
                        print(f"Metadata: {chunk.metadata}")
                        print("---------------------")

            print(f"--- KET THUC DEBUG CHUNKING CHO FILE {file_name} ---")

    if not all_processed_chunks:
        print("ERROR: Khong co chunk nao duoc tao tu tat ca cac file da xu ly.")
        print("Pipeline xu ly tai lieu ket thuc som.")
        return

    embeddings = get_embedding_model()
    if embeddings is None:
        print("Pipeline xu ly tai lieu ket thuc som do lay/khoi tao Embedding Model that bai.")
        return

    vectorstore_collection = manually_store_chunks_in_vector_db(all_processed_chunks, embeddings)
    if vectorstore_collection is None:
        print("Pipeline xu ly tai lieu ket thuc som do luu tru vao Vector DB that bai.")
        return

    print("\n--- Pipeline xu ly tai lieu hoan tat thanh cong ---")


if __name__ == "__main__":
    process_document_pipeline()
