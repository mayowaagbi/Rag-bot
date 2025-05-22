from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
from PyPDF2 import PdfReader
import docx


def load_documents_from_directory(directory_path):
    ext = os.path.splitext(directory_path)[1].lower()

    if ext == ".txt":
        with open(directory_path, r, encoding="utf-8") as f:
            return f.read().splitlines()
    elif ext == ".pdf":
        reader = PdfReader(directory_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text.splitlines()
    elif ext == ".docx":
        doc =docx.Document(directory_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text
        return text.splitlines()
    #will add later
    # elif ext == ".pptx":
    #     from pptx import Presentation
    #     prs = Presentation(directory_path)
    #     text = ""
    #     for slide in prs.slides:
    #         for shape in slide.shapes:
    #             if hasattr(shape, "text"):
    #                 text += shape.text + "\n"
    #     return text.splitlines()
    else:
        raise ValueError(f"Unsupported file type: {ext}")   

