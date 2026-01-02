import pytest
from unittest.mock import MagicMock
from datetime import datetime
from backend.load_data import load_video_metadata, load_transcripts_metadata, update_transcript_text
from database import Video, Transcript

def test_load_video_metadata():
    """Test loading video metadata into database."""
    session = MagicMock()
    video_data = {
        "video_id": "abc",
        "url": "http://example.com",
        "metadata": {
            "title": "Title",
            "description": "Desc",
            "author": "Author",
            "view_count": "100",
            "duration": "PT1M"
        }
    }
    
    load_video_metadata(session, video_data)
    
    session.merge.assert_called_once()
    session.commit.assert_called_once()
    
    # Check the call args to verify data
    args, _ = session.merge.call_args
    video_obj = args[0]
    assert isinstance(video_obj, Video)
    assert video_obj.video_id == "abc"
    assert video_obj.title == "Title"

def test_load_transcripts_metadata_new():
    """Test loading new transcript metadata."""
    session = MagicMock()
    video_id = "abc"
    transcripts_list = [{
        "language_code": "en",
        "is_generated": False,
        "language": "English",
        "is_translatable": True,
        "transcript": "Content"
    }]
    
    # query().filter_by().first() returns None -> new record
    session.query.return_value.filter_by.return_value.first.return_value = None
    
    load_transcripts_metadata(session, video_id, transcripts_list)
    
    session.add.assert_called_once()
    session.commit.assert_called_once()
    
    args, _ = session.add.call_args
    t_obj = args[0]
    assert isinstance(t_obj, Transcript)
    assert t_obj.video_id == "abc"
    assert t_obj.transcript == "Content"

def test_load_transcripts_metadata_update():
    """Test updating existing transcript metadata."""
    session = MagicMock()
    video_id = "abc"
    transcripts_list = [{
        "language_code": "en",
        "is_generated": False,
        "language": "English",
        "is_translatable": True,
        "transcript": "New Content"
    }]
    
    # Mock existing record
    existing_transcript = MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value = existing_transcript
    
    load_transcripts_metadata(session, video_id, transcripts_list)
    
    session.add.assert_not_called()
    session.commit.assert_called_once()
    
    assert existing_transcript.transcript == "New Content"

def test_update_transcript_text_existing():
    """Test updating transcript text for existing record."""
    session = MagicMock()
    existing_transcript = MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value = existing_transcript
    
    update_transcript_text(session, "abc", "en", False, "Updated Text")
    
    assert existing_transcript.transcript == "Updated Text"
    session.commit.assert_called_once()

def test_update_transcript_text_new():
    """Test updating transcript text when record missing (creates new)."""
    session = MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value = None
    
    update_transcript_text(session, "abc", "en", False, "New text")
    
    session.add.assert_called_once()
    session.commit.assert_called_once()
