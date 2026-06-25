from fastapi import APIRouter, UploadFile, File
import pandas as pd

from services.feature_engineering_service import feature_engineering

router = APIRouter()

@router.post("/feature-engineering")
async def analyze(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)
    return feature_engineering(df)