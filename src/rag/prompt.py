"""
src/rag/prompt.py
System and human prompt templates for the RAG pipeline.
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

RAG_SYSTEM_PROMPT = """You are an expert AI assistant answering questions from enterprise PDF documents.

You have been given the following retrieved context chunks from the document.
Each chunk includes the page number and content type (text, table, image, math).

CONTEXT:
{context}

INSTRUCTIONS:
- Answer the question based ONLY on the provided context.
- If the answer is not in the context, say "I could not find this information in the provided document."
- When referencing specific data, mention the page number (e.g., "According to page 3...").
- For table data, present it clearly (use bullet points or short table format).
- For image/chart descriptions, summarize what the visual shows.
- For mathematical equations, explain them in plain language first, then show the formula.
- Be concise but complete. Do not hallucinate facts not in the context.
- Cite content type when relevant (e.g., "The bar chart on page 4 shows...").
"""

RAG_HUMAN_PROMPT = "Question: {question}"

def get_rag_prompt() -> ChatPromptTemplate:
    """Return the RAG chain prompt template."""
    return ChatPromptTemplate.from_messages([
        ("system", RAG_SYSTEM_PROMPT),
        ("human", RAG_HUMAN_PROMPT),
    ])


def format_docs(docs) -> str:
    """Format retrieved documents into a context string for the prompt."""
    parts = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        chunk_header = (
            f"[Chunk {i} | Page {meta.get('page', '?')} | "
            f"Type: {meta.get('type', 'unknown')}]"
        )
        parts.append(f"{chunk_header}\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)
