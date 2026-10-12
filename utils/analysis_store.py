import os
import json
import uuid
import shutil
import pandas as pd
from typing import Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(BASE_DIR, "tmp", "datasets")
SESSIONS_DIR = os.path.join(BASE_DIR, "tmp", "sessions")
ANALYSIS_FILE = os.path.join(BASE_DIR, "analysis", "latest_analysis.json")

os.makedirs(DATASETS_DIR, exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(ANALYSIS_FILE), exist_ok=True)

DEFAULT_SESSION_ID = "default_session"


def get_dataset_version_path(session_id: str, version: int) -> str:
    return os.path.join(DATASETS_DIR, f"{session_id}_v{version}.csv")


def get_preview_path(session_id: str, preview_id: str) -> str:
    return os.path.join(DATASETS_DIR, f"preview_{session_id}_{preview_id}.csv")


def get_session_meta_path(session_id: str) -> str:
    return os.path.join(SESSIONS_DIR, f"{session_id}_meta.json")


def load_session_meta(session_id: str) -> Dict[str, Any]:
    meta_path = get_session_meta_path(session_id)
    if not os.path.exists(meta_path):
        return {
            "session_id": session_id,
            "filename": "dataset.csv",
            "current_version": 0,
            "max_version": 0,
            "history": [],
            "previews": {}
        }
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_session_meta(session_id: str, meta: Dict[str, Any]) -> None:
    meta_path = get_session_meta_path(session_id)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4)


def register_dataset_upload(df: pd.DataFrame, filename: str, session_id: Optional[str] = None) -> str:
    """Stores initial dataset version (v0) and initializes session metadata."""
    if not session_id:
        session_id = DEFAULT_SESSION_ID
    
    meta = {
        "session_id": session_id,
        "filename": filename,
        "current_version": 0,
        "max_version": 0,
        "history": [
            {
                "version": 0,
                "operation_id": "initial_upload",
                "operations": [],
                "timestamp": pd.Timestamp.now().isoformat(),
                "summary": f"Uploaded original dataset: {filename}"
            }
        ],
        "previews": {}
    }
    
    # Save v0 CSV
    v0_path = get_dataset_version_path(session_id, 0)
    df.to_csv(v0_path, index=False)
    save_session_meta(session_id, meta)
    return session_id


def load_dataset(session_id: str, version: Optional[int] = None) -> pd.DataFrame:
    meta = load_session_meta(session_id)
    target_version = version if version is not None else meta.get("current_version", 0)
    path = get_dataset_version_path(session_id, target_version)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset for session '{session_id}' version '{target_version}' not found.")
    return pd.read_csv(path)


def save_dataset_version(session_id: str, df: pd.DataFrame, operations_summary: Dict[str, Any]) -> int:
    meta = load_session_meta(session_id)
    new_version = meta.get("current_version", 0) + 1
    new_path = get_dataset_version_path(session_id, new_version)
    df.to_csv(new_path, index=False)
    
    meta["current_version"] = new_version
    meta["max_version"] = max(meta.get("max_version", 0), new_version)
    meta["history"].append({
        "version": new_version,
        "timestamp": pd.Timestamp.now().isoformat(),
        **operations_summary
    })
    save_session_meta(session_id, meta)
    return new_version


def save_preview_dataset(session_id: str, preview_id: str, df: pd.DataFrame, preview_data: Dict[str, Any]) -> None:
    path = get_preview_path(session_id, preview_id)
    df.to_csv(path, index=False)
    
    meta = load_session_meta(session_id)
    if "previews" not in meta:
        meta["previews"] = {}
    meta["previews"][preview_id] = preview_data
    save_session_meta(session_id, meta)


def get_preview_info(session_id: str, preview_id: str) -> Optional[Dict[str, Any]]:
    meta = load_session_meta(session_id)
    return meta.get("previews", {}).get(preview_id)


def load_preview_dataset(session_id: str, preview_id: str) -> pd.DataFrame:
    path = get_preview_path(session_id, preview_id)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Preview '{preview_id}' not found.")
    return pd.read_csv(path)


def undo_cleaning_version(session_id: str) -> int:
    meta = load_session_meta(session_id)
    curr = meta.get("current_version", 0)
    if curr <= 0:
        raise ValueError("Cannot undo: Already at original dataset version (v0).")
    
    meta["current_version"] = curr - 1
    save_session_meta(session_id, meta)
    return meta["current_version"]


# Backwards compatible analysis store functions
def load_analysis() -> Dict[str, Any]:
    if not os.path.exists(ANALYSIS_FILE):
        return {}
    with open(ANALYSIS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_analysis(data: Dict[str, Any]) -> None:
    with open(ANALYSIS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def update_analysis(section: str, data: Any) -> None:
    analysis = load_analysis()
    analysis[section] = data
    save_analysis(analysis)


def clear_analysis() -> None:
    save_analysis({})