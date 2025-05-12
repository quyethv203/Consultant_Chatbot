# app/rag/document_processor.py

# --- DEBUG TEST: THEM DONG PRINT NAY NGAY DAU FILE ---
print("--- DEBUG TEST: FILE app/rag/document_processor.py DANG DUOC THUC THI ---")
# --- END DEBUG TEST ---

import os
import random  # Import thu vien random

import pytesseract  # Wrapper Python cho Tesseract OCR
# Import text splitter. Kiem tra lai import path nay tuy phien ban LangChain da cai
# Tu langchain.text_splitter hoac langchain_community.text_splitter
from langchain.text_splitter import RecursiveCharacterTextSplitter  # De chia van ban thanh cac phan nho (chunks)
from langchain_community.vectorstores import Chroma  # De luu tru va tim kiem vector
from langchain_core.documents import Document  # Import Document de lam viec voi ket qua retrieve
# Import embedding model
# <-- SU DUNG HuggingFaceEmbeddings THAY VI SentenceTransformerEmbeddings -->
# Dam bao da cai dat langchain-huggingface, transformers va torch
from langchain_huggingface import HuggingFaceEmbeddings  # Import HuggingFaceEmbeddings
# Import cac thu vien cho OCR
from pdf2image import convert_from_path  # De chuyen PDF sang anh

# Import Config de lay duong dan file va ten model, chunk size/overlap
from app.core.config import Config

# Import cac component tu LangChain de xu ly document va tao embeddings/vectorstore
# Import PyPDFLoader (van can de load cau truc trang)

# --- Cau hinh duong dan den Tesseract executable ---
# Ban can thay the duong dan nay bang duong dan thuc te den tesseract.exe tren may cua ban
# Vi du tren Windows: r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Vi du tren Linux/macOS: co the khong can dong nay neu tesseract nam trong PATH
# Kiem tra xem Config co TESSERACT_PATH khong, neu khong thi dat mac dinh hoac bao loi
if hasattr(Config, 'TESSERACT_PATH') and Config.TESSERACT_PATH:
    try:
        pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_PATH
        print(f"Da cau hinh duong dan Tesseract: {Config.TESSERACT_PATH}")
    except Exception as e:
        print(f"ERROR: Khong the cau hinh duong dan Tesseract '{Config.TESSERACT_PATH}': {e}")
        print("Vui long kiem tra lai duong dan TESSERACT_PATH trong config.py.")
        # Tiep tuc chay, pytesseract se thu tim trong PATH he thong
else:
    # Neu khong co TESSERACT_PATH trong config, pytesseract se thu tim trong PATH
    # In canh bao neu khong tim thay trong config
    print("WARNING: Config.TESSERACT_PATH khong duoc thiet lap trong config.py.")
    print("pytesseract se thu tim Tesseract trong PATH he thong.")
    print(
        "Neu gap loi 'TesseractNotFound', vui long cai dat Tesseract OCR engine va thiet lap bien moi truong PATH hoac Config.TESSERACT_PATH.")


# --- Ham helper de lay Embedding Model ---
# Ham nay duoc goi tu process_document_pipeline va tu VectorStoreManager
def get_embedding_model():
    """
    Khoi tao va cau hinh Embedding Model.
    """
    print("\n--- Dang khoi tao Embedding Model (get_embedding_model) ---") # <-- Them print dau ham
    # Check xem Config.SENTENCE_TRANSFORMER_MODEL_NAME da co chua
    if not hasattr(Config, 'SENTENCE_TRANSFORMER_MODEL_NAME') or not Config.SENTENCE_TRANSFORMER_MODEL_NAME:
        print("ERROR: Config.SENTENCE_TRANSFORMER_MODEL_NAME khong duoc tim thay.") # <-- Print loi
        print("Dam bao SENTENCE_TRANSFORMER_MODEL_NAME duoc dinh nghia trong config.py.")
        print("get_embedding_model hoan tat, tra ve None.") # <-- Them print
        return None

    model_name = Config.SENTENCE_TRANSFORMER_MODEL_NAME # Lay ten model tu config
    print(f"Dang khoi tao HuggingFaceEmbeddings voi model: '{model_name}'") # <-- SUA PRINT

    try:
        # Khoi tao HuggingFaceEmbeddings voi ten model tu config
        # model_kwargs co the dung de cau hinh device (cpu/cuda)
        # encode_kwargs co the dung de cau hinh pooling
        embeddings = HuggingFaceEmbeddings(model_name=model_name, model_kwargs={'device': 'cpu'}) # Mac dinh dung CPU
        print(f"Da khoi tao HuggingFaceEmbeddings voi model '{model_name}' thanh cong.") # <-- SUA PRINT
        print("get_embedding_model hoan tat, tra ve Embedding Model.") # <-- Them print
        return embeddings # Tra ve instance model da khoi tao

    # <-- SUA CACH BAT NGOAI LE -->
    except Exception as e: # Bat bat ky loi nao xay ra trong qua trinh khoi tao/tai model
        print(
            f"ERROR: Loi khi khoi tao HuggingFaceEmbeddings voi model '{model_name}': {e}")  # <-- SUA PRINT VA IN RA THONG TIN LOI CU THE
        print("Dam bao da cai dat thu vien langchain-huggingface, transformers va torch.")
        print("Kiem tra ket noi mang va ten model co chinh xac khong tren Hugging Face Hub.")
        print("get_embedding_model hoan tat, tra ve None do loi.") # <-- Them print
        return None # Tra ve None neu co loi


# --- Ham thuc hien OCR tren file PDF ---
def perform_ocr_on_pdf(file_path: str) -> str | None:
    print(f"\n--- Dang thuc hien OCR tren file: {file_path} ---")  # <-- Them print
    full_text = ""  # Bien luu tru toan bo van ban sau OCR
    try:
        if not os.path.exists(file_path):
            print(f"ERROR: File tai lieu khong ton tai de thuc hien OCR: {file_path}")  # <-- Print loi
            print("perform_ocr_on_pdf hoan tat, tra ve None.")  # <-- Them print
            return None  # Tra ve None neu file khong ton tai

        # Chuyen doi tung trang PDF sang anh
        print("Dang chuyen doi cac trang PDF sang anh...")  # <-- Them print
        # DPI 300 thuong cho ket qua OCR tot hon 200 mac dinh
        images = convert_from_path(file_path, dpi=300)

        print(f"Da chuyen doi thanh cong {len(images)} trang sang anh. Dang thuc hien OCR...")  # <-- Them print

        # Thuc hien OCR tren tung anh va ghep noi dung
        for i, image in enumerate(images):
            print(f"Dang thuc hien OCR cho trang {i + 1}/{len(images)}...")  # <-- Them print
            # Su dung pytesseract de lay text tu anh
            # lang='vie' de su dung ngon ngu Tieng Viet (can cai dat data ngon ngu cho Tesseract)
            # config='--psm 6' (Page Segmentation Mode) co the giup cai thien ket qua tuy loai tai lieu
            try:
                # Them timeout de tranh bi treo neu trang bi loi
                text = pytesseract.image_to_string(image, lang='vie', timeout=15)  # Thuc hien OCR
                full_text += text + "\n\n--- Trang Ket Thuc ---\n\n"  # Them text cua trang va dau phan cach ro rang
                print(f"OCR trang {i + 1} hoan tat. Trich xuat duoc {len(text)} ky tu.")  # <-- Them print
            except Exception as e:
                print(f"WARNING: Loi khi thuc hien OCR cho trang {i + 1}: {e}")  # <-- IN RA LOI CU THE nhung tiep tuc
                full_text += f"\n\n--- Loi OCR Trang {i + 1} ---\n\n"  # Them dau hieu loi

        print(f"OCR tren toan bo file hoan tat. Tong so ky tu trich xuat: {len(full_text)}")  # <-- Them print
        print("perform_ocr_on_pdf hoan tat, tra ve toan bo van ban sau OCR.")  # <-- Them print
        return full_text  # Tra ve toan bo van ban sau OCR

    # <-- SUA CACH BAT NGOAI LE -->
    except Exception as e:  # Bat bat ky loi nao xay ra trong qua trinh OCR
        print(f"ERROR: Loi xay ra trong qua trinh OCR tren file {file_path}: {e}")  # <-- IN RA LOI CU THE
        print("perform_ocr_on_pdf hoan tat, tra ve None do loi.")  # <-- Them print
        return None  # Tra ve None neu co loi nghiem trong


# --- Ham chia van ban thanh cac chunk nho (nhan vao string) ---
# <-- SUA HAM split_document DE NHAN VAO STRING VA DEBUG -->
def split_document_text(text: str) -> list[Document] | None:
    print("\n--- Dang chia van ban (string) thanh cac chunk (split_document_text) ---")  # <-- Them print dau ham
    if not text or not text.strip():  # Kiem tra text co rong hoac chi chua khoang trang khong
        print("WARNING: Van ban dau vao rong hoac chi chua khoang trang. Khong the chia chunk.")  # <-- Print canh bao
        print("split_document_text hoan tat, tra ve danh sach chunk rong.")  # <-- Them print
        return []  # Tra ve danh sach rong neu text rong

    # Debug: In ra mot phan noi dung cua text dau vao
    print(f"Do dai van ban dau vao: {len(text)}")  # <-- Them print
    # In ra noi dung 2000 ky tu dau tien cua text dau vao
    print(f"Noi dung 2000 ky tu dau tien cua van ban dau vao:\n---\n{text[:2000]}\n---") # <-- Tang len 2000 ky tu


    # Dam bao Config.CHUNK_SIZE va Config.CHUNK_OVERLAP duoc dinh nghia trong config.py
    chunk_size = Config.CHUNK_SIZE
    chunk_overlap = Config.CHUNK_OVERLAP
    print(
        f"Dang chia van ban thanh cac chunk voi kich thuoc {chunk_size} va overlap {chunk_overlap}...")  # <-- Them print

    # Dinh nghia separators (co thể đặt bên trong hàm nếu chỉ dùng ở đây)
    # <-- SU DUNG SEPARATORS KET HOP CAU TRUC VA DON GIAN -->
    structure_and_simple_separators = [
        r'\nChương\s+[IVXLCDM\d]+\s*[\.:]', # Nhan dien "Chuong I", "Chuong II", "Chuong 1", ...
        r'\nĐiều\s+\d+\s*[\.]?',          # Nhan dien "Dieu 1.", "Dieu 2", ...
        "\n\n",                           # Chia theo doan rong
        "\n",                             # Chia theo dong moi
        " ",                              # Chia theo khoang trang
        "",                               # Chia theo ky tu (khi khong con cach nao khac)
    ]


    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,  # Doc tu config
            chunk_overlap=chunk_overlap,  # Doc tu config
            separators=structure_and_simple_separators,  # <-- SU DUNG SEPARATORS KET HOP
            length_function=len,  # Mac dinh la len
            is_separator_regex=True # <-- DAT LA TRUE VI DUNG REGEX
        )
        # Chia van ban (string) thanh cac text chunk
        # split_text tra ve list of strings
        string_chunks = text_splitter.split_text(text)  # <-- SU DUNG split_text cho string

        # Chuyen doi cac string chunks thanh Document objects
        # Giu lai metadata tu document goc neu can (can truyen documents goc vao day)
        # Tam thoi chi tao Document tu string, metadata co the bo sung sau
        chunks = [Document(page_content=chunk) for chunk in string_chunks]  # <-- Tao Document tu string chunks

        print(f"Da chia thanh cong {len(chunks)} chunk.")  # <-- Them print
        print("split_document_text hoan tat, tra ve danh sach chunks (Document objects).")  # <-- Them print

        # Debug: In ra mot phan noi dung cua cac chunk vua tao (neu co)
        if chunks:
            print("\n--- DEBUG TEST: NOI DUNG CUA MOT VAI CHUNK DA TAO ---") # <-- Them print
            # In ra noi dung 500 ky tu dau tien cua chunk dau tien va chunk cuoi cung
            if hasattr(chunks[0], 'page_content'):
                 print(f"--- Chunk dau tien (do dai: {len(chunks[0].page_content)}) ---") # <-- Them do dai
                 print(f"Noi dung (500 ky tu dau): {chunks[0].page_content[:500]}...") # <-- Them ...
                 print("---------------------")
            else:
                 print("WARNING: Chunk dau tien khong co thuoc tinh 'page_content'.") # <-- Them print

            if len(chunks) > 1:
                 if hasattr(chunks[-1], 'page_content'): # In ra chunk cuoi cung
                      print(f"--- Chunk cuoi cung (do dai: {len(chunks[-1].page_content)}) ---") # <-- Them do dai
                      print(f"Noi dung (500 ky tu dau): {chunks[-1].page_content[:500]}...") # <-- Them ...
                      print("---------------------")
                 else:
                      print("WARNING: Chunk cuoi cung khong co thuoc tinh 'page_content'.") # <-- Them print

            # In ra noi dung 3 chunk ngau nhien (neu co du)
            if len(chunks) > 3:
                 print("--- Noi dung 3 chunk ngau nhien ---") # <-- Them print
                 random_chunks = random.sample(chunks, min(len(chunks), 3)) # Chon ngau nhien, gioi han so luong
                 for i, chunk in enumerate(random_chunks):
                      if hasattr(chunk, 'page_content'):
                           print(f"--- Chunk ngau nhien {i+1} (do dai: {len(chunk.page_content)}) ---") # <-- Them do dai
                           print(f"Noi dung (500 ky tu dau): {chunk.page_content[:500]}...") # <-- Them ...
                           print("---------------------")
                      else:
                           print(f"WARNING: Chunk ngau nhien {i+1} khong co thuoc tinh 'page_content'.") # <-- Them print

            print("--- KET THUC DEBUG CHUNKING ---") # <-- Them print


        return chunks  # Tra ve danh sach chunks (co the rong)

    # <-- SUA CACH BAT NGOAI LE -->
    except Exception as e:  # Bat bat ky loi nao xay ra trong qua trinh chia chunk
        print(f"ERROR: Loi khi chia van ban (string) thanh chunk: {e}")  # <-- IN RA LOI CU THE
        print("split_document_text hoan tat, tra ve None do loi.")  # <-- Them print
        return None  # Tra ve None neu co loi


# --- Ham tao Vector Database va luu tru Embeddings ---
def store_chunks_in_vector_db(chunks: list[Document], embeddings) -> Chroma | None:
    print("\n--- Dang tao Vector Database va luu tru Embeddings (store_chunks_in_vector_db) ---")  # <-- Them print
    if not chunks:
        print("WARNING: Danh sach chunks dau vao rong. Khong the luu vao Vector DB.")  # <-- Print canh bao
        print("store_chunks_in_vector_db hoan tat, tra ve None.")  # <-- Them print
        return None  # Tra ve None neu chunks rong

    if embeddings is None:
        print("ERROR: Embedding Model la None. Khong the luu vao Vector DB.")  # <-- Print loi
        print("store_chunks_in_vector_db hoan tat, tra ve None.")  # <-- Them print
        return None  # Tra ve None neu embeddings la None

    # Lay duong dan DB tu Config
    # Dam bao Config.VECTOR_DB_PATH da duoc set va tro den app/data/chroma_db
    db_directory = Config.VECTOR_DB_PATH
    print(f"Dang luu tru embeddings vao thu muc: {db_directory}")  # <-- Them print

    # --- DEBUG: Kiem tra du lieu truoc khi goi Chroma.from_documents ---
    print("\n--- DEBUG TEST: Du lieu truoc khi goi Chroma.from_documents ---")
    print(f"So luong chunks: {len(chunks)}")
    print(f"Kieu cua doi tuong embeddings: {type(embeddings)}")
    if chunks:
        print(f"Kieu cua phan tu dau tien trong chunks: {type(chunks[0])}")
        if hasattr(chunks[0], 'page_content'):
            print(f"Noi dung cua chunk dau tien (500 ky tu dau): {chunks[0].page_content[:500]}...")
        if hasattr(chunks[0], 'metadata'):
            print(f"Metadata cua chunk dau tien: {chunks[0].metadata}")
    print("--- KET THUC DEBUG TRUOC CHROMA ---")
    # --- END DEBUG ---


    try:
        # Khoi tao Chroma hoac ket noi den Chroma DB neu da ton tai
        # Su dung persist_directory de chi dinh thu muc luu tru
        # Su dung embedding_function de chi dinh model embedding
        # Neu thu muc chua co du lieu, add_documents se them moi
        # Neu thu muc da co du lieu, Chroma will load len va add_documents se them vao (hoac cap nhat tuy logic)
        print("Dang goi Chroma.from_documents...")  # <-- Them print
        vectorstore = Chroma.from_documents(
            documents=chunks,  # Cac text chunk da chia
            embedding=embeddings,  # Embedding model de tao vector
            persist_directory=db_directory  # Duong dan luu tru DB
        )
        print(f"Da tao/ket noi VectorStore (Chroma) thanh cong tai {db_directory}.")  # <-- Them print

        # Day la buoc luu tru embeddings vao dia.
        # Voi Chroma.from_documents, buoc persist() thuong duoc goi tu dong ben trong.
        # Tuy nhien, goi ro rang persist() la cach an toan de dam bao du lieu duoc ghi xuong dia.
        # Kiem tra xem instance vectorstore co phuong thuc persist() khong
        if hasattr(vectorstore, "persist"):
            print("Dang luu tru (persist) Vector Database...")  # <-- Them print
            try:
                vectorstore.persist()  # Luu tru du lieu vao dia
                print("Da luu tru (persist) Vector Database thanh cong.")  # <-- Them print
            # <-- SUA CACH BAT NGOAI LE -->
            except Exception as e:
                print(f"ERROR: Loi khi luu tru (persist) Vector Database: {e}")  # <-- IN RA LOI CU THE
                # Loi persist co the do quyen ghi hoac loi dia
                print("store_chunks_in_vector_db hoan tat, tra ve None do loi persist.")  # <-- Them print
                return None  # Tra ve None neu luu tru that bai
        else:
            print(
                "WARNING: Instance VectorStore khong co phuong thuc 'persist()'. Du lieu co the da duoc luu tu dong hoac chua duoc luu.")  # <-- Them print

        print("store_chunks_in_vector_db hoan tat, tra ve VectorStore.")  # <-- Them print
        return vectorstore  # Tra ve instance VectorStore vua tao/tai

    # <-- SUA CACH BAT NGOAI LE -->
    except Exception as e:  # Bat bat ky loi nao xay ra trong qua trinh tao VectorStore/luu tru
        print(f"ERROR: Loi khi tao VectorStore (Chroma) hoac luu tru embeddings: {e}")  # <-- IN RA LOI CU THE
        print("store_chunks_in_vector_db hoan tat, tra ve None do loi.")  # <-- Them print
        return None  # Tra ve None neu co loi o buoc nay


# --- Ham pipeline chinh ---
def process_document_pipeline():
    print("\n--- Bat dau pipeline xu ly tai lieu ---")  # <-- Them print dau pipeline

    # --- Buoc 0: Kiem tra cac cau hinh can thiet ---
    print("Dang kiem tra cac cau hinh can thiet...")  # <-- Them print
    # Dam bao cac cau hinh can thiet ton tai trong config.py
    # CHUNK_SIZE va CHUNK_OVERLAP can duoc them vao config.py
    required_configs = [
        'DOCUMENT_PATH',
        'VECTOR_DB_PATH',
        'SENTENCE_TRANSFORMER_MODEL_NAME', # Giu ten bien nay de tuong thich nguoc
        'CHUNK_SIZE',
        'CHUNK_OVERLAP'
        # Them TESSERACT_PATH vao danh sach kiem tra neu ban muon bat buoc thiet lap
        # 'TESSERACT_PATH'
    ]
    missing_configs = [cfg for cfg in required_configs if not hasattr(Config, cfg) or getattr(Config, cfg) is None]

    # Kiem tra rieng TESSERACT_PATH neu no khong bat buoc nhung can canh bao
    if not hasattr(Config, 'TESSERACT_PATH') or not Config.TESSERACT_PATH:
        print(
            "WARNING: Config.TESSERACT_PATH khong duoc thiet lap. OCR co the khong hoat dong neu Tesseract khong co trong PATH.")


    if missing_configs:
        print("ERROR: Chua dap ung dieu kien tien quyet de chay pipeline xu ly tai lieu.")  # <-- Them print
        print("Cac cau hinh sau dang thieu hoac la None trong config.py:")
        for cfg in missing_configs:
            print(f"- Config.{cfg}")
        print("Pipeline xu ly tai lieu ket thuc som.")  # <-- Them print
        return  # Thoat neu thieu config

    print("Cac cau hinh can thiet da duoc tim thay.")  # <-- Them print


    # --- Buoc 1.5: Thuc hien OCR de trich xuat van ban tu PDF ---
    ocr_text = perform_ocr_on_pdf(Config.DOCUMENT_PATH)
    if ocr_text is None:
        print("Pipeline xu ly tai lieu ket thuc som do thuc hien OCR that bai.")  # <-- Them print
        return  # Thoat neu OCR that bai

    if not ocr_text or not ocr_text.strip():
        print("ERROR: Thuc hien OCR thanh cong nhung khong trich xuat duoc van ban nao.")  # <-- Print loi
        print("Kiem tra lai file PDF hoac cau hinh Tesseract/ngon ngu.")
        print("Pipeline xu ly tai lieu ket thuc som.")  # <-- Them print
        return  # Thoat neu OCR khong ra text


    # --- Buoc 2: Chia van ban da OCR thanh cac chunk nho ---
    # Truyen van ban da OCR vao ham chia chunk moi
    print("--- DEBUG TEST: GOI HAM split_document_text() ---") # <-- THEM DONG NAY
    chunks = split_document_text(ocr_text)  # <-- GOI HAM CHIA CHUNK MOI CHO STRING

    # split_document_text tra ve [] neu dau vao rong, hoac None neu co loi
    if chunks is None:  # Chi kiem tra None (khi co loi)
        print("Pipeline xu ly tai lieu ket thuc som do chia chunk that bai.")  # <-- Them print
        return  # Thoat neu chia chunk that bai

    if not chunks:  # Kiem tra sau khi chia chunk co tao ra chunk nao khong
        print("WARNING: Chia chunk hoan tat nhung khong tao ra chunk nao.")  # <-- Print canh bao
        print("Khong co chunk de luu vao Vector DB. Pipeline ket thuc.")  # <-- Them print
        return  # Thoat neu khong co chunk nao duoc tao


    # --- Buoc 3: Tao Embedding Model ---
    embeddings = get_embedding_model()
    if embeddings is None:
        print("Pipeline xu ly tai lieu ket thuc som do lay/khoi tao Embedding Model that bai.")  # <-- Them print
        return  # Thoat neu lay embedding that bai

    # --- Buoc 4: Tao Vector Database va luu tru Embeddings ---
    vectorstore = store_chunks_in_vector_db(chunks, embeddings)
    if vectorstore is None:
        print("Pipeline xu ly tai lieu ket thuc som do luu tru vao Vector DB that bai.")  # <-- Them print
        return  # Thoat neu luu tru that bai

    print("\n--- Pipeline xu ly tai lieu hoan tat thanh cong ---")  # <-- Them print cuoi cung

# --- Goi ham pipeline khi script chay truc tiep ---
if __name__ == "__main__":
    # Dieu kien tien quyet (cac cau hinh can thiet)
    # Logic kiem tra dieu kien tien quyet da chuyen vao dau ham process_document_pipeline()
    process_document_pipeline()  # Goi ham pipeline chinh
