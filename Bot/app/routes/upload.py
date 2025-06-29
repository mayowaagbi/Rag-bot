from fastapi import APIRouter, UploadFile, File, HTTPException
from app.utils.file_handler import save_file
from app.services.ingest import DocumentIngestor
from config import OptimizationConfig
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize ingestor with optimized configuration
ingest_service = DocumentIngestor(**OptimizationConfig.get_ingestor_config())


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Endpoint to upload and ingest a file with memory optimization.
    """
    try:
        # Save the uploaded file
        file_path = await save_file(file)

        # Get optimized chunking parameters
        chunk_params = OptimizationConfig.get_chunking_params()

        # Ingest the file with optimized settings
        chunks_created, success = ingest_service.ingest_file(
            file_path,
            max_tokens=chunk_params["max_tokens"],
            overlap=chunk_params["overlap"],
        )

        if success:
            return {
                "message": "File uploaded and ingested successfully",
                "file_path": file_path,
                "chunks_created": chunks_created,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to ingest file")

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
