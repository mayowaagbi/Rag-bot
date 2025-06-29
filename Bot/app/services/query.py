# app/services/query.py
import os
import pickle
import gzip
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv
import gc  # For garbage collection

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)


class QueryService:
    """Service for querying the document knowledge base."""

    def __init__(
        self,
        model_name: str = "paraphrase-MiniLM-L3-v2",  # Smaller model
        chunks_path: str = "data/chunks.pkl.gz",  # Compressed storage
        index_path: str = "data/faiss.index",
        groq_model: str = "llama3-8b-8192",  # Smaller, faster model
        enable_compression: bool = True,
    ):
        self.model_name = model_name
        self.chunks_path = Path(chunks_path)
        self.index_path = Path(index_path)
        self.groq_model = groq_model
        self.enable_compression = enable_compression

        # Lazy-loaded components
        self._model = None
        self._chunks = None
        self._index = None
        self._groq_client = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the sentence transformer model."""
        if self._model is None:
            logger.info(f"Loading SentenceTransformer model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def unload_model(self):
        """Unload model to free memory when not needed."""
        if self._model is not None:
            del self._model
            self._model = None
            gc.collect()
            logger.info("Query model unloaded to save memory")

    @property
    def chunks(self) -> List[str]:
        """Lazy load the text chunks."""
        if self._chunks is None:
            self._chunks = self.load_chunks()
        return self._chunks

    @property
    def index(self) -> faiss.IndexFlatL2:
        """Lazy load the FAISS index."""
        if self._index is None:
            self._index = self.load_faiss_index()
        return self._index

    @property
    def groq_client(self) -> Groq:
        """Lazy load the Groq client."""
        if self._groq_client is None:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable is required")
            self._groq_client = Groq(api_key=api_key)
        return self._groq_client

    def load_chunks(self, filepath: Optional[str] = None) -> List[str]:
        """
        Load text chunks from pickle file with compression support.

        Args:
            filepath: Optional custom path to chunks file

        Returns:
            List[str]: List of text chunks

        Raises:
            FileNotFoundError: If chunks file doesn't exist
        """
        chunks_file = Path(filepath) if filepath else self.chunks_path

        if not chunks_file.exists():
            raise FileNotFoundError(f"Chunks file not found: {chunks_file}")

        try:
            if self.enable_compression and chunks_file.suffix == ".gz":
                with gzip.open(chunks_file, "rb") as f:
                    chunks = pickle.load(f)
            else:
                with open(chunks_file, "rb") as f:
                    chunks = pickle.load(f)
            logger.info(f"Loaded {len(chunks)} chunks from {chunks_file}")
            return chunks
        except Exception as e:
            logger.error(f"Error loading chunks: {str(e)}")
            raise

    def load_faiss_index(self, filepath: Optional[str] = None) -> faiss.IndexFlatL2:
        """
        Load FAISS index from file.

        Args:
            filepath: Optional custom path to index file

        Returns:
            faiss.IndexFlatL2: Loaded FAISS index

        Raises:
            FileNotFoundError: If index file doesn't exist
        """
        index_file = Path(filepath) if filepath else self.index_path

        if not index_file.exists():
            raise FileNotFoundError(f"FAISS index file not found: {index_file}")

        try:
            index = faiss.read_index(str(index_file))
            logger.info(
                f"Loaded FAISS index with {index.ntotal} vectors from {index_file}"
            )
            return index
        except Exception as e:
            logger.error(f"Error loading FAISS index: {str(e)}")
            raise

    def query_index(
        self, question: str, top_k: int = 3  # Reduced from 5 to save memory
    ) -> List[Tuple[str, float]]:
        """
        Query the FAISS index for relevant chunks with memory optimization.

        Args:
            question: User question to search for
            top_k: Number of top results to return (reduced for memory efficiency)

        Returns:
            List of (chunk_text, distance) tuples sorted by relevance
        """
        try:
            # Encode the question
            question_embedding = self.model.encode([question])

            # Search the index
            distances, indices = self.index.search(
                np.array(question_embedding), min(top_k, self.index.ntotal)
            )

            # Format results
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx < len(self.chunks):  # Ensure valid index
                    results.append((self.chunks[idx], float(distance)))

            # Clean up embeddings from memory
            del question_embedding, distances, indices
            gc.collect()

            logger.info(f"Found {len(results)} relevant chunks for query")
            return results

        except Exception as e:
            logger.error(f"Error querying index: {str(e)}")
            raise

    def generate_answer(
        self,
        question: str,
        context_chunks: List[str],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate an answer using Groq LLM based on context chunks.

        Args:
            question: User question
            context_chunks: List of relevant text chunks
            system_prompt: Optional custom system prompt

        Returns:
            Dict containing the answer and metadata
        """
        # Default system prompt
        if system_prompt is None:
            system_prompt = (
                "You are a helpful and knowledgeable assistant. Answer the user's question "
                "based primarily on the provided context. If the context doesn't contain "
                "sufficient information, clearly state this and provide what general knowledge "
                "you can that might be helpful. Be thorough and comprehensive in your response."
            )

        # Prepare context
        context_text = "\n\n".join(context_chunks)
        user_prompt = f"Context:\n{context_text}\n\nQuestion: {question}\n\nAnswer:"

        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model=self.groq_model,
                temperature=0.7,
                max_tokens=1024,
            )

            answer = response.choices[0].message.content

            return {
                "answer": answer,
                "model": self.groq_model,
                "context_chunks_used": len(context_chunks),
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error generating answer with Groq: {str(e)}")
            return {"answer": None, "error": str(e), "success": False}

    def search_and_answer(
        self, question: str, top_k: int = 5, system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete search and answer pipeline.

        Args:
            question: User question
            top_k: Number of chunks to use for context
            system_prompt: Optional custom system prompt

        Returns:
            Dict containing answer, sources, and metadata
        """
        try:
            # Search for relevant chunks
            search_results = self.query_index(question, top_k)

            if not search_results:
                return {
                    "answer": "I couldn't find any relevant information in the knowledge base.",
                    "sources": [],
                    "success": False,
                    "error": "No relevant chunks found",
                }

            # Extract chunks and distances
            chunks = [chunk for chunk, _ in search_results]
            distances = [distance for _, distance in search_results]

            # Generate answer
            answer_result = self.generate_answer(question, chunks, system_prompt)

            # Combine results
            result = {
                "question": question,
                "answer": answer_result.get("answer"),
                "sources": [
                    {"text": chunk, "relevance_score": float(distance), "rank": idx + 1}
                    for idx, (chunk, distance) in enumerate(search_results)
                ],
                "metadata": {
                    "chunks_used": len(chunks),
                    "model": self.groq_model,
                    "top_k": top_k,
                },
                "success": answer_result.get("success", False),
            }

            if not answer_result.get("success"):
                result["error"] = answer_result.get("error")

            return result

        except Exception as e:
            logger.error(f"Error in search and answer pipeline: {str(e)}")
            return {
                "question": question,
                "answer": None,
                "sources": [],
                "success": False,
                "error": str(e),
            }

    def health_check(self) -> Dict[str, Any]:
        """
        Check if all required components are available and working.

        Returns:
            Dict with health check status
        """
        status = {
            "chunks_available": False,
            "index_available": False,
            "model_loaded": False,
            "groq_api_available": False,
            "overall_status": "unhealthy",
        }

        try:
            # Check chunks
            if self.chunks_path.exists():
                chunks = self.load_chunks()
                status["chunks_available"] = len(chunks) > 0
                status["chunks_count"] = len(chunks)

            # Check index
            if self.index_path.exists():
                index = self.load_faiss_index()
                status["index_available"] = index.ntotal > 0
                status["index_vectors"] = index.ntotal

            # Check model (this will load it)
            model = self.model
            status["model_loaded"] = model is not None

            # Check Groq API
            if os.getenv("GROQ_API_KEY"):
                status["groq_api_available"] = True

            # Overall status
            if all(
                [
                    status["chunks_available"],
                    status["index_available"],
                    status["model_loaded"],
                    status["groq_api_available"],
                ]
            ):
                status["overall_status"] = "healthy"

        except Exception as e:
            status["error"] = str(e)

        return status


# Convenience functions for backward compatibility
def loadchunks(filepath: str = "data/chunks.pkl") -> List[str]:
    """Load chunks from pickle file."""
    service = QueryService(chunks_path=filepath)
    return service.load_chunks()


def load_faiss_index(filepath: str = "data/faiss.index") -> faiss.IndexFlatL2:
    """Load FAISS index from file."""
    service = QueryService(index_path=filepath)
    return service.load_faiss_index()


def load_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """Load sentence transformer model."""
    service = QueryService(model_name=model_name)
    return service.model


def query_index(
    question: str,
    index: faiss.IndexFlatL2,
    chunks: List[str],
    model: SentenceTransformer,
    top_k: int = 5,
) -> List[Tuple[str, float]]:
    """Query FAISS index for relevant chunks."""
    question_embedding = model.encode([question])
    distances, indices = index.search(np.array(question_embedding), top_k)
    results = [(chunks[i], distances[0][idx]) for idx, i in enumerate(indices[0])]
    return results
