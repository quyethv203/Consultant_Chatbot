from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from app.rag.vector_storage_manager import VectorStoreManager

from app.rag.document_processor import get_embedding_model

from app.core.config import Config

PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([

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
    {context}"""),

    ("user", "{question}"),
])


def get_rag_chain():
    """
    Tao va cau hinh chuoi RAG (LangChain chain).
    Chuoi nay se thuc hien: nhan cau hoi -> truy xuat context -> xay prompt -> goi LLM -> tra ve phan hoi.
    """
    print("--- DEBUG TEST: DA VAO HAM GET_RAG_CHAIN ---")
    print("\n--- Dang tao RAG Chain ---")

    print("Dang kiem tra GEMINI_API_KEY va khoi tao LLM...")

    if not Config.GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY khong duoc thiet lap hoac khong hop le.")
        print("Dam bao bien moi truong GEMINI_API_KEY da duoc thiet lap va key la hop le.")
        return None

    try:

        print(f"Dang khoi tao ChatGoogleGenerativeAI voi model: {Config.GEMINI_MODEL_NAME}")
        llm = ChatGoogleGenerativeAI(model=Config.GEMINI_MODEL_NAME, temperature=0.7,
                                     google_api_key=Config.GEMINI_API_KEY)
        print(f"Da khoi tao Chat Model '{Config.GEMINI_MODEL_NAME}' thanh cong.")

    except Exception as e:
        print(f"ERROR: Loi khi khoi tao Chat Model Gemini: {e}")
        print("Dam bao thu vien google-generativeai da cai dat va GEMINI_API_KEY hop le.")
        return None

    print("Dang khoi tao VectorStoreManager va tai VectorStore Collection...")
    try:

        vector_store_manager = VectorStoreManager()

        vectorstore_collection = vector_store_manager.load_vector_store()

        if vectorstore_collection is None:
            print("ERROR: VectorStoreManager().load_vector_store() tra ve None.")
            print("Dam bao da chay script process_document.py va thu muc data/chroma_db ton tai.")
            return None

        embeddings = get_embedding_model()
        if embeddings is None:
            print("ERROR: Khong the lay Embedding Model cho Retriever.")
            return None

        retriever_func = vector_store_manager.get_retriever_from_collection(vectorstore_collection, embeddings)

        if retriever_func is None:
            print("ERROR: Khong thể tạo Retriever function.")
            return None

        print("Da lay Retriever tu VectorStore Collection thanh cong.")

    except Exception as e:
        print(f"ERROR: Loi khi tai VectorStore hoac lay Retriever: {e}")
        return None

    print("Dang tao Prompt Template...")
    try:

        rag_prompt = PROMPT_TEMPLATE
        print("Da tao Prompt Template cho RAG thanh cong.")
    except Exception as e:
        print(f"ERROR: Loi khi tao Prompt Template: {e}")
        return None

    print("Dang xay dung RAG Chain...")
    try:

        def format_docs(docs: list[Document]) -> str:
            """Ghep noi dung cac document thanh mot chuoi duy nhat."""
            print("\n--- DEBUG TEST: CAC DOCUMENTS DUOC FORMAT CHO PROMPT ---")
            context_text = ""
            if not docs:
                print("WARNING: Danh sach documents de format rong.")
            else:
                for i, doc in enumerate(docs):
                    content_preview = doc.page_content[:500] + "..." if doc.page_content else "<TRONG>"
                    metadata_info = doc.metadata if doc.metadata else "Không có metadata"
                    print(f"--- Document {i + 1} (Formatted) ---")
                    print(f"Metadata: {metadata_info}")
                    print(f"Noi dung (500 ky tu dau): {content_preview}")
                    print("---------------------")
                    context_text += doc.page_content + "\n\n"
            print("--- KET THUC DEBUG FORMAT ---")
            return context_text

        rag_chain = (
                {
                    "context": RunnableLambda(lambda x: retriever_func(x["question"])) | format_docs,
                    "question": RunnablePassthrough()
                }
                | rag_prompt
                | llm
                | StrOutputParser()
        )

        print("Da xay dung RAG Chain thanh cong (su dung retriever thu cong).")

    except Exception as e:
        print(f"ERROR: Loi khi xay dung RAG Chain: {e}")
        return None

    print("--- Tao RAG Chain hoan tat ---")
    return rag_chain
