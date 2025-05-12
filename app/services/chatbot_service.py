# app/services/chatbot_service.py
import logging
# logging khong dung nua, su dung print
# logger = logging.getLogger(__name__) # Co the xoa neu khong dung logger

# Import ham lay RAG Chain tu package rag
from app.rag.rag_chain import get_rag_chain

# Import Config de doc thong tin chung (nhu GEMINI_API_KEY de check)
from app.core.config import Config


class ChatbotService:
    """
    Service nay dieu phoi viec lay phan hoi cho chatbot.
    No se su dung RAG chain de tra loi cac cau hoi dua tren tai lieu.
    RAG Chain duoc khoi tao mot cach luoi bieng (lazy-initialized).
    """
    # Khong can Singleton pattern don gian nhu truoc nua voi Flask va manual DI tren controller
    # Flask se tao instance ChatbotService khi can (qua ChatService instance tren moi request)
    # Nhung viec khoi tao RAG Chain ben trong moi la critical


    def __init__(self):
        """
        Khoi tao ChatbotService. RAG Chain chua duoc tao o buoc nay.
        """
        print("Khoi tao instance ChatbotService...")
        self._rag_chain = None # Bien noi bo de luu instance RAG Chain
        self._rag_chain_initialized = False # Flag de danh dau da tung thu khoi tao chua

    def _initialize_rag_chain(self):
        """
        Khoi tao RAG Chain neu chua duoc khoi tao truoc do.
        """
        # Chi thuc hien logic khoi tao neu chua tung thu truoc do
        if not self._rag_chain_initialized:
            print("Dang thu khoi tao RAG Chain lan dau...")
            try:
                # Goi ham lay RAG Chain tu file rag_chain.py
                print("--> Goi get_rag_chain()...")
                self._rag_chain = get_rag_chain()
                print("<-- Ket thuc get_rag_chain().")

                if self._rag_chain:
                    print("RAG Chain da san sang.")
                else:
                    # get_rag_chain da in ERROR chi tiet neu that bai
                    print("ERROR: get_rag_chain() tra ve None. RAG Chain khong the khoi tao.")
                    self._rag_chain = None # Dam bao la None

            except Exception as e:
                # Bat ngoai le xay ra trong qua trinh get_rag_chain()
                print(f"ERROR: Ngoai le xay ra khi khoi tao RAG Chain: {e}")
                self._rag_chain = None # Dam bao la None
            finally:
                # Danh dau rang da tung thu khoi tao, du thanh cong hay that bai
                self._rag_chain_initialized = True


    # Sua phuong thuc de nhan user_input va goi RAG Chain
    def get_chatbot_response(self, user_input: str) -> str:
        """
        Lay phan hoi tu chatbot su dung RAG chain.
        """
        print(f"ChatbotService nhan input: '{user_input}'")

        if not user_input:
            return "Tôi có thể giúp gì cho bạn?" # Phản hồi cho input rỗng

        # --- Kiem tra va khoi tao RAG Chain mot cach luoi bieng ---
        # Neu chua tung thu khoi tao truoc do, thi thu ngay bay gio
        if not self._rag_chain_initialized:
            print("--> Dang thuc hien _initialize_rag_chain() lan dau khi nhan tin nhan...")
            self._initialize_rag_chain() # Thuc hien khoi tao
            print("<-- Ket thuc _initialize_rag_chain().")


        # Kiem tra xem RAG Chain da khoi tao thanh cong chua sau khi thu
        if self._rag_chain is None:
             print("ERROR: RAG Chain chua san sang (khoi tao that bai). Tra ve phan hoi loi.")
             # Tra ve thong bao loi tu ChatbotService de Service goi luu vao DB
             return "Xin lỗi, hệ thống chatbot đang gặp sự cố hoặc chưa sẵn sàng. Vui lòng thử lại sau."

        # --- Goi RAG Chain de lay phan hoi ---
        try:
            print(f"Dang goi RAG Chain voi input: '{user_input}'")
            # self._rag_chain.invoke() thuc thi toan bo quy trinh RAG
            bot_response_text = self._rag_chain.invoke(user_input)
            print(f"Nhan phan hoi tu RAG Chain: '{bot_response_text}'")

            if not bot_response_text or bot_response_text.strip() == "":
                 # Truong hop LLM tra ve chuoi rong hoac chi co khoang trang
                 # Co the do prompt feedback (bi chan) hoac LLM khong biet tra loi tu context
                 print("Nhan phan hoi rong hoac chi co khoang trang tu RAG Chain. Tra ve thong bao khong tim thay thong tin.")
                 # Tra ve thong bao khong tim thay thong tin de Service luu vao DB
                 return "Tôi không tìm thấy thông tin liên quan trong tài liệu để trả lời câu hỏi này."

            return bot_response_text.strip() # Loai bo khoang trang dau/cuoi

        except Exception as e:
            # Bat cac ngoai le xay ra trong qua trinh invoke RAG Chain
            print(f"ERROR: Loi khi goi RAG Chain.invoke(): {e}")
            # Tra ve thong bao loi chung de Service luu vao DB
            return "Xin lỗi, đã xảy ra lỗi khi xử lý tin nhắn của bạn."


# Ham helper de lay VectorStore da tao (dung trong VectorStoreManager) KHONG NAM O DAY