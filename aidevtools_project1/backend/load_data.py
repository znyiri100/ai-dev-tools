#!/usr/bin/env python3
import sys
from datetime import datetime
from database import get_session, init_db, Video, Transcript

def load_video_metadata(session, video_data):
    """
    Load video metadata into the 'videos' table.
    """
    video_id = video_data.get("video_id")
    meta = video_data.get("metadata", {})
    
    # Use merge for upsert behavior (insert or update)
    video = Video(
        video_id=video_id,
        url=video_data.get("url"),
        title=meta.get("title"),
        description=meta.get("description"),
        author=meta.get("author"),
        view_count=meta.get("view_count"),
        duration=meta.get("duration"),
        fetched_at=datetime.now()
    )
    
    session.merge(video)
    session.commit()
    print(f"✓ Upserted video metadata for ID: {video_id}")

def load_transcripts_metadata(session, video_id, transcripts_list):
    """
    Load transcript metadata.
    """
    if not transcripts_list:
        print(f"  No transcripts metadata to load for {video_id}")
        return

    for t in transcripts_list:
        lang_code = t.get("language_code")
        is_generated = t.get("is_generated")
        
        # Check if exists
        existing = session.query(Transcript).filter_by(
            video_id=video_id,
            language_code=lang_code,
            is_generated=is_generated
        ).first()

        transcript_text = t.get("transcript")

        if existing:
            existing.language = t.get("language")
            existing.is_translatable = t.get("is_translatable")
            # Only update transcript text if new one is provided (not None/Empty) or if we want to overwrite
            if transcript_text:
                 existing.transcript = transcript_text
        else:
            new_transcript = Transcript(
                video_id=video_id,
                language=t.get("language"),
                language_code=lang_code,
                is_generated=is_generated,
                is_translatable=t.get("is_translatable"),
                transcript=transcript_text
            )
            session.add(new_transcript)
    
    session.commit()
    print(f"✓ Loaded {len(transcripts_list)} transcript records for {video_id}")

def update_transcript_text(session, video_id, language_code, is_generated, transcript_text):
    """
    Update the transcript text for a specific record.
    """
    transcript = session.query(Transcript).filter_by(
        video_id=video_id,
        language_code=language_code,
        is_generated=is_generated
    ).first()
    
    if transcript:
        transcript.transcript = transcript_text
        session.commit()
        print(f"✓ Updated transcript text for {video_id} ({language_code})")
    else:
        # If it doesn't exist, we create a stub record
        print(f"  Transcript record not found for {video_id}, creating new one...")
        new_transcript = Transcript(
            video_id=video_id,
            language_code=language_code,
            is_generated=is_generated,
            transcript=transcript_text,
            is_translatable=False # Default
        )
        session.add(new_transcript)
        session.commit()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
