from fastapi import APIRouter, UploadFile, File, Form
import pandas as pd

from services.visualization_service import visualization_analysis

router = APIRouter()


@router.post("/visualizations")
async def visualize(file: UploadFile = File(...),  target: str = Form(None)):

    df = pd.read_csv(file.file)

    return visualization_analysis(df, target)