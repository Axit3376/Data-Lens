from fastapi import APIRouter, UploadFile, File
from services.statistics_service import statistics_analysis

router = APIRouter()

@router.post("/statistics")
async def statistics(file:UploadFile = File(...)):
    return await statistics_analysis(file)