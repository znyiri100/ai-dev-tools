import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys

# Patch modules before importing api
mock_load_data = MagicMock()
mock_youtube_api = MagicMock()
mock_database = MagicMock()
mock_llm_utils = MagicMock()

with patch.dict(sys.modules, {
    'load_data': mock_load_data, 
    'youtube_api': mock_youtube_api,
    'database': mock_database,
    'llm_utils': mock_llm_utils
}):
    from api import app, get_db

client = TestClient(app)

def test_generate_study_guide_success():
    # Mock DB session and transcript
    mock_session = MagicMock()
    mock_transcript = MagicMock()
    mock_transcript.video_id = "VID1"
    mock_transcript.language_code = "en"
    mock_transcript.transcript = "This is a transcript."
    
    mock_session.query.return_value.filter.return_value.first.return_value = mock_transcript
    
    app.dependency_overrides[get_db] = lambda: mock_session
    
    # Mock LLM generation
    mock_llm_utils.generate_study_guide.return_value = "## Study Guide Content"

    response = client.post("/api/v1/transcript/VID1/en/generate_study_guide")
    
    assert response.status_code == 200
    assert response.json()["content"] == "## Study Guide Content"
    assert mock_transcript.study_guide == "## Study Guide Content"
    mock_session.commit.assert_called()
    
    app.dependency_overrides = {}

def test_generate_quiz_success():
    # Mock DB session and transcript
    mock_session = MagicMock()
    mock_transcript = MagicMock()
    mock_transcript.video_id = "VID1"
    mock_transcript.language_code = "en"
    mock_transcript.transcript = "This is a transcript."
    
    mock_session.query.return_value.filter.return_value.first.return_value = mock_transcript
    
    app.dependency_overrides[get_db] = lambda: mock_session
    
    # Mock LLM generation
    mock_llm_utils.generate_quiz.return_value = "## Quiz Content"

    response = client.post("/api/v1/transcript/VID1/en/generate_quiz")
    
    assert response.status_code == 200
    assert response.json()["content"] == "## Quiz Content"
    assert mock_transcript.quiz == "## Quiz Content"
    mock_session.commit.assert_called()
    
    app.dependency_overrides = {}

def test_generate_study_guide_no_transcript_text():
    mock_session = MagicMock()
    mock_transcript = MagicMock()
    mock_transcript.transcript = None # Empty transcript
    
    mock_session.query.return_value.filter.return_value.first.return_value = mock_transcript
    app.dependency_overrides[get_db] = lambda: mock_session
    
    response = client.post("/api/v1/transcript/VID1/en/generate_study_guide")
    assert response.status_code == 400
    assert "Transcript text is empty" in response.json()["detail"]
    
    app.dependency_overrides = {}

def test_generate_study_guide_not_found():
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None
    app.dependency_overrides[get_db] = lambda: mock_session
    
    response = client.post("/api/v1/transcript/VID1/en/generate_study_guide")
    assert response.status_code == 404
    
    app.dependency_overrides = {}
