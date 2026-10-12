import pytest
import io
import pandas as pd
from fastapi.testclient import TestClient

from main import app
from utils.analysis_store import register_dataset_upload, load_dataset


client = TestClient(app)


@pytest.fixture
def sample_dataset():
    session_id = "test_session_api"
    csv_content = (
        "id,name,age,city\n"
        "1,Alice,25,Pune\n"
        "2,Bob,,pune\n"
        "3,Charlie,30, Mumbai \n"
        "3,Charlie,30, Mumbai \n"  # Duplicate row
        "4,David,150,Delhi\n"      # Outlier in age
    )
    df = pd.read_csv(io.StringIO(csv_content))
    register_dataset_upload(df, "test.csv", session_id)
    return session_id


def test_api_analyze(sample_dataset):
    resp = client.post(f"/cleaning/analyze?session_id={sample_dataset}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == sample_dataset
    assert data["total_rows"] == 5
    assert "quality_score" in data
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0


def test_api_preview_non_destructive(sample_dataset):
    # Check original dataset before preview
    df_before = load_dataset(sample_dataset)
    assert len(df_before) == 5

    preview_payload = {
        "session_id": sample_dataset,
        "operations": [
            {"action": "remove_duplicates"},
            {"action": "impute_median", "column": "age"}
        ]
    }
    resp = client.post("/cleaning/preview", json=preview_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "preview_id" in data
    assert data["summary"]["rows_removed"] == 1
    assert data["score_after"]["overall_score"] > data["score_before"]["overall_score"]

    # Original dataframe must STILL have 5 rows and missing age (non-destructive)
    df_after = load_dataset(sample_dataset)
    assert len(df_after) == 5
    assert df_after["age"].isna().sum() == 1


def test_api_apply_and_undo_and_export(sample_dataset):
    # 1. Preview
    preview_payload = {
        "session_id": sample_dataset,
        "operations": [
            {"action": "remove_duplicates"},
            {"action": "impute_median", "column": "age"}
        ]
    }
    preview_resp = client.post("/cleaning/preview", json=preview_payload)
    preview_id = preview_resp.json()["preview_id"]

    # 2. Apply via preview_id
    apply_resp = client.post("/cleaning/apply", json={
        "session_id": sample_dataset,
        "preview_id": preview_id
    })
    assert apply_resp.status_code == 200
    apply_data = apply_resp.json()
    assert apply_data["current_version"] == 1
    assert apply_data["previous_version"] == 0

    # Dataset at current version should now have 4 rows and 0 missing ages
    df_cleaned = load_dataset(sample_dataset)
    assert len(df_cleaned) == 4
    assert df_cleaned["age"].isna().sum() == 0

    # 3. Export CSV
    export_resp = client.get(f"/cleaning/export?session_id={sample_dataset}")
    assert export_resp.status_code == 200
    assert export_resp.headers["content-type"].startswith("text/csv")
    assert "cleaned_v1" in export_resp.headers.get("content-disposition", "")
    exported_df = pd.read_csv(io.StringIO(export_resp.text))
    assert len(exported_df) == 4

    # 4. Undo
    undo_resp = client.post("/cleaning/undo", json={"session_id": sample_dataset})
    assert undo_resp.status_code == 200
    assert undo_resp.json()["current_version"] == 0

    # Restored dataset should have 5 rows again
    df_restored = load_dataset(sample_dataset)
    assert len(df_restored) == 5
    assert df_restored["age"].isna().sum() == 1


def test_api_stale_preview_rejection(sample_dataset):
    # Preview on v0
    preview_resp = client.post("/cleaning/preview", json={
        "session_id": sample_dataset,
        "operations": [{"action": "remove_duplicates"}]
    })
    preview_id = preview_resp.json()["preview_id"]

    # Directly advance version to v1 with another apply
    client.post("/cleaning/apply", json={
        "session_id": sample_dataset,
        "operations": [{"action": "trim_whitespace", "column": "city"}]
    })

    # Now attempt to apply the old preview (which was generated on v0)
    stale_resp = client.post("/cleaning/apply", json={
        "session_id": sample_dataset,
        "preview_id": preview_id
    })
    assert stale_resp.status_code == 409
    assert "stale" in stale_resp.json()["detail"].lower()
