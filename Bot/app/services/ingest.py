# app/services/ingest.py
import os
import re
import pickle
import logging
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader
from docx import Document

# Set up logging
logger = logging.getLogger(__name__)


class DocumentIngestor:
    """Service for ingesting and processing documents into FAISS index."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        chunks_path: str = "data/chunks.pkl",
        index_path: str = "data/faiss.index",
    ):
        self.model_name = model_name
        self.chunks_path = Path(chunks_path)
        self.index_path = Path(index_path)
        self._model = None

        # Ensure data directory exists
        self.chunks_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the sentence transformer model."""
        if self._model is None:
            logger.info(f"Loading SentenceTransformer model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def load_document(self, filepath: str) -> str:
        """
        Load text content from various document types.

        Args:
            filepath: Path to the document file

        Returns:
            str: Extracted text content

        Raises:
            ValueError: If file type is not supported
            FileNotFoundError: If file doesn't exist
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        ext = filepath.suffix.lower()

        try:
            if ext == ".txt":
                return self._load_text_file(filepath)
            elif ext == ".pdf":
                return self._load_pdf_file(filepath)
            elif ext == ".docx":
                return self._load_docx_file(filepath)
            else:
                # For unknown extensions, try to read as text
                logger.warning(f"Unknown file type {ext}, attempting to read as text")
                return self._load_text_file(filepath)
        except Exception as e:
            logger.error(f"Error loading document {filepath}: {str(e)}")
            raise

    def _load_text_file(self, filepath: Path) -> str:
        """Load text from .txt file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(filepath, "r", encoding="latin-1") as f:
                return f.read()

    def _load_pdf_file(self, filepath: Path) -> str:
        """Load text from .pdf file."""
        reader = PdfReader(str(filepath))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text

    def _load_docx_file(self, filepath: Path) -> str:
        """Load text from .docx file."""
        doc = Document(str(filepath))
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.

        Args:
            text: Raw text to clean

        Returns:
            str: Cleaned text
        """
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove or replace non-ASCII characters more gently
        text = text.encode("ascii", "ignore").decode("ascii")

        # Remove common PDF artifacts
        text = re.sub(r"PoweredbyTCPDF.*", "", text)
        text = re.sub(r"Page number:\d+/\d+", "", text, flags=re.IGNORECASE)

        return text.strip()

    def chunk_text(
        self, text: str, max_tokens: int = 200, overlap: int = 20
    ) -> List[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk
            max_tokens: Maximum tokens per chunk
            overlap: Number of overlapping tokens between chunks

        Returns:
            List[str]: List of text chunks
        """
        if not text.strip():
            logger.warning("Empty text provided for chunking")
            return []

        words = text.split()
        if len(words) == 0:
            return []

        chunks = []
        start = 0

        while start < len(words):
            end = start + max_tokens
            chunk = " ".join(words[start:end])
            if chunk.strip():  # Only add non-empty chunks
                chunks.append(chunk)
            start += max_tokens - overlap

            # Prevent infinite loop
            if start >= len(words):
                break

        return chunks

    def build_faiss_index(
        self, chunks: List[str]
    ) -> Tuple[faiss.IndexFlatL2, np.ndarray]:
        """
        Build FAISS index from text chunks.

        Args:
            chunks: List of text chunks

        Returns:
            Tuple of (FAISS index, embeddings array)
        """
        if not chunks:
            raise ValueError("No chunks provided for index building")

        logger.info(f"Encoding {len(chunks)} chunks...")
        embeddings = self.model.encode(chunks, show_progress_bar=True)

        # Create FAISS index
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings.astype(np.float32))

        logger.info(f"Built FAISS index with {index.ntotal} vectors")
        return index, embeddings

    def save_chunks(self, chunks: List[str]) -> bool:
        """Save chunks to pickle file."""
        try:
            # Ensure directory exists
            self.chunks_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.chunks_path, "wb") as f:
                pickle.dump(chunks, f)
            logger.info(f"Saved {len(chunks)} chunks to {self.chunks_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save chunks: {str(e)}")
            return False

    def save_faiss_index(self, index: faiss.IndexFlatL2) -> bool:
        """Save FAISS index to file."""
        try:
            # Ensure directory exists
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            faiss.write_index(index, str(self.index_path))
            logger.info(f"Saved FAISS index to {self.index_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {str(e)}")
            return False

    def ingest_file(
        self, filepath: str, max_tokens: int = 200, overlap: int = 20
    ) -> Tuple[int, bool]:
        """
        Ingest a single file into the knowledge base.

        Args:
            filepath: Path to the file to ingest
            max_tokens: Maximum tokens per chunk
            overlap: Overlap between chunks

        Returns:
            Tuple of (number of chunks created, success status)
        """
        try:
            logger.info(f"📄 Loading document: {filepath}")

            # Load and process document
            raw_text = self.load_document(filepath)
            if not raw_text.strip():
                logger.warning(f"No text content found in {filepath}")
                return 0, False

            cleaned_text = self.clean_text(raw_text)
            new_chunks = self.chunk_text(cleaned_text, max_tokens, overlap)

            if not new_chunks:
                logger.warning(f"No chunks created from {filepath}")
                return 0, False

            logger.info(f"✂️ Document split into {len(new_chunks)} chunks")

            # Load existing data if available
            existing_chunks = self._load_existing_chunks()
            existing_index = self._load_existing_index()

            # Combine with new chunks
            all_chunks = existing_chunks + new_chunks

            # Build/update index
            if existing_index is not None and len(existing_chunks) > 0:
                # Add new embeddings to existing index
                logger.info("Updating existing index...")
                new_embeddings = self.model.encode(new_chunks)
                existing_index.add(new_embeddings.astype(np.float32))
                index = existing_index
            else:
                # Build new index
                logger.info("Building new index...")
                index, _ = self.build_faiss_index(all_chunks)

            # Save everything
            chunks_saved = self.save_chunks(all_chunks)
            index_saved = self.save_faiss_index(index)

            success = chunks_saved and index_saved
            if success:
                logger.info("✅ Document ingestion complete")
            else:
                logger.error("❌ Failed to save ingested data")

            return len(new_chunks), success

        except Exception as e:
            logger.error(f"Error ingesting file {filepath}: {str(e)}")
            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")
            return 0, False

    def ingest_directory(
        self, directory_path: str, max_tokens: int = 200, overlap: int = 20
    ) -> Tuple[int, int, bool]:
        """
        Ingest all supported files from a directory.

        Args:
            directory_path: Path to directory containing documents
            max_tokens: Maximum tokens per chunk
            overlap: Overlap between chunks

        Returns:
            Tuple of (total chunks, files processed, success status)
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        supported_extensions = {".txt", ".pdf", ".docx"}
        all_chunks = []
        files_processed = 0

        # Process each supported file
        for filepath in directory.iterdir():
            if filepath.is_file() and filepath.suffix.lower() in supported_extensions:
                try:
                    logger.info(f"📄 Processing: {filepath.name}")

                    raw_text = self.load_document(str(filepath))
                    cleaned_text = self.clean_text(raw_text)
                    chunks = self.chunk_text(cleaned_text, max_tokens, overlap)

                    all_chunks.extend(chunks)
                    files_processed += 1

                    logger.info(f"✅ {filepath.name} → {len(chunks)} chunks")

                except Exception as e:
                    logger.error(f"⚠️ Error processing {filepath.name}: {str(e)}")

        if not all_chunks:
            logger.warning("No chunks created from directory")
            return 0, files_processed, False

        # Build index and save
        try:
            logger.info(f"📦 Total chunks: {len(all_chunks)}")
            index, _ = self.build_faiss_index(all_chunks)

            chunks_saved = self.save_chunks(all_chunks)
            index_saved = self.save_faiss_index(index)

            success = chunks_saved and index_saved
            if success:
                logger.info("💾 All data saved successfully")
            else:
                logger.error("❌ Failed to save processed data")

            return len(all_chunks), files_processed, success

        except Exception as e:
            logger.error(f"Error building index: {str(e)}")
            return len(all_chunks), files_processed, False

    def _load_existing_chunks(self) -> List[str]:
        """Load existing chunks if available."""
        if self.chunks_path.exists():
            try:
                with open(self.chunks_path, "rb") as f:
                    chunks = pickle.load(f)
                logger.info(f"Loaded {len(chunks)} existing chunks")
                return chunks
            except Exception as e:
                logger.error(f"Error loading existing chunks: {str(e)}")
        return []

    def _load_existing_index(self) -> Optional[faiss.IndexFlatL2]:
        """Load existing FAISS index if available."""
        if self.index_path.exists():
            try:
                index = faiss.read_index(str(self.index_path))
                logger.info(f"Loaded existing FAISS index with {index.ntotal} vectors")
                return index
            except Exception as e:
                logger.error(f"Error loading existing index: {str(e)}")
        return None
