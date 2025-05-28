# main.py - Enhanced FastAPI application setup
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Optional
from pydantic import BaseModel
import json
import asyncio
from datetime import datetime
import uuid
import os
from pathlib import Path

# from app.routes.chat import router as chat_router
from .routes.chat import router as chat_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Document Knowledge Base API",
    description="API for ingesting documents and querying them with AI-powered responses",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "https://mayowas-rag-bot.vercel.app",
    ],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your existing routers
app.include_router(chat_router)  # Your existing chat router
# app.include_router(query_router)  # Your query router


# Data models for frontend compatibility
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    id: Optional[str] = None
    createdAt: Optional[str] = None


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    documentIds: Optional[List[str]] = []


class Document(BaseModel):
    id: str
    name: str
    size: int
    type: str
    uploadedAt: str
    pages: Optional[int] = None


documents_store = {}

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


frontend_router = APIRouter(prefix="/api", tags=["frontend"])


@frontend_router.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):

    try:
        from app.services.ingest import DocumentIngestor

        ingest_service = DocumentIngestor()

        uploaded_docs = []

        for file in files:

            doc_id = str(uuid.uuid4())

            file_path = UPLOAD_DIR / f"{doc_id}_{file.filename}"
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            try:
                chunks_created, success = ingest_service.ingest_file(
                    filepath=str(file_path), max_tokens=200, overlap=20
                )

                if success:
                    # Create document record for frontend
                    document = Document(
                        id=doc_id,
                        name=file.filename,
                        size=len(content),
                        type=file.content_type or "application/octet-stream",
                        uploadedAt=datetime.now().isoformat(),
                        pages=chunks_created,  # Use chunks as page count for simplicity
                    )

                    # Store document info
                    documents_store[doc_id] = document
                    uploaded_docs.append(document)

                    logger.info(
                        f"Uploaded and ingested document: {file.filename} (ID: {doc_id}, Chunks: {chunks_created})"
                    )
                else:
                    logger.error(f"Failed to ingest document: {file.filename}")
                    # Clean up file
                    if file_path.exists():
                        file_path.unlink()
                    continue

            except Exception as ingest_error:
                logger.error(f"Error ingesting {file.filename}: {str(ingest_error)}")
                # Clean up file
                if file_path.exists():
                    file_path.unlink()
                continue

        return {
            "success": True,
            "documents": [doc.dict() for doc in uploaded_docs],
            "message": f"Successfully uploaded and processed {len(uploaded_docs)} document(s)",
        }

    except Exception as e:
        logger.error(f"Error uploading documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@frontend_router.get("/documents")
async def get_documents():
    """Get all uploaded documents"""
    return {"documents": [doc.dict() for doc in documents_store.values()]}


@frontend_router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove file from disk
    doc = documents_store[document_id]
    file_path = UPLOAD_DIR / f"{document_id}_{doc.name}"
    if file_path.exists():
        file_path.unlink()

    # Remove from store
    del documents_store[document_id]

    logger.info(f"Deleted document: {document_id}")
    return {"success": True, "message": "Document deleted successfully"}


async def stream_ai_response(question: str, document_ids: List[str]):
    """Stream AI response using your existing query service"""
    try:
        from app.services.query import QueryService

        query_service = QueryService()

        # Use your existing query service
        result = query_service.search_and_answer(question=question, top_k=5)

        if result["success"] and result.get("answer"):
            response_text = result["answer"]

            # Split response into words for streaming effect
            words = response_text.split()

            for i, word in enumerate(words):
                chunk_data = {
                    "choices": [
                        {
                            "delta": {
                                "content": word + (" " if i < len(words) - 1 else "")
                            }
                        }
                    ]
                }

                yield f"data: {json.dumps(chunk_data)}\n\n"
                await asyncio.sleep(0.05)  # Simulate streaming delay
        else:
            # Fallback response
            fallback_response = f"I couldn't find specific information about '{question}' in the uploaded documents. Please make sure your documents are properly uploaded and indexed."
            words = fallback_response.split()

            for i, word in enumerate(words):
                chunk_data = {
                    "choices": [
                        {
                            "delta": {
                                "content": word + (" " if i < len(words) - 1 else "")
                            }
                        }
                    ]
                }

                yield f"data: {json.dumps(chunk_data)}\n\n"
                await asyncio.sleep(0.05)

        # Send final chunk
        yield f"data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"Error in stream_ai_response: {str(e)}")
        error_response = (
            f"I encountered an error while processing your question: {str(e)}"
        )
        chunk_data = {"choices": [{"delta": {"content": error_response}}]}
        yield f"data: {json.dumps(chunk_data)}\n\n"
        yield f"data: [DONE]\n\n"


@frontend_router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Handle chat requests - integrates with your existing query service"""
    try:
        logger.info(f"Chat request received with {len(request.messages)} messages")

        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")

        # Get the last user message
        last_message = request.messages[-1]
        if last_message.role != "user":
            raise HTTPException(
                status_code=400, detail="Last message must be from user"
            )

        # Return streaming response using your existing services
        return StreamingResponse(
            stream_ai_response(last_message.content, request.documentIds or []),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8",
            },
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@frontend_router.get("/suggestions")
async def get_suggestions():
    """Get search suggestions"""
    suggestions = [
        "What are the main topics covered in my documents?",
        "Summarize the key findings from the uploaded files",
        "What are the most important points mentioned?",
        "Can you extract the main conclusions?",
        "What recommendations are provided in the documents?",
    ]

    return {"suggestions": suggestions}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    # Return a default favicon or 204 No Content
    return Response(status_code=204)


@frontend_router.post("/debug-chat")
async def debug_chat(request: dict):
    """Debug endpoint to see what we're receiving"""
    print(f"Received raw request: {request}")
    return {"received": request}


# Include the frontend integration router
app.include_router(frontend_router)


@app.get("/")
async def root():
    return {
        "message": "Document Knowledge Base API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/ping",
    }


@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "Service is running"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
