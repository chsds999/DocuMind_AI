import os
import uuid
from typing import List, Dict, Tuple

import chromadb
from chromadb.utils import embedding_functions

from openai import OpenAI

from .settings import settings
from .pdf_loader import extract_pages, chunk_text


client = OpenAI(api_key=settings.openai_api_key)

# Chroma client
chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)

# Use OpenAI embedding function through Chroma helper
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=settings.openai_api_key,
    model_name=settings.openai_embed_model,
)


def get_collection(doc_id: str):
    return chroma_client.get_or_create_collection(
        name=f"doc_{doc_id}",
        embedding_function=openai_ef,
        metadata={"hnsw:space": "cosine"},
    )


def ingest_pdf(file_path: str) -> Tuple[str, int, int]:
    """
    Create a new doc_id and store chunks in Chroma with metadata (page, source).
    Returns (doc_id, pages_count, chunks_count).
    """
    doc_id = uuid.uuid4().hex
    pages = extract_pages(file_path)

    collection = get_collection(doc_id)

    ids = []
    docs = []
    metas = []

    for p in pages:
        page_num = p["page"]
        text = p["text"]
        chunks = chunk_text(text)

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_{page_num}_{idx}"
            ids.append(chunk_id)
            docs.append(chunk)
            metas.append({"page": page_num})

    if docs:
        collection.add(ids=ids, documents=docs, metadatas=metas)

    return doc_id, len(pages), len(docs)


def retrieve(doc_id: str, question: str, k: int = 5) -> List[Dict]:
    collection = get_collection(doc_id)
    res = collection.query(query_texts=[question], n_results=k)

    out = []
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, dists):
        out.append(
            {
                "text": doc,
                "page": int(meta.get("page", -1)) if meta else -1,
                "distance": float(dist) if dist is not None else None,
            }
        )
    return out


def generate_answer(question: str, contexts: List[Dict]) -> Tuple[str, List[Dict]]:
    """
    Produces an answer grounded only in retrieved contexts.
    Returns (answer, citations)
    """
    if not contexts:
        return (
            "I couldn’t find relevant text in the uploaded document to answer that. Try rephrasing or asking about a specific section.",
            [],
        )

    context_block = "\n\n".join(
        [f"[Page {c['page']}]\n{c['text']}" for c in contexts if c["text"]]
    )

    system = (
        "You are a document Q&A assistant. Answer ONLY using the provided document excerpts. "
        "If the excerpts do not contain the answer, say you don't know. "
        "Keep the answer concise and factual. Provide no outside knowledge."
    )

    user = (
        f"Question:\n{question}\n\n"
        f"Document excerpts:\n{context_block}\n\n"
        "Instructions:\n"
        "- Answer using only the excerpts.\n"
        "- If missing, say you don't know based on the document.\n"
    )

    resp = client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )

    answer = resp.choices[0].message.content.strip()

    citations = []
    for c in contexts:
        snippet = c["text"][:220].replace("\n", " ").strip()
        citations.append({"page": c["page"], "snippet": snippet})

    return answer, citations
