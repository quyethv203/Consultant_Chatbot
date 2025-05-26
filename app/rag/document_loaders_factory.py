# app/rag/document_loaders_factory.py

from abc import ABC, abstractmethod
import os

from langchain_docling import DoclingLoader
from langchain_core.documents import Document

# Không cần import các lớp cấu hình OCR của docling ở đây nữa
# from docling.document_converter import DocumentConverter, PdfFormatOption
# from docling.datamodel.base_models import InputFormat
# from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions


class DocumentLoaderFactory(ABC):
    """
    Abstract Factory de tao ra cac bo tai tai lieu.
    """

    @abstractmethod
    def create_loader(self, file_path: str):
        """
        Phuong thuc truu tuong de tao mot bo tai tai lieu cu the.
        """
        pass


class DoclingLoaderFactory(DocumentLoaderFactory):
    """
    Concrete Factory su dung DoclingLoader cua LangChain de tai va tien xu ly cac loai file.
    """

    def create_loader(self, file_path: str):
        print(f"--- DoclingLoaderFactory: Tao bo tai su dung DoclingLoader cua LangChain cho file: {file_path} ---")
        return DoclingLoader(file_path=file_path)


def get_document_loader_factory(file_path: str) -> DocumentLoaderFactory:
    """
    Chon va tra ve mot DocumentLoaderFactory.
    Voi docling, chung ta chi can mot factory.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File khong ton tai: {file_path}")

    return DoclingLoaderFactory()

