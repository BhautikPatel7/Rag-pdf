"""
src/ingestion/math_extractor.py
Detects and extracts mathematical content from PDF pages.
Strategy:
  1. Scan page text for math symbols / LaTeX patterns
  2. If math found, extract the region as an image and describe via vision LLM
  3. Also store the raw math text for keyword search
"""
import re
from typing import List

from langchain_core.documents import Document

# Unicode math symbols that indicate mathematical content
MATH_SYMBOLS = set("∑∫√πΣαβγδεζηθλμξπρστυφψωΔΦΨΩ∂∇∞≤≥≠≈∝∈∉∩∪⊂⊃⊆⊇±×÷→←↔⟹⟺")

# LaTeX-like patterns in text
MATH_PATTERNS = [
    r"\b(cos|sin|tan|log|ln|exp|lim|sum|int|sqrt|partial|nabla)\b",
    r"[A-Za-z]\s*[=\+\-\*\/\^]\s*[A-Za-z0-9]",  # variable equations
    r"\d+\s*[\+\-\*\/\^]\s*\d+",                   # arithmetic
    r"O\([A-Za-z0-9\s\*\^]+\)",                    # Big-O notation
    r"[A-Za-z]\s*[_\^]\s*[{A-Za-z0-9}]",          # subscript/superscript
]

_MATH_RE = re.compile("|".join(MATH_PATTERNS), re.IGNORECASE)


def _has_math(text: str) -> bool:
    """Return True if the text contains mathematical content."""
    if any(ch in text for ch in MATH_SYMBOLS):
        return True
    return bool(_MATH_RE.search(text))


def extract_math(page, fitz_page, page_num: int, source: str, vision_llm) -> List[Document]:
    """
    Extract mathematical content from a page.

    Args:
        page: pdfplumber page object (for text extraction)
        fitz_page: PyMuPDF page (for rendering regions)
        page_num: 1-indexed page number
        source: PDF file path
        vision_llm: Vision LLM for describing math regions

    Returns:
        List of Documents with math content/descriptions
    """
    raw_text = page.extract_text() or ""

    if not _has_math(raw_text):
        return []

    # Extract math-containing lines
    math_lines = []
    for line in raw_text.split("\n"):
        if _has_math(line):
            math_lines.append(line.strip())

    if not math_lines:
        return []

    math_text = "\n".join(math_lines)

    # Try to render the full page as image and describe the math via vision LLM
    try:
        import fitz
        mat = fitz.Matrix(2, 2)   # 2x zoom for clarity
        clip = fitz_page.rect
        pix = fitz_page.get_pixmap(matrix=mat, clip=clip)
        img_bytes = pix.tobytes("png")

        from langchain_core.messages import HumanMessage
        import base64
        b64 = base64.b64encode(img_bytes).decode("utf-8")

        prompt = (
            "This is a page from a PDF document. "
            "Focus ONLY on the mathematical equations, formulas, or expressions visible. "
            "For each equation:\n"
            "1. Write it in plain English (e.g. 'cosine similarity equals dot product divided by product of norms')\n"
            "2. Explain what each symbol means\n"
            "3. Explain what the formula is used for\n"
            "Ignore non-mathematical text."
        )
        message = HumanMessage(content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ])
        vision_desc = vision_llm.invoke([message]).content.strip()

        content = (
            f"[MATH on page {page_num}]\n"
            f"Raw math text:\n{math_text}\n\n"
            f"Vision LLM description:\n{vision_desc}"
        )
    except Exception as e:
        # Fallback: just store raw math text
        content = f"[MATH on page {page_num}]\n{math_text}"

    return [Document(
        page_content=content,
        metadata={
            "source": source,
            "page": page_num,
            "type": "math",
            "math_lines": len(math_lines),
        },
    )]
