"""
src/ingestion/image_extractor.py
Extracts images (charts, logos, photos, icons) from PDF pages using PyMuPDF.
Each image is sent to a vision LLM to get a natural-language description.
The description is then stored as a searchable chunk in the vector store.
"""
import base64
import tempfile
import os
from typing import List

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage


def _image_bytes_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def _describe_image_with_llm(
    image_bytes: bytes,
    vision_llm,
    page_num: int,
    img_index: int,
) -> str:
    """
    Send image bytes to the vision LLM and return a text description.
    Works with Gemini 1.5 Flash (native vision) and Ollama LLaVA.
    """
    b64 = _image_bytes_to_base64(image_bytes)

    prompt = (
        "You are analyzing an image extracted from a PDF document. "
        "Describe this image in detail, including:\n"
        "- If it's a chart/graph: type of chart, what the axes represent, key data points, trends\n"
        "- If it's a table: summarize the data\n"
        "- If it's a logo/icon: describe what it represents\n"
        "- If it's a photo/diagram: describe what is shown\n"
        "- Any text visible in the image\n"
        "- Mathematical notation if present\n"
        "Be specific and factual. This description will be used for search."
    )

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            },
        ]
    )

    try:
        response = vision_llm.invoke([message])
        return response.content.strip()
    except Exception as e:
        return f"[Image on page {page_num}, index {img_index}: could not describe — {e}]"


def extract_images(fitz_page, page_num: int, source: str, vision_llm) -> List[Document]:
    """
    Extract all images from a PyMuPDF (fitz) page and describe them via vision LLM.

    Args:
        fitz_page: PyMuPDF page object (fitz.Page)
        page_num: 1-indexed page number
        source: PDF file path
        vision_llm: Vision-capable LangChain LLM (from get_vision_llm())

    Returns:
        List of Documents with image descriptions, metadata type="image"
    """
    import fitz  # PyMuPDF

    image_list = fitz_page.get_images(full=True)
    if not image_list:
        return []

    # Get the parent document to extract image bytes
    doc = fitz_page.parent
    documents = []

    for img_idx, img_info in enumerate(image_list):
        xref = img_info[0]
        try:
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext   = base_image.get("ext", "png")

            # Skip very small images (likely decorative bullets/borders)
            if len(image_bytes) < 1000:
                continue

            # Get natural language description
            description = _describe_image_with_llm(
                image_bytes, vision_llm, page_num, img_idx
            )

            content = (
                f"[IMAGE on page {page_num}, index {img_idx}]\n"
                f"Description: {description}"
            )

            documents.append(Document(
                page_content=content,
                metadata={
                    "source": source,
                    "page": page_num,
                    "type": "image",
                    "image_index": img_idx,
                    "image_format": image_ext,
                    "image_size_bytes": len(image_bytes),
                    "description": description,
                },
            ))

        except Exception as e:
            # Don't fail the whole ingestion if one image fails
            documents.append(Document(
                page_content=f"[IMAGE on page {page_num}, index {img_idx}: extraction failed — {e}]",
                metadata={
                    "source": source,
                    "page": page_num,
                    "type": "image",
                    "image_index": img_idx,
                    "error": str(e),
                },
            ))

    return documents
