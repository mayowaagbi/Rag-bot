from fastapi import APIRouter,uploadFile,File
from app.utils.file_handler import save_file

router = APIRouter()
@router.post("/upload")
async def upload_file(file: uploadFile = File(...)):
    """
    Endpoint to upload a file.
    """
    try:
        # Save the uploaded file
        file_path = await save_file(file)
        return {"message": "File uploaded successfully", "file_path": file_path}
    except Exception as e:
        return {"error": str(e)}
    