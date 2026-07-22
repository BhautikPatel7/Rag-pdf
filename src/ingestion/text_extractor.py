"""
src/ingestion/text_extractor.py
Extracts plain text (paragraphs, headings, body) from each PDF page.
Emojis and all UTF-8 characters are preserved as-is.
"""
import re
from typing import List
from langchain_core.documents import Document


def extract_text(page, page_num: int, source: str) -> List[Document]:
    """
    Extract text chunks from a single pdfplumber page.

    Args:
        page: pdfplumber page object
        page_num: 1-indexed page number
        source: PDF file path (used as metadata)

    Returns:
        List of Document objects with metadata type="text"
    """
    raw_text = page.extract_text()
    if not raw_text or not raw_text.strip():
        return []

    # Clean up: normalize whitespace, preserve newlines between paragraphs
    text = re.sub(r"\n{3,}", "\n\n", raw_text)   # collapse 3+ newlines → 2
    text = re.sub(r"[ \t]+", " ", text)            # collapse multiple spaces
    text = text.strip()

    if len(text) < 20:
        return []

    return [Document(
        page_content=text,
        metadata={
            "source": source,
            "page": page_num,
            "type": "text",
        },
    )]
