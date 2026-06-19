from fastapi import APIRouter, UploadFile, File
import pandas as pd

from services.quality_service import analyze_quality

router = APIRouter()

@router.post("/analysis")
async def quality_analysis(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)

    result = analyze_quality(df)

    return result