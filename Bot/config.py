# config.py
"""
Configuration settings for optimized deployment on resource-constrained platforms.
"""

import os
from typing import Dict, Any

class OptimizationConfig:
    """Configuration class for deployment optimization settings."""
    
    # Model settings - using smaller, faster models
    EMBEDDING_MODEL = "paraphrase-MiniLM-L3-v2"  # Smaller than all-MiniLM-L6-v2
    LLM_MODEL = "llama3-8b-8192"  # Smaller than llama3-70b-8192
    
    # Memory optimization settings
    MAX_CHUNKS = int(os.getenv("MAX_CHUNKS", "1000"))  # Limit total chunks in memory
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))  # Process embeddings in batches
    TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "3"))  # Fewer results per query
    
    # Chunking settings - larger chunks = fewer total chunks
    MAX_TOKENS_PER_CHUNK = int(os.getenv("MAX_TOKENS_PER_CHUNK", "400"))  # Increased from 200
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))  # Reduced overlap
    
    # Storage settings
    ENABLE_COMPRESSION = os.getenv("ENABLE_COMPRESSION", "true").lower() == "true"
    CHUNKS_FILE = "data/chunks.pkl.gz" if ENABLE_COMPRESSION else "data/chunks.pkl"
    INDEX_FILE = "data/faiss.index"
    
    # Memory management
    UNLOAD_MODEL_AFTER_USE = os.getenv("UNLOAD_MODEL_AFTER_USE", "true").lower() == "true"
    
    @classmethod
    def get_ingestor_config(cls) -> Dict[str, Any]:
        """Get configuration for DocumentIngestor."""
        return {
            "model_name": cls.EMBEDDING_MODEL,
            "chunks_path": cls.CHUNKS_FILE,
            "index_path": cls.INDEX_FILE,
            "max_chunks": cls.MAX_CHUNKS,
            "enable_compression": cls.ENABLE_COMPRESSION,
        }
    
    @classmethod
    def get_query_config(cls) -> Dict[str, Any]:
        """Get configuration for QueryService."""
        return {
            "model_name": cls.EMBEDDING_MODEL,
            "chunks_path": cls.CHUNKS_FILE,
            "index_path": cls.INDEX_FILE,
            "groq_model": cls.LLM_MODEL,
            "enable_compression": cls.ENABLE_COMPRESSION,
        }
    
    @classmethod
    def get_chunking_params(cls) -> Dict[str, int]:
        """Get optimized chunking parameters."""
        return {
            "max_tokens": cls.MAX_TOKENS_PER_CHUNK,
            "overlap": cls.CHUNK_OVERLAP,
        }
    
    @classmethod
    def get_query_params(cls) -> Dict[str, int]:
        """Get optimized query parameters."""
        return {
            "top_k": cls.TOP_K_RESULTS,
        }

# Environment-specific configurations
class DeploymentProfiles:
    """Pre-configured profiles for different deployment environments."""
    
    RENDER_FREE = {
        "MAX_CHUNKS": "500",
        "MAX_TOKENS_PER_CHUNK": "500",
        "CHUNK_OVERLAP": "25",
        "TOP_K_RESULTS": "2",
        "BATCH_SIZE": "25",
        "ENABLE_COMPRESSION": "true",
        "UNLOAD_MODEL_AFTER_USE": "true",
    }
    
    VERCEL = {
        "MAX_CHUNKS": "300",
        "MAX_TOKENS_PER_CHUNK": "600",
        "CHUNK_OVERLAP": "30",
        "TOP_K_RESULTS": "2",
        "BATCH_SIZE": "20",
        "ENABLE_COMPRESSION": "true",
        "UNLOAD_MODEL_AFTER_USE": "true",
    }
    
    RAILWAY = {
        "MAX_CHUNKS": "800",
        "MAX_TOKENS_PER_CHUNK": "400",
        "CHUNK_OVERLAP": "40",
        "TOP_K_RESULTS": "3",
        "BATCH_SIZE": "40",
        "ENABLE_COMPRESSION": "true",
        "UNLOAD_MODEL_AFTER_USE": "true",
    }
    
    @classmethod
    def apply_profile(cls, profile_name: str):
        """Apply a deployment profile by setting environment variables."""
        profiles = {
            "render": cls.RENDER_FREE,
            "vercel": cls.VERCEL,
            "railway": cls.RAILWAY,
        }
        
        if profile_name.lower() not in profiles:
            raise ValueError(f"Unknown profile: {profile_name}. Available: {list(profiles.keys())}")
        
        profile = profiles[profile_name.lower()]
        for key, value in profile.items():
            os.environ[key] = value
        
        print(f"Applied {profile_name} optimization profile")
