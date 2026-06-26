from fastapi import APIRouter, UploadFile, File
from services.profiling_service import profile_dataset
from utils.analysis_store import clear_analysis

router = APIRouter()

@router.post("/profiling")
async def upload_file(file: UploadFile = File(...)):
    clear_analysis()
    return profile_dataset(file)