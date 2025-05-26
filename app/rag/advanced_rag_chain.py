# app/rag/advanced_rag_chain.py

"""
Advanced RAG Chain với các tính năng nâng cao:
- Query expansion (mở rộng câu hỏi)
- Hybrid search (tìm kiếm kết hợp) 
- Conversation context (ngữ cảnh hội thoại)
- Response validation (xác thực phản hồi)
- Quality scoring (đánh giá chất lượng)
"""

import re
from typing import List, Dict, Any

from langchain_core.documents import Document
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import Config
from app.rag.document_processor import get_embedding_model
from app.rag.vector_storage_manager import VectorStoreManager


class AdvancedRAGChain:
    def __init__(self):
        """Khởi tạo Advanced RAG Chain với các component thông minh"""
        self.llm = None
        self.vector_store_manager = None
        self.retriever_func = None
        self.conversation_history: List[BaseMessage] = []
        self.max_history_length = 6

        # Templates cho các chức năng khác nhau
        self.query_expansion_template = self._create_query_expansion_template()
        self.main_rag_template = self._create_main_rag_template()
        self.response_validator_template = self._create_response_validator_template()

        self._initialize_components()

    def _initialize_components(self):
        """Khởi tạo các component cần thiết"""
        print("--- Khởi tạo Advanced RAG Chain ---")

        # Khởi tạo LLM
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY không được thiết lập")

        self.llm = ChatGoogleGenerativeAI(
            model=Config.GEMINI_MODEL_NAME,
            temperature=0.7,
            google_api_key=Config.GEMINI_API_KEY
        )

        # Khởi tạo Vector Store
        self.vector_store_manager = VectorStoreManager()
        vectorstore_collection = self.vector_store_manager.load_vector_store()

        if vectorstore_collection is None:
            raise ValueError("Không thể tải VectorStore Collection")

        embeddings = get_embedding_model()
        if embeddings is None:
            raise ValueError("Không thể lấy Embedding Model")

        self.retriever_func = self.vector_store_manager.get_retriever_from_collection(
            vectorstore_collection, embeddings
        )

        if self.retriever_func is None:
            raise ValueError("Không thể tạo Retriever function")

        print("--- Advanced RAG Chain đã sẵn sàng ---")

    def _create_query_expansion_template(self) -> ChatPromptTemplate:
        """Template để mở rộng câu hỏi"""
        return ChatPromptTemplate.from_messages([
            ("system", """Bạn là chuyên gia phân tích câu hỏi. Nhiệm vụ của bạn là tạo ra các từ khóa tìm kiếm hiệu quả.
            Dựa vào câu hỏi của người dùng và lịch sử hội thoại, hãy:
            1. Tạo 3-5 từ khóa chính liên quan
            2. Tạo 2-3 câu hỏi tương tự nhưng diễn đạt khác
            3. Xác định chủ đề chính
            
            Lịch sử hội thoại gần đây:
            {conversation_context}
            
            Hãy trả về kết quả theo định dạng:
            KEYWORDS: từ khóa 1, từ khóa 2, từ khóa 3
            RELATED_QUESTIONS: câu hỏi 1 | câu hỏi 2 | câu hỏi 3
            MAIN_TOPIC: chủ đề chính"""),
            ("user", "Câu hỏi: {question}")
        ])

    def _create_main_rag_template(self) -> ChatPromptTemplate:
        """Template chính cho RAG với ngữ cảnh hội thoại"""
        return ChatPromptTemplate.from_messages([
            ("system", """Bạn là trợ lý AI thông minh chuyên tư vấn về quy chế và nội quy nhà trường.

            NGUYÊN TẮC TRẢ LỜI:
            1. Phân tích câu hỏi trong ngữ cảnh hội thoại
            2. Sử dụng thông tin từ tài liệu và lịch sử trò chuyện
            3. Trả lời một cách tự nhiên, thân thiện
            4. Cung cấp thông tin chính xác và hữu ích
            5. Nếu thông tin không đầy đủ, thành thật thừa nhận
            6. Không trả lời thông tin không liên quan đến nhà trường
            
            CẤU TRÚC PHẢN HỒI:
            - Câu trả lời ngắn gọn đầu tiên
            - Thông tin chi tiết có cấu trúc
            - Ví dụ minh họa (nếu có)
            - Gợi ý bổ sung (nếu phù hợp)
            
            Lịch sử hội thoại:
            {conversation_history}
            
            Thông tin tham khảo từ tài liệu:4
            {context}"""),
            ("user", "{question}")
        ])

    def _create_response_validator_template(self) -> ChatPromptTemplate:
        """Template để xác thực chất lượng phản hồi"""
        return ChatPromptTemplate.from_messages([
            ("system", """Bạn là chuyên gia đánh giá chất lượng phản hồi AI.

            Hãy đánh giá phản hồi dựa trên các tiêu chí:
            1. ACCURACY (0-10): Tính chính xác của thông tin
            2. RELEVANCE (0-10): Mức độ liên quan đến câu hỏi  
            3. COMPLETENESS (0-10): Tính đầy đủ của câu trả lời
            4. CLARITY (0-10): Tính rõ ràng, dễ hiểu
            5. HELPFULNESS (0-10): Tính hữu ích cho người dùng
            
            Trả về định dạng:
            SCORE: accuracy/relevance/completeness/clarity/helpfulness
            TOTAL: tổng điểm/50
            FEEDBACK: nhận xét ngắn gọn
            IMPROVED: có nên cải thiện không (YES/NO)"""),
            ("user", """Câu hỏi: {question}
            Phản hồi được đánh giá: {response}
            Ngữ cảnh tài liệu: {context}""")
        ])

    def _expand_query(self, question: str) -> Dict[str, str]:
        """Mở rộng câu hỏi để tìm kiếm hiệu quả hơn"""
        try:
            conversation_context = self._format_conversation_history()

            expansion_chain = self.query_expansion_template | self.llm | StrOutputParser()

            expansion_result = expansion_chain.invoke({
                "question": question,
                "conversation_context": conversation_context
            })

            # Parse kết quả
            keywords = ""
            related_questions = ""
            main_topic = ""

            for line in expansion_result.split('\n'):
                if line.startswith('KEYWORDS:'):
                    keywords = line.replace('KEYWORDS:', '').strip()
                elif line.startswith('RELATED_QUESTIONS:'):
                    related_questions = line.replace('RELATED_QUESTIONS:', '').strip()
                elif line.startswith('MAIN_TOPIC:'):
                    main_topic = line.replace('MAIN_TOPIC:', '').strip()

            return {
                "keywords": keywords,
                "related_questions": related_questions,
                "main_topic": main_topic,
                "original_question": question
            }

        except Exception as e:
            print(f"ERROR trong query expansion: {e}")
            return {
                "keywords": question,
                "related_questions": question,
                "main_topic": "general",
                "original_question": question
            }

    def _hybrid_search(self, query_info: Dict[str, str], top_k: int = 8) -> List[Document]:
        """Tìm kiếm kết hợp với nhiều chiến lược"""
        all_docs = []

        try:
            # Tìm kiếm với câu hỏi gốc
            original_docs = self.retriever_func(query_info["original_question"])
            all_docs.extend(original_docs[:3])

            # Tìm kiếm với từ khóa
            if query_info["keywords"]:
                keyword_docs = self.retriever_func(query_info["keywords"])
                all_docs.extend(keyword_docs[:3])

            # Tìm kiếm với câu hỏi liên quan
            if query_info["related_questions"]:
                for related_q in query_info["related_questions"].split("|")[:2]:
                    related_docs = self.retriever_func(related_q.strip())
                    all_docs.extend(related_docs[:2])

            # Loại bỏ trùng lặp và giới hạn số lượng
            unique_docs = []
            seen_content = set()

            for doc in all_docs:
                content_hash = hash(doc.page_content[:200])  # Hash 200 ký tự đầu
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    unique_docs.append(doc)

                if len(unique_docs) >= top_k:
                    break

            return unique_docs

        except Exception as e:
            print(f"ERROR trong hybrid search: {e}")
            # Fallback về tìm kiếm đơn giản
            return self.retriever_func(query_info["original_question"])

    def _format_conversation_history(self) -> str:
        """Format lịch sử hội thoại"""
        if not self.conversation_history:
            return "Chưa có lịch sử hội thoại."

        formatted = []
        for i, message in enumerate(self.conversation_history[-6:]):  # Lấy 6 tin nhắn gần nhất
            if isinstance(message, HumanMessage):
                formatted.append(f"Người dùng: {message.content}")
            elif isinstance(message, AIMessage):
                formatted.append(f"AI: {message.content[:150]}...")  # Rút gọn phản hồi AI

        return "\n".join(formatted)

    def _validate_response(self, question: str, response: str, context: str) -> Dict[str, Any]:
        """Xác thực chất lượng phản hồi"""
        try:
            validation_chain = self.response_validator_template | self.llm | StrOutputParser()

            validation_result = validation_chain.invoke({
                "question": question,
                "response": response,
                "context": context[:1000]  # Giới hạn context
            })

            # Parse kết quả validation
            scores = {}
            total_score = 0
            feedback = ""
            should_improve = False

            for line in validation_result.split('\n'):
                if line.startswith('SCORE:'):
                    score_parts = line.replace('SCORE:', '').strip().split('/')
                    if len(score_parts) >= 5:
                        scores = {
                            'accuracy': int(score_parts[0]) if score_parts[0].isdigit() else 7,
                            'relevance': int(score_parts[1]) if score_parts[1].isdigit() else 7,
                            'completeness': int(score_parts[2]) if score_parts[2].isdigit() else 7,
                            'clarity': int(score_parts[3]) if score_parts[3].isdigit() else 7,
                            'helpfulness': int(score_parts[4]) if score_parts[4].isdigit() else 7
                        }
                elif line.startswith('TOTAL:'):
                    total_match = re.search(r'(\d+)', line)
                    total_score = int(total_match.group(1)) if total_match else 35
                elif line.startswith('FEEDBACK:'):
                    feedback = line.replace('FEEDBACK:', '').strip()
                elif line.startswith('IMPROVED:'):
                    should_improve = 'YES' in line.upper()

            return {
                'scores': scores,
                'total_score': total_score,
                'feedback': feedback,
                'should_improve': should_improve,
                'quality_level': self._get_quality_level(total_score)
            }

        except Exception as e:
            print(f"ERROR trong response validation: {e}")
            return {
                'scores': {'accuracy': 7, 'relevance': 7, 'completeness': 7, 'clarity': 7, 'helpfulness': 7},
                'total_score': 35,
                'feedback': "Không thể đánh giá chất lượng",
                'should_improve': False,
                'quality_level': 'good'
            }

    def _get_quality_level(self, total_score: int) -> str:
        """Xác định mức chất lượng dựa trên điểm số"""
        if total_score >= 40:
            return 'excellent'
        elif total_score >= 35:
            return 'good'
        elif total_score >= 25:
            return 'fair'
        else:
            return 'poor'

    def _format_docs(self, docs: List[Document]) -> str:
        """Format documents thành context"""
        if not docs:
            return "Không tìm thấy thông tin liên quan."

        context_parts = []
        for i, doc in enumerate(docs, 1):
            # Lấy thông tin metadata nếu có
            source = doc.metadata.get('source', f'Tài liệu {i}')
            page = doc.metadata.get('page', '')
            page_info = f" (trang {page})" if page else ""

            context_parts.append(f"--- Nguồn {i}: {source}{page_info} ---\n{doc.page_content}\n")

        return "\n".join(context_parts)

    def add_to_conversation_history(self, message: BaseMessage):
        """Thêm tin nhắn vào lịch sử hội thoại"""
        self.conversation_history.append(message)

        # Giới hạn độ dài lịch sử
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]

    def invoke(self, question: str) -> str:
        """Xử lý câu hỏi với Advanced RAG Pipeline"""
        print(f"\n--- ADVANCED RAG PROCESSING: '{question}' ---")

        try:
            # Bước 1: Mở rộng câu hỏi
            print("Bước 1: Mở rộng câu hỏi...")
            query_info = self._expand_query(question)
            print(f"Keywords: {query_info['keywords']}")
            print(f"Main topic: {query_info['main_topic']}")

            # Bước 2: Tìm kiếm kết hợp
            print("Bước 2: Tìm kiếm tài liệu...")
            docs = self._hybrid_search(query_info)
            print(f"Tìm thấy {len(docs)} tài liệu liên quan")

            # Bước 3: Tạo phản hồi chính
            print("Bước 3: Tạo phản hồi...")
            context = self._format_docs(docs)
            conversation_history = self._format_conversation_history()

            main_chain = self.main_rag_template | self.llm | StrOutputParser()

            response = main_chain.invoke({
                "question": question,
                "context": context,
                "conversation_history": conversation_history
            })

            # Bước 4: Xác thực chất lượng phản hồi
            print("Bước 4: Xác thực chất lượng...")
            validation = self._validate_response(question, response, context)
            print(f"Quality level: {validation['quality_level']} (Score: {validation['total_score']}/50)")

            # Bước 5: Cập nhật lịch sử hội thoại
            self.add_to_conversation_history(HumanMessage(content=question))
            self.add_to_conversation_history(AIMessage(content=response))

            # Thêm thông tin debug nếu cần
            if validation['quality_level'] == 'poor':
                print(f"WARNING: Low quality response - {validation['feedback']}")

            print("--- ADVANCED RAG PROCESSING COMPLETED ---\n")
            return response

        except Exception as e:
            print(f"ERROR trong Advanced RAG processing: {e}")
            # Fallback về basic response
            return f"Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi của bạn. Vui lòng thử lại hoặc diễn đạt câu hỏi khác. Lỗi: {str(e)}"


    # Factory function để tạo Advanced RAG Chain
def get_advanced_rag_chain() -> AdvancedRAGChain:
    """Tạo và trả về Advanced RAG Chain instance"""
    try:
        return AdvancedRAGChain()
    except Exception as e:
        print(f"ERROR: Không thể tạo Advanced RAG Chain: {e}")
        return None
