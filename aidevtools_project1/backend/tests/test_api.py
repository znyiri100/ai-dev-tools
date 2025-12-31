import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys

# Patch modules before importing api
# We need to mock load_data and youtube_api to avoid side effects
mock_load_data = MagicMock()
mock_youtube_api = MagicMock()
mock_database = MagicMock()

with patch.dict(sys.modules, {
    'load_data': mock_load_data, 
    'youtube_api': mock_youtube_api,
    'database': mock_database
}):
    from api import app, get_db

client = TestClient(app)

def test_get_video_info_success():
    # Setup mock
    mock_youtube_api.extract_video_id.return_value = "TEST_ID"
    mock_youtube_api.list_transcripts_json.return_value = {
        "video_id": "TEST_ID",
        "url": "http://test",
        "metadata": {
            "title": "Test Video",
            "description": "Desc",
            "author": "Me",
            "view_count": "100",
            "duration": "PT1M"
        },
        "transcripts": []
    }

    response = client.get("/api/v1/video/TEST_ID")
    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == "TEST_ID"
    assert data["metadata"]["title"] == "Test Video"

def test_get_video_info_not_found():
    mock_youtube_api.extract_video_id.return_value = "BAD_ID"
    mock_youtube_api.list_transcripts_json.return_value = {"error": "Video unavailable"}

    response = client.get("/api/v1/video/BAD_ID")
    assert response.status_code == 400
    assert "Video unavailable" in response.json()["detail"]

def test_store_video_data_success():
    mock_youtube_api.extract_video_id.return_value = "TEST_ID"
    mock_youtube_api.list_transcripts_json.return_value = {
        "video_id": "TEST_ID",
        "url": "http://test",
        "metadata": {"title": "Test", "description": "D", "author": "A", "view_count": "1", "duration": "P"},
        "transcripts": []
    }
    
    # Mock DB session
    mock_session = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_session

    response = client.post("/api/v1/video/TEST_ID/store")
    
    assert response.status_code == 200
    assert response.json()["video_id"] == "TEST_ID"
    
    # Verify load_data calls
    mock_load_data.load_video_metadata.assert_called()
    mock_load_data.load_transcripts_metadata.assert_called()
    
    # Cleanup dependency override
    app.dependency_overrides = {}

def test_list_stored_videos():
    # Mock DB session and query result
    mock_session = MagicMock()
    mock_video = MagicMock()
    mock_video.video_id = "DB_VID"
    mock_video.title = "DB Title"
    mock_video.fetched_at = "2025-01-01T00:00:00"
    
    mock_session.query.return_value.all.return_value = [mock_video]
    
    app.dependency_overrides[get_db] = lambda: mock_session
    
    response = client.get("/api/v1/db/videos")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["video_id"] == "DB_VID"
    
    # Cleanup
    app.dependency_overrides = {}
