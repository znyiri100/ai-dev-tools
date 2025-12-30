import os
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class Video(Base):
    __tablename__ = 'videos'

    video_id = Column(String, primary_key=True)
    url = Column(String)
    title = Column(String)
    description = Column(String)
    author = Column(String)
    view_count = Column(String)
    duration = Column(String)
    fetched_at = Column(DateTime, default=func.now())

    transcripts = relationship("Transcript", back_populates="video", cascade="all, delete-orphan")

class Transcript(Base):
    __tablename__ = 'transcripts'

    video_id = Column(String, ForeignKey('videos.video_id'), primary_key=True)
    language = Column(String)
    language_code = Column(String, primary_key=True)
    is_generated = Column(Boolean, primary_key=True)
    is_translatable = Column(Boolean)
    transcript = Column(Text)

    video = relationship("Video", back_populates="transcripts")

def get_db_url():
    """
    Constructs the database URL based on environment variables.
    Defaults to local DuckDB if POSTGRES_HOST is not set.
    """
    host = os.environ.get("POSTGRES_HOST")
    if host:
        user = os.environ.get("POSTGRES_USER")
        password = os.environ.get("POSTGRES_PASSWORD")
        port = os.environ.get("POSTGRES_PORT", "5432")
        db_name = os.environ.get("POSTGRES_DATABASE", "postgres")
        # Construct Postgres URL
        return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    
    # Default to local DuckDB
    return "duckdb:///youtube_data.duckdb"

def get_engine():
    return create_engine(get_db_url())

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def init_db():
    """Creates tables if they don't exist."""
    engine = get_engine()
    Base.metadata.create_all(engine)
