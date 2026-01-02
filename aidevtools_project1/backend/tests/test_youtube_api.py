import pytest
import os
from unittest.mock import patch, MagicMock
from backend.youtube_api import (
    extract_video_id,
    get_video_metadata,
    get_transcript_text,
    list_transcripts_json,
    search_youtube_videos
)

def test_extract_video_id():
    """Test extracting video ID from various URL formats."""
    assert extract_video_id("https://www.youtube.com/watch?v=12345678901") == "12345678901"
    assert extract_video_id("https://youtu.be/12345678901") == "12345678901"
    assert extract_video_id("https://www.youtube.com/embed/12345678901") == "12345678901"
    assert extract_video_id("12345678901") == "12345678901"
    assert extract_video_id("invalid") == "invalid"

@patch('yt_dlp.YoutubeDL')
def test_get_video_metadata_ytdlp(mock_ydl):
    """Test getting video metadata using yt-dlp."""
    mock_instance = mock_ydl.return_value.__enter__.return_value
    mock_instance.extract_info.return_value = {
        "title": "Test Video",
        "description": "Test Description",
        "uploader": "Test Author",
        "view_count": 100,
        "duration": 300
    }
    
    metadata = get_video_metadata("12345678901")
    
    assert metadata["title"] == "Test Video"
    assert metadata["description"] == "Test Description"
    assert metadata["author"] == "Test Author"
    assert metadata["view_count"] == "100"
    assert metadata["duration"] == "PT300S"

@patch('yt_dlp.YoutubeDL')
@patch('backend.youtube_api.requests.get')
def test_get_video_metadata_fallback(mock_get, mock_ydl):
    """Test getting video metadata fallback when yt-dlp fails."""
    # Simulate yt-dlp failure
    mock_ydl.side_effect = Exception("yt-dlp error")
    
    # Mock requests.get response
    mock_response = MagicMock()
    mock_response.text = '<html><meta property="og:title" content="Fallback Title"></html>'
    mock_get.return_value = mock_response
    
    metadata = get_video_metadata("12345678901")
    
    # We only mocked title in regex for simplicity, check if it extracted 'Fallback Title'
    # Note: real HTML parsing depends on specific meta tags. 
    # This test assumes the fallback logic works with regex on 'og:title'.
    assert metadata["title"] == "Fallback Title"

def test_get_transcript_text_list():
    """Test extracting text from list of snippets."""
    mock_transcript = MagicMock()
    mock_transcript.fetch.return_value = [
        {'text': 'Hello'}, {'text': 'world'}
    ]
    
    text = get_transcript_text(mock_transcript)
    assert text == "Hello world"

def test_get_transcript_text_obj():
    """Test extracting text from list of objects."""
    mock_snippet1 = MagicMock()
    mock_snippet1.text = 'Hello'
    mock_snippet2 = MagicMock()
    mock_snippet2.text = 'world'
    
    mock_transcript = MagicMock()
    mock_transcript.fetch.return_value = [mock_snippet1, mock_snippet2]
    
    text = get_transcript_text(mock_transcript)
    assert text == "Hello world"

@patch('backend.youtube_api.YouTubeTranscriptApi')
@patch('backend.youtube_api.get_video_metadata')
def test_list_transcripts_json(mock_metadata, mock_api):
    """Test listing transcripts JSON."""
    mock_metadata.return_value = {"title": "Test"}
    
    mock_transcript = MagicMock()
    mock_transcript.language = "English"
    mock_transcript.language_code = "en"
    mock_transcript.is_generated = False
    mock_transcript.is_translatable = True
    
    # Mock list method on instance if instantiated, OR directly on class if static
    # checking source, it's api.list(video_id) where api is instance of YouTubeTranscriptApi()
    # BUT wait, checking source again: 
    # api = YouTubeTranscriptApi() ... transcript_list = api.list(video_id)
    # Actually YouTubeTranscriptApi.list is usually a static method but here it is used as instance?
    # Let's check source code again.
    # source: api = YouTubeTranscriptApi() ... transcript_list = api.list(video_id)
    # The source code instantiates it. 
    
    mock_api_instance = mock_api.return_value
    mock_api_instance.list.return_value = [mock_transcript]
    
    result = list_transcripts_json("12345678901")
    
    assert result["video_id"] == "12345678901"
    assert len(result["transcripts"]) == 1
    assert result["transcripts"][0]["language_code"] == "en"

@patch('backend.youtube_api.build')
@patch.dict(os.environ, {"YOUTUBE_API_KEY": "fake_key"})
def test_search_youtube_videos(mock_build):
    """Test searching YouTube videos."""
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    
    mock_search = mock_service.search.return_value
    mock_list = mock_search.list.return_value
    mock_list.execute.return_value = {
        "items": [
            {"id": {"videoId": "vid1"}},
            {"id": {"videoId": "vid2"}}
        ]
    }
    
    videos = search_youtube_videos("term", 2)
    assert videos == ["vid1", "vid2"]
