from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
from PyPDF2 import PdfReader
import docx
import pickle
import re


def load_documents_from_directory(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".txt":
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    elif ext == ".pdf":
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    elif ext == ".docx":
        doc = docx.Document(filepath)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def chunk_text(text, max_tokens=150, overlap=30):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + max_tokens
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += max_tokens - overlap
    return chunks


def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\x00-\x7F]+", "", text)
    text = re.sub(r"PoweredbyTCPDF.*", "", text)
    text = re.sub(r"Page number:\d+/\d+", "", text, flags=re.IGNORECASE)
    return text.strip()


def save_chunks(chunks, filepath="chunks.pkl"):
    with open(filepath, "wb") as f:
        pickle.dump(chunks, f)


def save_faiss_index(index, filepath="faiss.index"):
    faiss.write_index(index, filepath)


def build_faiss_index(chunks, model_name="all-MiniLM-L6-v2"):
    model = SentenceTransformer(model_name)
    embeddings = model.encode(chunks)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))
    return index, model, embeddings


def ingest_directory(dir_path):
    all_chunks = []
    for filename in os.listdir(dir_path):
        filepath = os.path.join(dir_path, filename)
        if not os.path.isfile(filepath):
            continue
        try:
            print(f"📄 Loading: {filename}")
            raw_text = load_documents_from_directory(filepath)
            cleaned = clean_text(raw_text)
            chunks = chunk_text(cleaned, max_tokens=200, overlap=20)
            all_chunks.extend(chunks)
            print(f"✅ {filename} → {len(chunks)} chunks")
        except Exception as e:
            print(f"⚠️ Error with {filename}: {e}")

    print(f"\n📦 Total Chunks: {len(all_chunks)}")
    index, model, embeddings = build_faiss_index(all_chunks)
    save_chunks(all_chunks)
    save_faiss_index(index)
    print("💾 All chunks and FAISS index saved.")
    return index, model


# def ingest_and_save(file_path):
#     print(f"📄 Loading single file from {file_path}")
#     raw_text = load_documents_from_directory(file_path)
#     cleaned_text = clean_text(raw_text)
#     chunks = chunk_text(cleaned_text, max_tokens=200, overlap=20)
#     print(f"✂️ Document split into {len(chunks)} chunks.")
#     index, model, embeddings = build_faiss_index(chunks)
#     save_chunks(chunks)
#     save_faiss_index(index)
#     print("💾 Saved single-file chunks and FAISS index.")
#     return index, model


def ingest_and_save_incrementally(
    file_path, chunks_path="chunks.pkl", index_path="faiss.index"
):
    print(f"🔍 Loading document from: {file_path}")
    raw_text = load_documents_from_directory(file_path)
    if isinstance(raw_text, list):
        raw_text = " ".join(raw_text)
    cleaned_text = clean_text(raw_text)
    new_chunks = chunk_text(cleaned_text, max_tokens=200, overlap=20)
    print(f"✂️ Document split into {len(chunks_path)} chunks.")

    model = SentenceTransformer("all-MiniLM-L6-v2")
    new_embeddings = model.encode(chunks_path)

    # Load existing index and chunks (if available)
    if os.path.exists(index_path) and os.path.exists(chunks_path):
        print("📦 Loading existing FAISS index and chunks...")
        index = faiss.read_index(index_path)
        with open(chunks_path, "rb") as f:
            existing_chunks = pickle.load(f)
    else:
        print("📦 No existing index or chunks found. Creating new ones...")
        index = faiss.IndexFlatL2(new_embeddings.shape[1])
        existing_chunks = []
    index.add(np.array(new_embeddings))
    all_chunks = existing_chunks + new_chunks

    print("💾 Saving updated index and chunks...")
    with open(chunks_path, "wb") as f:
        pickle.dump(all_chunks, f)
    faiss.write_index(index, index_path)
    print("✅ Document ingestion complete.\n")


# if __name__ == "__main__":
#     import sys

#     if len(sys.argv) < 3:
#         print("Usage: python ingest.py <mode: file|dir> <path>")
#         sys.exitnew(1)

#     mode, path = sys.argv[1], sys.argv[2]
#     if mode == "file":
#         ingest_and_save(path)
#     elif mode == "dir":
#         ingest_directory(path)
#     else:
#         print("Invalid mode. Use 'file' or 'dir'.")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ingest.py <file_path>")
        sys.exit(1)

    ingest_and_save_incrementally(sys.argv[1])
