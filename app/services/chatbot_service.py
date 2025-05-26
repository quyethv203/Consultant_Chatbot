# app/services/chatbot_service.py

from app.rag.rag_chain import get_rag_chain # Import ham get_rag_chain
from app.rag.advanced_rag_chain import get_advanced_rag_chain # Import advanced RAG chain

class ChatbotService:
    _rag_chain_instance = None # Bien lop de luu tru instance RAG Chain (Singleton)
    _advanced_rag_instance = None # Advanced RAG Chain instance
    _use_advanced_rag = True # Flag để chọn sử dụng Advanced RAG

    def __init__(self):
        print("Khoi tao instance ChatbotService...")
        # RAG Chain se duoc khoi tao lan dau khi get_rag_chain_instance duoc goi

    def get_rag_chain_instance(self):
        """
        Tra ve instance RAG Chain. Sử dụng Advanced RAG nếu có thể.
        """
        if self._use_advanced_rag:
            # Thử sử dụng Advanced RAG Chain trước
            if ChatbotService._advanced_rag_instance is None:
                print("Dang thu khoi tao Advanced RAG Chain...")
                ChatbotService._advanced_rag_instance = get_advanced_rag_chain()
                
            if ChatbotService._advanced_rag_instance:
                print("Sử dụng Advanced RAG Chain.")
                return ChatbotService._advanced_rag_instance
            else:
                print("WARNING: Advanced RAG Chain không khả dụng, fallback về Basic RAG.")
                # Fallback về basic RAG nếu advanced không hoạt động
                self._use_advanced_rag = False
        
        # Sử dụng Basic RAG Chain
        if ChatbotService._rag_chain_instance is None:
            print("Dang thu khoi tao Basic RAG Chain...")
            ChatbotService._rag_chain_instance = get_rag_chain()
            if ChatbotService._rag_chain_instance:
                print("Basic RAG Chain da san sanh.")
            else:
                print("ERROR: get_rag_chain() tra ve None. RAG Chain khong the khoi tao.")
                
        return ChatbotService._rag_chain_instance

    def get_chatbot_info(self):
        """Lấy thông tin về loại chatbot đang sử dụng"""
        if self._use_advanced_rag and ChatbotService._advanced_rag_instance:
            return {
                "type": "Advanced RAG",
                "features": [
                    "Query Expansion", 
                    "Hybrid Search", 
                    "Conversation Context",
                    "Response Validation",
                    "Quality Scoring"
                ],
                "description": "Chatbot thông minh với các tính năng nâng cao"
            }
        else:
            return {
                "type": "Basic RAG", 
                "features": ["Document Retrieval", "Basic Response Generation"],
                "description": "Chatbot cơ bản với tính năng truy xuất tài liệu"
            }

    def reset_conversation_history(self):
        """Reset lịch sử hội thoại của Advanced RAG"""
        if ChatbotService._advanced_rag_instance:
            ChatbotService._advanced_rag_instance.conversation_history = []
            print("Đã reset lịch sử hội thoại.")
    
    def reset_conversation(self):
        """Reset conversation and clear memory"""
        try:
            self.reset_conversation_history()
            
            # If using advanced RAG, also reset any additional state
            if self._use_advanced_rag and ChatbotService._advanced_rag_instance:
                # Clear any cached queries or context
                if hasattr(ChatbotService._advanced_rag_instance, 'clear_cache'):
                    ChatbotService._advanced_rag_instance.clear_cache()
                    
            print("Cuộc trò chuyện đã được reset hoàn toàn.")
            return True
        except Exception as e:
            print(f"ERROR: Lỗi khi reset cuộc trò chuyện: {e}")
            return False


