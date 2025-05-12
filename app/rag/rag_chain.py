# app/rag/rag_chain.py

# Import cac component cua LangChain
from langchain_core.runnables import RunnablePassthrough  # De truyen du lieu qua cac buoc trong chain
from langchain_core.output_parsers import StrOutputParser  # De chuyen output tu LLM thanh chuoi don gian
# Import ChatGoogleGenerativeAI de su dung model chat cua Gemini
from langchain_google_genai import ChatGoogleGenerativeAI  # Wrapper cua LangChain cho Gemini Chat
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document # Import Document de lam viec voi ket qua retrieve

# Import cac component RAG da xay dung
# <-- DAM BAO IMPORT DUNG VectorStoreManager (khong phai VectorStore) -->
from app.rag.vector_storage_manager import VectorStoreManager  # De lay VectorStore va thuc hien retrieval

# Import cau hinh
from app.core.config import Config

# --- Cau hinh Prompt Template cho RAG ---
# Mau prompt huong dan LLM su dung context da cho de tra loi cau hoi
PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    # System message: Dat vai tro cho mo hinh va huong dan cach tra loi
    ("system", """Ban la mot tro ly AI huu ich chuyen tra loi cac cau hoi ve tai lieu duoc cung cap.
    Hay tong hop thong tin tu cac doan van ban ngu canh sau de tra loi cau hoi cua nguoi dung.
    Neu thong tin lien quan khong co trong cac doan duoc cung cap,
    hay noi mot cach lich su rang ban khong tim thay thong tin do TRONG CAC DOAN DUOC CUNG CAP.
    Neu ban tim thay thong tin lien quan nhung khong du de tra loi day du, hay cung cap thong tin ban co va noi ro rang no co the khong hoan chinh.
    KHONG tra loi cau hoi bang kien thuc chung cua ban.

    Ngu canh:
    {context}"""), # Placeholder cho ngu canh (các đoạn văn bản từ Vector DB)

    # User message: Chua cau hoi goc cua nguoi dung
    ("user", "{question}"), # Placeholder cho cau hoi cua nguoi dung
])


# Dong print nay da chuyen sang dau ham get_rag_chain() hoac co the xoa
# print(f"GEMINI_API_KEY trong Config: {Config.GEMINI_API_KEY}")

# --- Ham tao va tra ve RAG Chain ---
def get_rag_chain():
    """
    Tao va cau hinh chuoi RAG (LangChain chain).
    Chuoi nay se thuc hien: nhan cau hoi -> truy xuat context -> xay prompt -> goi LLM -> tra ve phan hoi.
    """
    print("--- DEBUG TEST: DA VAO HAM GET_RAG_CHAIN ---")
    print("\n--- Dang tao RAG Chain ---")  # <-- Them print de theo doi

    # --- Buoc 1: Kiem tra API Key va Khoi tao LLM (Gemini Chat Model) ---
    print("Dang kiem tra GEMINI_API_KEY va khoi tao LLM...")  # <-- Them print
    # Dong print API key chuyen vao day de kiem tra gia tri tai thoi diem chay ham
    # print(f"GEMINI_API_KEY trong Config (trong get_rag_chain): {Config.GEMINI_API_KEY}") # Tam thoi bo comment dong nay vi key da hop le

    # Kiem tra API Key (gio da doc tu bien moi truong)
    if not Config.GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY khong duoc thiet lap hoac khong hop le.")  # <-- Print chi tiet loi
        print("Dam bao bien moi truong GEMINI_API_KEY da duoc thiet lap va key la hop le.")
        return None

    try:
        # Khoi tao Chat Model cua Gemini
        print(f"Dang khoi tao ChatGoogleGenerativeAI voi model: {Config.GEMINI_MODEL_NAME}")  # <-- Them print
        llm = ChatGoogleGenerativeAI(model=Config.GEMINI_MODEL_NAME, temperature=0.9, google_api_key=Config.GEMINI_API_KEY)
        print(f"Da khoi tao Chat Model '{Config.GEMINI_MODEL_NAME}' thanh cong.")  # <-- Them print
    # <-- SUA CACH BAT NGOAI LE -->
    except Exception as e:  # Bat ngoai le va gan vao bien e
        print(f"ERROR: Loi khi khoi tao Chat Model Gemini: {e}")  # <-- IN RA THONG TIN LOI CU THE
        print("Dam bao thu vien google-generativeai da cai dat va GEMINI_API_KEY hop le.")
        return None  # Tra ve None neu khoi tao LLM that bai

    # --- Buoc 2: Lay Retriever tu VectorStoreManager ---
    print("Dang khoi tao VectorStoreManager va tai VectorStore...")  # <-- Them print
    try:
        # Khoi tao VectorStoreManager (dam bao import dung ten lop)
        vector_store_manager = VectorStoreManager()
        # Tai VectorStore (neu chua tai). Day la noi xay ra viec load DB tu file.
        # Phuong thuc load_vector_store() trong VectorStoreManager cung nen co print chi tiet
        vectorstore = vector_store_manager.load_vector_store()

        if vectorstore is None:
            print("ERROR: VectorStoreManager().load_vector_store() tra ve None.")  # <-- Print chi tiet loi
            print("Dam bao da chay script process_document.py va thu muc data/chroma_db ton tai.")
            return None  # Tra ve None neu tai VectorStore that bai
        # retriever = vectorstore.as_retriever(search_kwargs={"k": 10})  # <-- Lay 5 chunks lien quan nhat
        retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 10, "fetch_k": 20, "lambda_mult": 0.7})
        print("Da lay Retriever tu VectorStore thanh cong.")  # <-- Them print

    except Exception as e:  # Bat ngoai le xay ra trong qua trinh load VectorStore/Retriever
        print(f"ERROR: Loi khi tai VectorStore hoac lay Retriever: {e}")  # <-- IN RA THONG TIN LOI CU THE
        return None  # Tra ve None neu tai VectorStore that bai

    # --- Buoc 3: Tao Prompt Template ---
    print("Dang tao Prompt Template...")  # <-- Them print
    try:
        # PROMPT_TEMPLATE da la mot ChatPromptTemplate instance roi
        rag_prompt = PROMPT_TEMPLATE # Gan truc tiep template da dinh nghia
        print("Da tao Prompt Template cho RAG thanh cong.")  # <-- Them print
    except Exception as e:
        print(f"ERROR: Loi khi tao Prompt Template: {e}")  # <-- IN RA THONG TIN LOI CU THE
        return None

    # --- Buoc 4: Xay dung RAG Chain su dung LangChain Expression Language (LCEL) ---
    print("Dang xay dung RAG Chain...")  # <-- Them print
    try:
        # Chain nay dam bao 'context' (tu retriever) va 'question' (input goc)
        # duoc truyen dung vao prompt template.

        # Them buoc in ra context truoc khi truyen vao prompt
        def log_and_return_context(docs: list[Document]) -> str:
            """Ham in ra noi dung cac document duoc retrieve va tra ve chuoi ghep noi."""
            print("\n--- DEBUG TEST: CAC DOCUMENTS DUOC RETRIEVE ---")
            context_text = ""
            if not docs:
                print("WARNING: Retriever tra ve danh sach documents rong.")
            else:
                for i, doc in enumerate(docs):
                    # In ra mot phan noi dung va metadata (neu co)
                    content_preview = doc.page_content[:500] + "..." if doc.page_content else "<TRONG>"
                    metadata_info = doc.metadata if doc.metadata else "Không có metadata"
                    print(f"--- Document {i+1} ---")
                    print(f"Metadata: {metadata_info}")
                    print(f"Noi dung (500 ky tu dau): {content_preview}")
                    print("---------------------")
                    context_text += doc.page_content + "\n\n" # Ghep noi dung cac document
            print("--- KET THUC DEBUG RETRIEVE ---")
            return context_text # Tra ve chuoi ghep de truyen vao prompt

        # Dieu chinh chain de bao gom buoc log_and_return_context
        rag_chain = (
            {"context": retriever | log_and_return_context, "question": RunnablePassthrough()} # Retrieve, log, va format context
            | rag_prompt # Xay dung prompt voi context va question
            | llm # Goi LLM
            | StrOutputParser() # Parse output
        )

        print("Da xay dung RAG Chain thanh cong (bao gom debug retrieval).")  # <-- Them print

    except Exception as e:
        print(f"ERROR: Loi khi xay dung RAG Chain: {e}")  # <-- IN RA THONG TIN LOI CU THE
        return None

    print("--- Tao RAG Chain hoan tat ---")  # <-- Them print o cuoi ham
    return rag_chain  # <--- Tra ve chain neu tat ca thanh cong
