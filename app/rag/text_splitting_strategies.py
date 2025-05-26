# app/rag/text_splitting_strategies.py

from abc import ABC, abstractmethod
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class TextSplitterStrategy(ABC):
    """
    Abstract Strategy cho cac phuong phap chia van ban.
    """
    @abstractmethod
    def split_text(self, text: str, chunk_size: int, chunk_overlap: int) -> list[Document]:
        """
        Phuong thuc truu tuong de chia van ban thanh cac Document.
        """
        pass

class StructuredTextSplitterStrategy(TextSplitterStrategy):
    """
    Chiến lược chia văn bản có cấu trúc, ưu tiên giữ các phần như Chương, Điều.
    """
    def split_text(self, text: str, chunk_size: int, chunk_overlap: int) -> list[Document]:
        print(f"--- StructuredTextSplitterStrategy: Dang chia van ban voi kich thuoc {chunk_size} va overlap {chunk_overlap} (co cau truc) ---")
        structure_and_simple_separators = [
            r'\nChương\s+[IVXLCDM\d]+\s*[\.:]', # Nhan dien "Chuong I", "Chuong II", "Chuong 1", ...
            r'\nĐiều\s+\d+\s*[\.]?',          # Nhan dien "Dieu 1.", "Dieu 2", ...
            "\n\n",                           # Chia theo doan rong
            "\n",                             # Chia theo dong moi
            " ",                              # Chia theo khoang trang
            "",                               # Chia theo ky tu (khi khong con cach nao khac)
        ]
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=structure_and_simple_separators,
            length_function=len,
            is_separator_regex=True
        )
        string_chunks = text_splitter.split_text(text)
        return [Document(page_content=chunk) for chunk in string_chunks]

class UnstructuredTextSplitterStrategy(TextSplitterStrategy):
    """
    Chiến lược chia văn bản không có cấu trúc, sử dụng các dấu phân cách đơn giản.
    """
    def split_text(self, text: str, chunk_size: int, chunk_overlap: int) -> list[Document]:
        print(f"--- UnstructuredTextSplitterStrategy: Dang chia van ban voi kich thuoc {chunk_size} va overlap {chunk_overlap} (khong co cau truc) ---")
        simple_separators = ["\n\n", "\n", " ", ""]
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=simple_separators,
            length_function=len,
            is_separator_regex=False # Khong su dung regex cho simple separators
        )
        string_chunks = text_splitter.split_text(text)
        return [Document(page_content=chunk) for chunk in string_chunks]

class TextSplitterContext:
    """
    Context su dung TextSplitterStrategy de thuc hien viec chia van ban.
    """
    def __init__(self, strategy: TextSplitterStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: TextSplitterStrategy):
        self._strategy = strategy

    def split_document_text(self, text: str, chunk_size: int, chunk_overlap: int) -> list[Document]:
        """
        Thuc hien chia van ban su dung chien luoc da chon.
        """
        return self._strategy.split_text(text, chunk_size, chunk_overlap)

