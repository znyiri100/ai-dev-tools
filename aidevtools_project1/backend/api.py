from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import youtube_api
import load_data
from database import get_session, init_db, Video as DbVideo, Transcript as DbTranscript
from sqlalchemy.orm import Session

from contextlib import asynccontextmanager

# --- Events ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown logic can go here if needed

app = FastAPI(title="YouTube Transcript API", version="1.0.0", lifespan=lifespan)

# --- Pydantic Models ---
class VideoMetadata(BaseModel):
    title: Optional[str]
    description: Optional[str]
    author: Optional[str]
    view_count: Optional[str]
    duration: Optional[str]

class TranscriptInfo(BaseModel):
    language: Optional[str]
    language_code: Optional[str]
    is_generated: Optional[bool]
    is_translatable: Optional[bool]
    transcript: Optional[str] = None

class VideoResponse(BaseModel):
    video_id: str
    url: str
    metadata: VideoMetadata
    transcripts: List[TranscriptInfo]

class StoreResponse(BaseModel):
    message: str
    video_id: str

# --- Dependency ---
def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()



@app.get("/api/v1/video/{video_id}", response_model=VideoResponse)
def get_video_info(video_id: str, include_transcript: bool = False):
    """
    Fetch video metadata and available transcripts directly from YouTube.
    """
    real_id = youtube_api.extract_video_id(video_id)
    data = youtube_api.list_transcripts_json(real_id, include_transcript=include_transcript)
    
    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"])
        
    return data

@app.post("/api/v1/video/{video_id}/store", response_model=StoreResponse)
def store_video_data(video_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Fetch data from YouTube and store it in the database.
    This happens in the background? No, let's do it synchronously for simplicity, 
    or use background tasks if it takes too long. 
    Given it's a prototype, synchronous is fine for immediate feedback, 
    but fetching transcripts can be slow. Let's do it synchronously to return success/fail.
    """
    real_id = youtube_api.extract_video_id(video_id)
    
    # Fetch data
    data = youtube_api.list_transcripts_json(real_id, include_transcript=True) # Store usually implies full content
    
    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"])

    try:
        load_data.load_video_metadata(db, data)
        # Note: list_transcripts_json structure matches what load_transcripts_metadata expects
        load_data.load_transcripts_metadata(db, real_id, data.get("transcripts", []))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"message": "Video data and transcripts stored successfully", "video_id": real_id}

@app.get("/api/v1/db/videos")
def list_stored_videos(db: Session = Depends(get_db)):
    """
    List all videos currently stored in the database.
    """
    videos = db.query(DbVideo).all()
    results = []
    for v in videos:
        results.append({
            "video_id": v.video_id,
            "title": v.title,
            "fetched_at": v.fetched_at
        })
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
