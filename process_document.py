# app/process_document.py

import os
# Import ham pipeline chinh tu app.rag.document_processor
from app.rag.document_processor import process_document_pipeline

# Import Config de lay duong dan file va ten model (neu can kiem tra dieu kien tien quyet o day)
# Tu app.core.config import Config # Khong can import Config o day neu logic kiem tra da nam trong pipeline

# Ham main de chay script
if __name__ == "__main__":
    print("--- Dang chay script process_document.py ---") # <-- Them print
    # Goi ham pipeline chinh tu app/rag/document_processor.py
    # Toan bo logic xu ly (load, ocr, split, embed, store) nam trong ham nay
    process_document_pipeline()
    print("--- Script process_document.py hoan tat ---") # <-- Them print
