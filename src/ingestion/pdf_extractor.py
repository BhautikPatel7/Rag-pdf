"""
src/ingestion/pdf_extractor.py
Main orchestrator: opens a PDF and runs all extractors on each page.
Returns a flat list of LangChain Documents ready for embedding.
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config.settings import get_settings
from src.ingestion.text_extractor  import extract_text
from src.ingestion.table_extractor import extract_tables
from src.ingestion.image_extractor import extract_images
from src.ingestion.math_extractor  import extract_math
from src.providers.llm_provider    import get_vision_llm


@dataclass
class ExtractionSummary:
    total_pages: int = 0
    text_chunks:  int = 0
    table_chunks: int = 0
    image_chunks: int = 0
    math_chunks:  int = 0
    emoji_chunks: int = 0   # emojis are preserved inside text chunks

    @property
    def total_chunks(self) -> int:
        return self.text_chunks + self.table_chunks + self.image_chunks + self.math_chunks


def extract_pdf(pdf_path: str) -> tuple[List[Document], ExtractionSummary]:
    """
    Extract all content types from a PDF file.

    Strategy per page:
    1. Text          → text_extractor
    2. Tables        → table_extractor
    3. Images/Charts → image_extractor (via vision LLM)
    4. Math          → math_extractor  (via vision LLM for equations)

    Emojis and special characters are preserved inside text chunks.

    Returns:
        (documents, summary) where documents is a flat list of chunked Documents.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    settings  = get_settings()
    vision_llm = get_vision_llm()
    summary    = ExtractionSummary()

    # Text splitter for chunking long text/table content
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    all_docs: List[Document] = []

    # Open with pdfplumber for text + tables
    import pdfplumber
    import fitz  # PyMuPDF for images + math page rendering

    fitz_doc = fitz.open(pdf_path)
    source   = os.path.basename(pdf_path)

    with pdfplumber.open(pdf_path) as plumber_pdf:
        summary.total_pages = len(plumber_pdf.pages)

        for page_num, (plumber_page, fitz_page) in enumerate(
            zip(plumber_pdf.pages, fitz_doc.pages()), start=1
        ):
            print(f"  Processing page {page_num}/{summary.total_pages}...")

            # 1. Text
            text_docs = extract_text(plumber_page, page_num, source)
            chunked_text = splitter.split_documents(text_docs)
            all_docs.extend(chunked_text)
            summary.text_chunks += len(chunked_text)

            # 2. Tables
            table_docs = extract_tables(plumber_page, page_num, source)
            chunked_tables = splitter.split_documents(table_docs)
            all_docs.extend(chunked_tables)
            summary.table_chunks += len(chunked_tables)

            # 3. Images / Charts / Logos / Icons
            image_docs = extract_images(fitz_page, page_num, source, vision_llm)
            all_docs.extend(image_docs)
            summary.image_chunks += len(image_docs)

            # 4. Math
            math_docs = extract_math(plumber_page, fitz_page, page_num, source, vision_llm)
            all_docs.extend(math_docs)
            summary.math_chunks += len(math_docs)

    fitz_doc.close()

    print(f"\n  Extraction complete:")
    print(f"    Pages   : {summary.total_pages}")
    print(f"    Text    : {summary.text_chunks} chunks")
    print(f"    Tables  : {summary.table_chunks} chunks")
    print(f"    Images  : {summary.image_chunks} chunks")
    print(f"    Math    : {summary.math_chunks} chunks")
    print(f"    TOTAL   : {summary.total_chunks} chunks")

    return all_docs, summary
