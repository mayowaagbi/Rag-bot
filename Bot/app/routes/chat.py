# app/routers/query.py
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from app.services.query import QueryService
from app.services.ingest import DocumentIngestor
from config import OptimizationConfig
import os

# Set up logging
logger = logging.getLogger(__name__)

# Initialize services with optimized configuration
query_service = QueryService(**OptimizationConfig.get_query_config())
ingest_service = DocumentIngestor(**OptimizationConfig.get_ingestor_config())

router = APIRouter(prefix="/api/v1", tags=["knowledge-base"])

# Pydantic models for request/response validation
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="The question to ask")
    top_k: int = Field(default=OptimizationConfig.TOP_K_RESULTS, ge=1, le=10, description="Number of relevant chunks to retrieve")  # Reduced max
    system_prompt: Optional[str] = Field(None, max_length=2000, description="Custom system prompt for the LLM")

class SourceChunk(BaseModel):
    text: str
    relevance_score: float
    rank: int

class QueryResponse(BaseModel):
    question: str
    answer: Optional[str]
    sources: List[SourceChunk]
    metadata: Dict[str, Any]
    success: bool
    error: Optional[str] = None

class IngestResponse(BaseModel):
    success: bool
    message: str
    chunks_created: int
    files_processed: Optional[int] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    details: Dict[str, Any]

@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query the document knowledge base with a question.
    
    This endpoint searches through ingested documents to find relevant information
    and generates an AI-powered answer based on the context.
    """
    try:
        logger.info(f"Received query: {request.question[:100]}...")
        
        result = query_service.search_and_answer(
            question=request.question,
            top_k=request.top_k,
            system_prompt=request.system_prompt
        )
        
        response = QueryResponse(
            question=result["question"],
            answer=result.get("answer"),
            sources=[
                SourceChunk(
                    text=source["text"],
                    relevance_score=source["relevance_score"],
                    rank=source["rank"]
                )
                for source in result.get("sources", [])
            ],
            metadata=result.get("metadata", {}),
            success=result["success"],
            error=result.get("error")
        )
        
        if not response.success:
            logger.error(f"Query failed: {response.error}")
            raise HTTPException(status_code=500, detail=response.error)
        
        logger.info(f"Query processed successfully, returned {len(response.sources)} sources")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in query endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/query/simple")
async def simple_query(request: Request):
    try:
        data = await request.json()
        question = data.get("question")
        
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        if not isinstance(question, str) or len(question.strip()) == 0:
            raise HTTPException(status_code=400, detail="Question must be a non-empty string")
        
        # Use the query service
        result = query_service.search_and_answer(question=question.strip())
        if result["success"]:
            return {
                "success": True,
                "answer": result["answer"],
                "sources": [source["text"] for source in result["sources"]],
                "relevance_scores": [source["relevance_score"] for source in result["sources"]]
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Query failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in simple query endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    max_tokens: int = Form(default=200, ge=50, le=1000),
    overlap: int = Form(default=20, ge=0, le=100)
):
    """
    Ingest a single document file into the knowledge base.
    
    Supported file types: .txt, .pdf, .docx
    """
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in ['txt', 'pdf', 'docx']:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_ext}. Supported types: txt, pdf, docx"
            )
        
        # Save uploaded file temporarily
        temp_path = f"temp_{file.filename}"
        try:
            content = await file.read()
            with open(temp_path, "wb") as f:
                f.write(content)
            
            # Ingest the file
            chunks_created, success = ingest_service.ingest_file(
                filepath=temp_path,
                max_tokens=max_tokens,
                overlap=overlap
            )
            
            if success:
                message = f"Successfully ingested {chunks_created} chunks from {file.filename}"
                logger.info(message)
                return IngestResponse(
                    success=True,
                    message=message,
                    chunks_created=chunks_created,
                    files_processed=1
                )
            else:
                raise HTTPException(status_code=500, detail="Failed to ingest file")
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")