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
    study_guide: Optional[str] = None
    quiz: Optional[str] = None

class VideoResponse(BaseModel):
    video_id: str
    url: str
    metadata: VideoMetadata
    transcripts: List[TranscriptInfo]

class StoreResponse(BaseModel):
    message: str
    video_id: str

class GenerateResponse(BaseModel):
    message: str
    content: str

# --- Dependency ---
def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()

import llm_utils

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, Any]]

@app.post("/api/v1/transcript/{video_id}/{language_code}/chat", response_model=GenerateResponse)
def chat_with_study_guide_endpoint(video_id: str, language_code: str, request: ChatRequest, db: Session = Depends(get_db)):
    # Order by is_generated descending to match generation priority
    transcript = db.query(DbTranscript).filter(
        DbTranscript.video_id == video_id,
        DbTranscript.language_code == language_code
    ).order_by(DbTranscript.is_generated.desc()).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    if not transcript.study_guide:
        raise HTTPException(status_code=400, detail="Study guide not generated yet. Please generate it first.")

    content = llm_utils.chat_with_study_guide(transcript.study_guide, request.message, request.history)
    
    if content.startswith("Error"):
        raise HTTPException(status_code=500, detail=content)
    
    return {"message": "Chat response generated", "content": content}

class GenerateRequest(BaseModel):
    prompt: Optional[str] = None

class UpdateContentRequest(BaseModel):
    study_guide: Optional[str] = None
    quiz: Optional[str] = None

@app.put("/api/v1/transcript/{video_id}/{language_code}/update")
def update_transcript_content(
    video_id: str, 
    language_code: str, 
    request: UpdateContentRequest,
    db: Session = Depends(get_db)
):
    """
    Update study guide and/or quiz content for a transcript without regenerating.
    """
    transcript = db.query(DbTranscript).filter(
        DbTranscript.video_id == video_id,
        DbTranscript.language_code == language_code
    ).order_by(DbTranscript.is_generated.desc()).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    # Update fields if provided
    if request.study_guide is not None:
        transcript.study_guide = request.study_guide
    if request.quiz is not None:
        transcript.quiz = request.quiz
    
    db.commit()
    
    return {"message": "Content updated successfully"}


@app.post("/api/v1/transcript/{video_id}/{language_code}/generate_study_guide", response_model=GenerateResponse)
def generate_study_guide_endpoint(video_id: str, language_code: str, request: GenerateRequest = None, db: Session = Depends(get_db)):
    # Order by is_generated descending so True (1) comes before False (0)
    transcript = db.query(DbTranscript).filter(
        DbTranscript.video_id == video_id,
        DbTranscript.language_code == language_code
    ).order_by(DbTranscript.is_generated.desc()).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
        
    if not transcript.transcript:
         raise HTTPException(status_code=400, detail="Transcript text is empty")

    prompt = request.prompt if request else None
    content = llm_utils.generate_study_guide(transcript.transcript, prompt=prompt)
    
    if content.startswith("Error"):
         raise HTTPException(status_code=500, detail=content)

    transcript.study_guide = content
    db.commit()
    
    return {"message": "Study Guide generated successfully", "content": content}

@app.post("/api/v1/transcript/{video_id}/{language_code}/generate_quiz", response_model=GenerateResponse)
def generate_quiz_endpoint(video_id: str, language_code: str, request: GenerateRequest = None, db: Session = Depends(get_db)):
    # Order by is_generated descending so True (1) comes before False (0)
    transcript = db.query(DbTranscript).filter(
        DbTranscript.video_id == video_id,
        DbTranscript.language_code == language_code
    ).order_by(DbTranscript.is_generated.desc()).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
        
    if not transcript.transcript:
         raise HTTPException(status_code=400, detail="Transcript text is empty")

    prompt = request.prompt if request else None
    content = llm_utils.generate_quiz(transcript.transcript, prompt=prompt)

    if content.startswith("Error"):
         raise HTTPException(status_code=500, detail=content)
    
    transcript.quiz = content
    db.commit()
    
    return {"message": "Quiz generated successfully", "content": content}


@app.get("/api/v1/video/{video_id}", response_model=VideoResponse)
def get_video_info(video_id: str, include_transcript: bool = False):
    """
    Fetch video metadata and available transcripts directly from YouTube.
    """
    print(f"DEBUG: API get_video_info video_id={video_id} include_transcript={include_transcript}")
    real_id = youtube_api.extract_video_id(video_id)
    data = youtube_api.list_transcripts_json(real_id, include_transcript=include_transcript)
    
    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"])
        
    return data

@app.post("/api/v1/video/{video_id}/store", response_model=StoreResponse)
def store_video_data(video_id: str, include_transcript: bool = True, background_tasks: BackgroundTasks = None, db: Session = Depends(get_db)):
    """
    Fetch data from YouTube and store it in the database.
    """
    real_id = youtube_api.extract_video_id(video_id)
    
    # Fetch data
    data = youtube_api.list_transcripts_json(real_id, include_transcript=include_transcript)
    
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

@app.get("/api/v1/db/video/{video_id}", response_model=VideoResponse)
def get_stored_video(video_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a specific video and its transcripts from the database.
    """
    video = db.query(DbVideo).filter(DbVideo.video_id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found in DB")
    
    ts = []
    for t in video.transcripts:
        ts.append({
            "language": t.language,
            "language_code": t.language_code,
            "is_generated": t.is_generated,
            "is_translatable": t.is_translatable,
            "transcript": t.transcript,
            "study_guide": t.study_guide,
            "quiz": t.quiz
        })
        
    return {
        "video_id": video.video_id,
        "url": video.url,
        "metadata": {
            "title": video.title,
            "description": video.description,
            "author": video.author,
            "view_count": video.view_count,
            "duration": video.duration
        },
        "transcripts": ts
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
