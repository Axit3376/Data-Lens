from fastapi import APIRouter, UploadFile, File
from services.profiling_service import profile_dataset

router = APIRouter()

@router.post("/profiling")
async def upload_file(file: UploadFile = File(...)):
    return profile_dataset(file)