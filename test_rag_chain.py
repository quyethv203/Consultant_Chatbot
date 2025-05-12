# test_rag_chain.py

import os
import sys

# Them thu muc goc cua du an vao sys.path de import cac module khac
# Dam bao ban chay script nay tu thu muc goc cua du an
# Vi du: D:\TKKTPM\Chatbot-Web> python test_rag_chain.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import ham get_rag_chain tu module rag_chain
# Dam bao duong dan import nay dung voi vi tri file rag_chain.py cua ban
# Vi du: neu file rag_chain.py nam trong app/rag, thi import nhu sau:
from app.rag.rag_chain import get_rag_chain

# Import Config de doc cau hinh (neu can kiem tra API key truoc khi goi get_rag_chain)
from app.core.config import Config

def test_chain():
    """
    Tao RAG chain va gui mot cau hoi test.
    """
    print("--- Bat dau test RAG Chain ---")

    # Kiem tra API Key truoc khi tao chain
    if not hasattr(Config, 'GEMINI_API_KEY') or not Config.GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY chua duoc thiet lap trong Config.")
        print("Vui long thiet lap bien moi truong GEMINI_API_KEY hoac cap nhat file config.py.")
        return

    # Goi ham de lay RAG chain
    rag_chain = get_rag_chain()

    if rag_chain is None:
        print("ERROR: Khong the tao RAG Chain. Vui long kiem tra cac thong bao loi ben tren.")
        print("--- Ket thuc test RAG Chain do loi ---")
        return

    # Cau hoi test lien quan den noi dung tai lieu
    # Thay the cau hoi nay bang mot cau hoi khac neu can
    test_question = ["Quy chế này quy định về phạm vi điều chỉnh và đối tượng áp dụng như thế nào?", "Thời gian học tập tối đa đối với sinh viên là bao lâu?"] # Vi du cau hoi ve Dieu 1
    for i in test_question:
        print(f"\nDang gui cau hoi test toi RAG Chain: '{i}'")

        try:
            # Goi chain voi cau hoi test
            response = rag_chain.invoke(i)

            print("\n--- Phan hoi tu RAG Chain ---")
            print(response)
            print("--- Ket thuc test RAG Chain ---")

        except Exception as e:
            print(f"ERROR: Loi khi goi RAG Chain: {e}")
            print("--- Ket thuc test RAG Chain do loi ---")


# Chay ham test khi script duoc thuc thi truc tiep
if __name__ == "__main__":
    test_chain()
