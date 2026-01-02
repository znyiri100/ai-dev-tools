import os
import pytest
from unittest.mock import patch, MagicMock
from backend.database import Video, Transcript, get_db_url, get_engine, get_session, init_db, Base

def test_video_model():
    """Test Video model instantiation."""
    video = Video(
        video_id="abc12345",
        url="https://youtube.com/watch?v=abc12345",
        title="Test Video",
        description="A test description",
        author="Test Author",
        view_count="1000",
        duration="PT5M"
    )
    assert video.video_id == "abc12345"
    assert video.title == "Test Video"
    assert video.transcripts == []

def test_transcript_model():
    """Test Transcript model instantiation."""
    transcript = Transcript(
        video_id="abc12345",
        language="English",
        language_code="en",
        is_generated=False,
        is_translatable=True,
        transcript="Hello world",
        study_guide="Study guide content",
        quiz="Quiz content"
    )
    assert transcript.video_id == "abc12345"
    assert transcript.language_code == "en"
    assert transcript.transcript == "Hello world"

def test_get_db_url_default():
    """Test get_db_url returns duckdb default when no env vars set."""
    with patch.dict(os.environ, {}, clear=True):
        url = get_db_url()
        assert url == "duckdb:///youtube_data.duckdb"

def test_get_db_url_postgres():
    """Test get_db_url returns postgres url when env vars set."""
    env_vars = {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_USER": "user",
        "POSTGRES_PASSWORD": "password",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DATABASE": "mydb"
    }
    with patch.dict(os.environ, env_vars, clear=True):
        url = get_db_url()
        assert url == "postgresql://user:password@localhost:5432/mydb"

def test_get_db_url_postgres_defaults():
    """Test get_db_url returns postgres url with defaults."""
    env_vars = {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_USER": "user",
        "POSTGRES_PASSWORD": "password"
    }
    with patch.dict(os.environ, env_vars, clear=True):
        url = get_db_url()
        assert url == "postgresql://user:password@localhost:5432/postgres"

@patch('backend.database.create_engine')
def test_get_engine(mock_create_engine):
    """Test get_engine calls sqlalchemy create_engine."""
    get_engine()
    mock_create_engine.assert_called_once()

@patch('backend.database.sessionmaker')
@patch('backend.database.get_engine')
def test_get_session(mock_get_engine, mock_sessionmaker):
    """Test get_session creates and returns a session."""
    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine
    
    mock_session_cls = MagicMock()
    mock_session_instance = MagicMock()
    mock_session_cls.return_value = mock_session_instance
    mock_sessionmaker.return_value = mock_session_cls
    
    session = get_session()
    
    mock_get_engine.assert_called_once()
    mock_sessionmaker.assert_called_once_with(bind=mock_engine)
    mock_session_cls.assert_called_once()
    assert session == mock_session_instance

@patch('backend.database.get_engine')
def test_init_db(mock_get_engine):
    """Test init_db creates tables."""
    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine
    
    # Mock Base.metadata.create_all directly
    # Note: Logic here is a bit tricky since we import Base. 
    # But since we are patching get_engine, we just need to ensure create_all using that engine.
    
    with patch.object(Base.metadata, 'create_all') as mock_create_all:
        init_db()
        mock_get_engine.assert_called_once()
        mock_create_all.assert_called_once_with(mock_engine)
