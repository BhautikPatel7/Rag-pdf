"""
src/ingestion/table_extractor.py
Extracts tables from PDF pages using pdfplumber and converts them to
Markdown format so they can be embedded as searchable text chunks.
"""
from typing import List
from langchain_core.documents import Document


def _table_to_markdown(table: List[List]) -> str:
    """Convert a pdfplumber table (list of rows) to Markdown table string."""
    if not table or not table[0]:
        return ""

    # Sanitize cells
    def clean(cell) -> str:
        if cell is None:
            return ""
        return str(cell).strip().replace("\n", " ")

    rows = [[clean(cell) for cell in row] for row in table]
    header = rows[0]
    body   = rows[1:]

    # Build markdown
    lines = []
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    for row in body:
        # Pad short rows to header width
        padded = row + [""] * (len(header) - len(row))
        lines.append("| " + " | ".join(padded) + " |")

    return "\n".join(lines)


def extract_tables(page, page_num: int, source: str) -> List[Document]:
    """
    Extract all tables from a single pdfplumber page.

    Args:
        page: pdfplumber page object
        page_num: 1-indexed page number
        source: PDF file path

    Returns:
        List of Documents, one per table, with metadata type="table"
    """
    tables = page.extract_tables()
    if not tables:
        return []

    documents = []
    for table_idx, table in enumerate(tables):
        md = _table_to_markdown(table)
        if not md.strip():
            continue

        # Add a text prefix so the LLM has context about what the chunk is
        content = f"[TABLE on page {page_num}]\n{md}"

        documents.append(Document(
            page_content=content,
            metadata={
                "source": source,
                "page": page_num,
                "type": "table",
                "table_index": table_idx,
                "rows": len(table),
                "cols": len(table[0]) if table else 0,
            },
        ))

    return documents
