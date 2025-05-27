# app/rag/document_loaders_factory.py

import os
from abc import ABC, abstractmethod

from langchain_docling import DoclingLoader


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

