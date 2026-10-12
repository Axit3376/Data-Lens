import uuid
import os
import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import Response

from schemas.cleaning import PreviewRequest, ApplyRequest, UndoRequest
from services.cleaning_service import detect_cleaning_recommendations, execute_cleaning_plan
from services.quality_score_service import compute_quality_score
from utils.analysis_store import (
    load_dataset,
    save_dataset_version,
    save_preview_dataset,
    get_preview_info,
    load_preview_dataset,
    undo_cleaning_version,
    load_session_meta,
    update_analysis,
    load_analysis
)

router = APIRouter(prefix="/cleaning", tags=["cleaning"])


@router.api_route("/analyze", methods=["GET", "POST"])
async def analyze_cleaning(session_id: str = Query("default_session")):
    """
    Returns detected issues, recommended cleaning operations, and the current quality score.
    """
    try:
        df = load_dataset(session_id)
    except FileNotFoundError:
        # Fall back to trying to load from latest analysis or sample if session not found
        raise HTTPException(status_code=404, detail=f"No dataset found for session '{session_id}'. Please upload a dataset first.")

    meta = load_session_meta(session_id)
    recommendations = detect_cleaning_recommendations(df)
    quality_score = compute_quality_score(df)
    
    # Update analysis store with quality score
    update_analysis("quality_score", quality_score)
    
    return {
        "session_id": session_id,
        "current_version": meta.get("current_version", 0),
        "total_rows": len(df),
        "total_cols": len(df.columns),
        "quality_score": quality_score,
        "recommendations": recommendations,
        "history": meta.get("history", [])
    }


@router.post("/preview")
async def preview_cleaning(payload: PreviewRequest):
    """
    Executes cleaning operations on a temporary copy of the dataset.
    Returns preview summary, representative sample of changed records,
    and before-and-after quality score comparison.
    Does NOT mutate or commit changes.
    """
    session_id = payload.session_id or "default_session"
    try:
        df = load_dataset(session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset for session '{session_id}' not found.")

    meta = load_session_meta(session_id)
    current_version = meta.get("current_version", 0)

    # Compute original quality score
    score_before = compute_quality_score(df)

    # Run cleaning operations on isolated copy
    ops_list = [op.model_dump() for op in payload.operations]
    df_cleaned, summary = execute_cleaning_plan(df, ops_list)

    # Compute proposed quality score
    score_after = compute_quality_score(df_cleaned)

    # Prepare preview reference
    preview_id = str(uuid.uuid4())[:8]
    preview_info = {
        "preview_id": preview_id,
        "base_version": current_version,
        "operations": ops_list,
        "summary": summary,
        "score_before": score_before,
        "score_after": score_after
    }
    
    # Save preview isolated artifact
    save_preview_dataset(session_id, preview_id, df_cleaned, preview_info)

    # Representative preview rows (first 10 rows before and after)
    head_before = df.head(8).fillna("").to_dict(orient="records")
    head_after = df_cleaned.head(8).fillna("").to_dict(orient="records")

    return {
        "preview_id": preview_id,
        "session_id": session_id,
        "base_version": current_version,
        "summary": summary,
        "score_before": score_before,
        "score_after": score_after,
        "sample_before": head_before,
        "sample_after": head_after,
        "columns_before": list(df.columns),
        "columns_after": list(df_cleaned.columns)
    }


@router.post("/apply")
async def apply_cleaning(payload: ApplyRequest):
    """
    Applies the approved cleaning plan or previewed dataset, creating a new committed dataset version.
    Rejects stale previews if current version has advanced.
    """
    session_id = payload.session_id or "default_session"
    meta = load_session_meta(session_id)
    current_version = meta.get("current_version", 0)

    if payload.preview_id:
        preview_info = get_preview_info(session_id, payload.preview_id)
        if not preview_info:
            raise HTTPException(status_code=404, detail=f"Preview reference '{payload.preview_id}' not found or expired.")
        
        # Check staleness
        if preview_info.get("base_version") != current_version:
            raise HTTPException(
                status_code=409,
                detail=f"Preview is stale: generated on version {preview_info.get('base_version')} but dataset is now at version {current_version}."
            )
        
        # Load the previewed dataframe
        df_cleaned = load_preview_dataset(session_id, payload.preview_id)
        ops_executed = preview_info.get("operations", [])
        summary = preview_info.get("summary", {})
    elif payload.operations:
        try:
            df = load_dataset(session_id)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Dataset not found.")
        ops_list = [op.model_dump() for op in payload.operations]
        df_cleaned, summary = execute_cleaning_plan(df, ops_list)
        ops_executed = ops_list
    else:
        raise HTTPException(status_code=400, detail="Must provide either preview_id or operations list.")

    # Commit new dataset version
    new_version = save_dataset_version(session_id, df_cleaned, {
        "operation_id": str(uuid.uuid4())[:8],
        "operations": ops_executed,
        "summary": summary.get("operations_executed", [])
    })

    # Recalculate and update quality score and profiling metrics in analysis store
    new_score = compute_quality_score(df_cleaned)
    update_analysis("quality_score", new_score)

    # Update basic profiling info in store
    analysis = load_analysis()
    if "profiling" in analysis and "dataset_info" in analysis["profiling"]:
        analysis["profiling"]["dataset_info"]["rows"] = len(df_cleaned)
        analysis["profiling"]["dataset_info"]["cols"] = len(df_cleaned.columns)
        analysis["profiling"]["dataset_info"]["duplicate_values"] = int(df_cleaned.duplicated().sum())
        update_analysis("profiling", analysis["profiling"])

    return {
        "status": "success",
        "session_id": session_id,
        "previous_version": current_version,
        "current_version": new_version,
        "quality_score": new_score,
        "summary": summary
    }


@router.post("/undo")
async def undo_cleaning(payload: UndoRequest):
    """
    Restores the previous dataset version.
    """
    session_id = payload.session_id or "default_session"
    try:
        previous_version = undo_cleaning_version(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Re-evaluate score on restored version
    df_restored = load_dataset(session_id, previous_version)
    restored_score = compute_quality_score(df_restored)
    update_analysis("quality_score", restored_score)

    return {
        "status": "success",
        "session_id": session_id,
        "current_version": previous_version,
        "quality_score": restored_score
    }


@router.get("/export")
async def export_cleaned_dataset(session_id: str = Query("default_session"), version: int = Query(None)):
    """
    Downloads the currently approved cleaned dataset as a CSV file.
    """
    try:
        df = load_dataset(session_id, version)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset version not found.")

    meta = load_session_meta(session_id)
    orig_filename = meta.get("filename", "dataset.csv")
    base_name = os.path.splitext(orig_filename)[0]
    curr_v = version if version is not None else meta.get("current_version", 0)
    download_filename = f"{base_name}_cleaned_v{curr_v}.csv" if curr_v > 0 else f"{base_name}_v0.csv"

    csv_data = df.to_csv(index=False)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{download_filename}"'}
    )
