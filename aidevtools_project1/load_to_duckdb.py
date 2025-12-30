#!/usr/bin/env python3
import sys
import json
import duckdb
from datetime import datetime

DB_FILE = "youtube_data.duckdb"

def get_db_connection(db_file=DB_FILE):
    """Establish and return a DuckDB connection."""
    return duckdb.connect(db_file)

def init_db(con):
    """Initialize the database schema."""
    con.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            video_id VARCHAR PRIMARY KEY,
            url VARCHAR,
            title VARCHAR,
            description VARCHAR,
            author VARCHAR,
            view_count VARCHAR,
            duration VARCHAR,
            fetched_at TIMESTAMP
        );
    """)
    
    # Check if transcripts table exists
    tables = con.execute("SHOW TABLES").fetchall()
    table_names = [t[0] for t in tables]
    
    if 'transcripts' in table_names:
        # Check columns to see if migration is needed
        columns = con.execute("DESCRIBE transcripts").fetchall()
        col_names = [c[0] for c in columns]
        
        if 'transcript_text' in col_names:
            print("Migrating schema: Renaming transcript_text to transcript...", file=sys.stderr)
            con.execute("ALTER TABLE transcripts RENAME COLUMN transcript_text TO transcript")
            
        if 'preview' in col_names:
            print("Migrating schema: Dropping preview column...", file=sys.stderr)
            con.execute("ALTER TABLE transcripts DROP COLUMN preview")
            
    # Create table if it doesn't exist (with new schema)
    con.execute("""
        CREATE TABLE IF NOT EXISTS transcripts (
            video_id VARCHAR,
            language VARCHAR,
            language_code VARCHAR,
            is_generated BOOLEAN,
            is_translatable BOOLEAN,
            transcript VARCHAR, 
            FOREIGN KEY (video_id) REFERENCES videos(video_id),
            PRIMARY KEY (video_id, language_code, is_generated)
        );
    """)

def load_video_metadata(con, video_data):
    """
    Load video metadata into the 'videos' table.
    
    Args:
        con: DuckDB connection object.
        video_data: Dictionary containing video info (video_id, url, metadata).
    """
    video_id = video_data.get("video_id")
    meta = video_data.get("metadata", {})
    
    con.execute("""
        INSERT OR REPLACE INTO videos (video_id, url, title, description, author, view_count, duration, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        video_id,
        video_data.get("url"),
        meta.get("title"),
        meta.get("description"),
        meta.get("author"),
        meta.get("view_count"),
        meta.get("duration"),
        datetime.now()
    ))
    print(f"✓ Upserted video metadata for ID: {video_id}")

def load_transcripts_metadata(con, video_id, transcripts_list):
    """
    Load transcript metadata (availability, language) into the 'transcripts' table.
    Does NOT overwrite existing full 'transcript' if it exists, unless specified.
    
    Args:
        con: DuckDB connection object.
        video_id: The ID of the video.
        transcripts_list: List of transcript dictionaries from youtube_api.py.
    """
    if not transcripts_list:
        print(f"  No transcripts metadata to load for {video_id}")
        return

    for t in transcripts_list:
        transcript_content = t.get("transcript")
        
        con.execute("""
            INSERT INTO transcripts (video_id, language, language_code, is_generated, is_translatable, transcript)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (video_id, language_code, is_generated) DO UPDATE SET
                language = EXCLUDED.language,
                is_translatable = EXCLUDED.is_translatable,
                transcript = COALESCE(EXCLUDED.transcript, transcripts.transcript)
        """, (
            video_id,
            t.get("language"),
            t.get("language_code"),
            t.get("is_generated"),
            t.get("is_translatable"),
            transcript_content
        ))
    
    print(f"✓ Processed {len(transcripts_list)} transcript records for ID: {video_id}")

def update_transcript_text(con, video_id, language_code, is_generated, full_text):
    """
    Update the full text content of a specific transcript, creating the row if needed.
    
    Args:
        con: DuckDB connection object.
        video_id: Video ID.
        language_code: Language code (e.g., 'en').
        is_generated: Boolean indicating if it is auto-generated.
        full_text: The full transcript text string.
    """
    # First ensure the video exists to satisfy Foreign Key constraint if possible
    # We might not have metadata, but we can try to insert a placeholder video row if it doesn't exist
    try:
        con.execute("INSERT INTO videos (video_id, fetched_at) VALUES (?, ?) ON CONFLICT DO NOTHING", (video_id, datetime.now()))
    except Exception:
        pass # Ignore if this fails, likely constraints or other issues, let the main insert fail if it must

    con.execute("""
        INSERT INTO transcripts (video_id, language, language_code, is_generated, is_translatable, transcript)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT (video_id, language_code, is_generated) DO UPDATE SET
            transcript = EXCLUDED.transcript
    """, (
        video_id,
        language_code, # Use code as fallback language name
        language_code,
        is_generated,
        False, # Default
        full_text
    ))
    
    print(f"✓ Upserted transcript text for {video_id} ({language_code}, auto={is_generated})")

def process_stdin_data():
    """Read JSON from stdin and utilize the loading functions."""
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            return

        data = json.loads(input_data)
        if "error" in data:
            print(f"Skipping load due to input error: {data['error']}")
            return

        con = get_db_connection()
        init_db(con)

        # 1. Load Video Info
        load_video_metadata(con, data)

        # 2. Load Transcript Metadata (list of available languages)
        video_id = data.get("video_id")
        transcripts = data.get("transcripts", [])
        load_transcripts_metadata(con, video_id, transcripts)

        con.close()

    except json.JSONDecodeError:
        print("Error: Invalid JSON input.")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # If run as script with piped input, process it
    if not sys.stdin.isatty():
        process_stdin_data()
    else:
        # If run directly without input, just initialize DB
        con = get_db_connection()
        init_db(con)
        con.close()
        print("Database initialized.")
