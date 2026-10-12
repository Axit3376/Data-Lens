from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CleaningOperation(BaseModel):
    action: str = Field(..., description="Action name, e.g. impute_median, remove_duplicates, cap_outliers")
    column: Optional[str] = Field(None, description="Affected column name, or None if whole-dataset operation")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Parameters for the cleaning operation")


class PreviewRequest(BaseModel):
    session_id: Optional[str] = Field("default_session", description="Session identifier")
    operations: List[CleaningOperation] = Field(..., description="List of cleaning operations to preview")


class ApplyRequest(BaseModel):
    session_id: Optional[str] = Field("default_session", description="Session identifier")
    preview_id: Optional[str] = Field(None, description="Preview ID to commit directly")
    operations: Optional[List[CleaningOperation]] = Field(None, description="Or list of operations to apply directly")


class UndoRequest(BaseModel):
    session_id: Optional[str] = Field("default_session", description="Session identifier")
