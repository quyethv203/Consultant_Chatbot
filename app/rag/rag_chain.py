# app/rag/rag_chain.py

# Import cac component cua LangChain
from langchain_core.runnables import RunnablePassthrough, RunnableLambda  # Them RunnableLambda
from langchain_core.output_parsers import StrOutputParser  # De chuyen output tu LLM thanh chuoi don gian
# Import ChatGoogleGenerativeAI de su dung model chat cua Gemini
from langchain_google_genai import ChatGoogleGenerativeAI  # Wrapper cua LangChain cho Gemini Chat
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document  # Import Document de lam viec voi ket qua retrieve

# Import cac component RAG da xay dung
# <-- DAM BAO IMPORT DUNG VectorStoreManager -->
from app.rag.vector_storage_manager import VectorStoreManager  # De tai VectorStore va tao retriever

# Import ham get_embedding_model tu document_processor
from app.rag.document_processor import get_embedding_model

# Import cau hinh
from app.core.config import Config

PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    # System message: Dat vai tro cho mo hinh va huong dan cach tra loi
    ("system", """Bạn là một trợ lý AI hữu ích, chuyên trả lời các câu hỏi dựa trên nội dung từ các đoạn văn bản ngữ cảnh được cung cấp.
    NGUYÊN TẮC TRẢ LỜI:
    1. Phân tích kỹ câu hỏi của người dùng để hiểu ý định thực sự
    2. Tổng hợp thông tin từ nhiều nguồn để đưa ra câu trả lời toàn diện
    3. Cấu trúc câu trả lời rõ ràng, logic
    4. Đưa ra ví dụ cụ thể khi cần thiết
    5. Thừa nhận khi không có đủ thông tin
    HƯỚNG DẪN TRẢ LỜI:
    - Nếu thông tin liên quan trực tiếp: Trả lời chi tiết với cấu trúc:
        * Tóm tắt ngắn gọn
        * Thông tin chi tiết
        * Ví dụ/minh họa (nếu có)
        * Lời khuyên/gợi ý (nếu phù hợp)
    - Nếu thông tin liên quan gián tiếp: Trả lời những gì biết và gợi ý hướng tìm hiểu thêm
    - Nếu không có thông tin: Thừa nhận và đề xuất liên hệ phòng ban phù hợp


    Ngu canh:
    {context}"""),  # Placeholder cho ngu canh (các đoạn văn bản từ Vector DB)

    # User message: Chua cau hoi goc cua nguoi dung
    ("user", "{question}"),  # Placeholder cho cau hoi cua nguoi dung
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
        llm = ChatGoogleGenerativeAI(model=Config.GEMINI_MODEL_NAME, temperature=0.7,
                                     google_api_key=Config.GEMINI_API_KEY)
        print(f"Da khoi tao Chat Model '{Config.GEMINI_MODEL_NAME}' thanh cong.")  # <-- Them print
    # <-- SUA CACH BAT NGOAI LE -->
    except Exception as e:  # Bat ngoai le va gan vao bien e
        print(f"ERROR: Loi khi khoi tao Chat Model Gemini: {e}")  # <-- IN RA THONG TIN LOI CU THE
        print("Dam bao thu vien google-generativeai da cai dat va GEMINI_API_KEY hop le.")
        return None  # Tra ve None neu khoi tao LLM that bai

    # --- Buoc 2: Lay VectorStore Collection va tao Retriever ---
    print("Dang khoi tao VectorStoreManager va tai VectorStore Collection...")  # <-- Them print
    try:
        # Khoi tao VectorStoreManager (dam bao import dung ten lop)
        vector_store_manager = VectorStoreManager()
        # Tai VectorStore Collection (neu chua tai). Day la noi xay ra viec load DB tu file.
        vectorstore_collection = vector_store_manager.load_vector_store()

        if vectorstore_collection is None:
            print("ERROR: VectorStoreManager().load_vector_store() tra ve None.")  # <-- Print chi tiet loi
            print("Dam bao da chay script process_document.py va thu muc data/chroma_db ton tai.")
            return None  # Tra ve None neu tai VectorStore that bai

        # Lay Embedding Model (can thiet cho ham retriever thu cong)
        embeddings = get_embedding_model()
        if embeddings is None:
            print("ERROR: Khong the lay Embedding Model cho Retriever.")
            return None

        # Lay Retriever function tu VectorStoreManager
        # Ham retriever nay se thuc hien tim kiem trong Chroma Collection
        retriever_func = vector_store_manager.get_retriever_from_collection(vectorstore_collection, embeddings)

        if retriever_func is None:
            print("ERROR: Khong thể tạo Retriever function.")
            return None

        print("Da lay Retriever tu VectorStore Collection thanh cong.")

    except Exception as e:  # Bat ngoai le xay ra trong qua trinh load VectorStore/Retriever
        print(f"ERROR: Loi khi tai VectorStore hoac lay Retriever: {e}")  # <-- IN RA THONG TIN LOI CU THE
        return None  # Tra ve None neu tai VectorStore that bai

    # --- Buoc 3: Tao Prompt Template ---
    print("Dang tao Prompt Template...")  # <-- Them print
    try:
        # PROMPT_TEMPLATE da la mot ChatPromptTemplate instance roi
        rag_prompt = PROMPT_TEMPLATE  # Gan truc tiep template da dinh nghia
        print("Da tao Prompt Template cho RAG thanh cong.")  # <-- Them print
    except Exception as e:
        print(f"ERROR: Loi khi tao Prompt Template: {e}")  # <-- IN RA THONG TIN LOI CU THE
        return None

    # --- Buoc 4: Xay dung RAG Chain su dung LangChain Expression Language (LCEL) ---
    print("Dang xay dung RAG Chain...")  # <-- Them print
    try:
        # Ham format document de dua vao prompt
        def format_docs(docs: list[Document]) -> str:
            """Ghep noi dung cac document thanh mot chuoi duy nhat."""
            print("\n--- DEBUG TEST: CAC DOCUMENTS DUOC FORMAT CHO PROMPT ---")
            context_text = ""
            if not docs:
                print("WARNING: Danh sach documents de format rong.")
            else:
                for i, doc in enumerate(docs):
                    # In ra mot phan noi dung va metadata (neu co)
                    content_preview = doc.page_content[:500] + "..." if doc.page_content else "<TRONG>"
                    metadata_info = doc.metadata if doc.metadata else "Không có metadata"
                    print(f"--- Document {i + 1} (Formatted) ---")
                    print(f"Metadata: {metadata_info}")
                    print(f"Noi dung (500 ky tu dau): {content_preview}")
                    print("---------------------")
                    context_text += doc.page_content + "\n\n"  # Ghep noi dung cac document
            print("--- KET THUC DEBUG FORMAT ---")
            return context_text  # Tra ve chuoi ghep de truyen vao prompt

        # Dieu chinh chain de su dung ham retriever_func thu cong va ham format_docs
        rag_chain = (
                {
                    "context": RunnableLambda(lambda x: retriever_func(x["question"])) | format_docs,
                    "question": RunnablePassthrough()
                }
                | rag_prompt  # Xay dung prompt voi context va question
                | llm  # Goi LLM
                | StrOutputParser()  # Parse output
        )

        print("Da xay dung RAG Chain thanh cong (su dung retriever thu cong).")

    except Exception as e:
        print(f"ERROR: Loi khi xay dung RAG Chain: {e}")  # <-- IN RA THONG TIN LOI CU THE
        return None

    print("--- Tao RAG Chain hoan tat ---")
    return rag_chain  # <--- Tra ve chain neu tat ca thanh cong
