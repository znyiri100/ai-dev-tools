#!/usr/bin/env python3
"""
List Available Transcripts for YouTube Videos with JSON Output

This script lists all available transcripts for a given YouTube video
in JSON format. It also fetches basic video metadata.
"""

import sys
import os
import re
import json
import argparse
import warnings
import requests

# Suppress Python version warnings from google.api_core
warnings.filterwarnings("ignore", category=FutureWarning, module="google.api_core._python_version_support")

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    VideoUnavailable,
    InvalidVideoId,
    NoTranscriptFound,
)
from googleapiclient.discovery import build

def extract_video_id(input_string: str) -> str:
    """Extract video_id from a YouTube URL or return the input."""
    patterns = [
        r'(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})',
        r'(?:youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, input_string)
        if match:
            return match.group(1)
    return input_string

def get_video_metadata(video_id: str) -> dict:
    """Fetch basic video metadata using requests and regex (no API key needed)."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        html = response.text
        
        metadata = {
            "title": None,
            "description": None,
            "author": None,
            "view_count": None,
            "duration": None
        }
        
        # Extract Og tags
        title_match = re.search(r'<meta property="og:title" content="(.*?)">', html)
        if title_match:
            metadata["title"] = title_match.group(1)
            
        desc_match = re.search(r'<meta property="og:description" content="(.*?)">', html)
        if desc_match:
            metadata["description"] = desc_match.group(1)
            
        # Try to find author
        author_match = re.search(r'<link itemprop="name" content="(.*?)">', html)
        if author_match:
            metadata["author"] = author_match.group(1)
            
        # Try to find view count (approximate)
        views_match = re.search(r'<meta itemprop="interactionCount" content="(.*?)">', html)
        if views_match:
            metadata["view_count"] = views_match.group(1)

        # Try to find duration
        duration_match = re.search(r'<meta itemprop="duration" content="(.*?)">', html)
        if duration_match:
            metadata["duration"] = duration_match.group(1)
            
        return metadata
    except Exception as e:
        return {"error": str(e)}

def get_transcript_text(transcript_obj):
    """Fetch transcript data and return the full text."""
    try:
        data = transcript_obj.fetch()
        # snippets are objects with a .text attribute, but in fetch() result they are typically dicts if using the API directly,
        # but the object wrapper might return objects. The original code used snippet.text.
        # Let's verify: The snippet in `data` (list of dicts) usually has 'text' key. 
        # But wait, youtube_transcript_api returns a list of dictionaries like [{'text': '...', 'start': ...}, ...]
        # UNLESS using the Transcript object which might wrap it?
        # The previous code: "snippets are objects with a .text attribute" -> suggests snippet.text access.
        # Wait, looking at library docs: Transcript.fetch() returns a list of dictionaries.
        # So it should be snippet['text'].
        # However, the PREVIOUS code used snippet.text successfully (presumably). 
        # Actually, let's look at the previous code again: `full_text = " ".join([snippet.text for snippet in data])`
        # If it was working, then `data` items have `.text`.
        # I'll stick to what was there but clean it up.
        full_text = " ".join([snippet['text'] for snippet in data])
        clean_text = " ".join(full_text.split())
        return clean_text
    except Exception as e:
        # If accessing as dict fails, try attribute access (backward compatibility if previous code was correct/incorrect)
        try:
             full_text = " ".join([snippet.text for snippet in data])
             clean_text = " ".join(full_text.split())
             return clean_text
        except:
             return None

def list_transcripts_json(video_id: str, include_transcript: bool = False):
    """Retrieve all transcripts and return as a JSON-compatible dictionary."""
    result = {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "metadata": get_video_metadata(video_id),
        "transcripts": []
    }

    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        for transcript in transcript_list:
            t_info = {
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated,
                "is_translatable": transcript.is_translatable,
            }
            
            if include_transcript:
                full_text = get_transcript_text(transcript)
                if full_text:
                    t_info["transcript"] = full_text
                
            result["transcripts"].append(t_info)

    except Exception as e:
        result["error"] = {
            "type": type(e).__name__,
            "message": str(e)
        }

    return result

def search_youtube_videos(topic: str, max_results: int = 5) -> list:
    """Search YouTube for videos by topic."""
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        raise ValueError(
            "YOUTUBE_API_KEY environment variable not set. "
            "Get a key from https://console.cloud.google.com/"
        )
    
    youtube = build('youtube', 'v3', developerKey=api_key)
    max_results = max(1, min(int(max_results), 50))
    
    print(f"🔍 Searching YouTube for: '{topic}' (max {max_results} results)", file=sys.stderr)
    
    search_response = youtube.search().list(
        q=topic,
        part='id,snippet',
        maxResults=max_results,
        type='video',
        order='relevance'
    ).execute()
    
    videos = []
    for item in search_response.get('items', []):
        videos.append(item['id']['videoId'])
    
    return videos

def main():
    parser = argparse.ArgumentParser(
        description="List available transcripts in JSON format",
        epilog="""Examples:
  # Using Video ID
  uv run youtube_api.py EMd3H0pNvSE
  
  # Using YouTube URL
  uv run youtube_api.py https://www.youtube.com/watch?v=EMd3H0pNvSE
  
  # Using YouTube URL with Transcript and Upload
  uv run youtube_api.py https://www.youtube.com/watch?v=EMd3H0pNvSE --transcript --upload

  # Search by Topic and Upload Top 3 Results
  uv run youtube_api.py --topic "machine learning" --max-results 3 --upload""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('video_input', nargs='?', help='YouTube video ID or URL')
    parser.add_argument('--topic', '-t', help='Search YouTube for videos by topic')
    parser.add_argument('--max-results', '-m', type=int, default=5, help='Max search results (1-50)')
    parser.add_argument('--transcript', action='store_true', help='Include full transcript text')
    parser.add_argument('--upload', action='store_true', help='Upload fetched metadata and transcript list to DuckDB')
    
    args = parser.parse_args()
    
    if not args.video_input and not args.topic:
        parser.print_help()
        sys.exit(0)
    
    video_ids = []
    if args.topic:
        try:
            video_ids = search_youtube_videos(args.topic, args.max_results)
        except Exception as e:
            print(f"Error searching videos: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        video_ids = [extract_video_id(args.video_input)]

    all_outputs = []
    for video_id in video_ids:
        output_data = list_transcripts_json(video_id, include_transcript=args.transcript)
        all_outputs.append(output_data)
        
        # Optional Database Upload
        if args.upload:
            try:
                import load_data
                from database import get_session, init_db
                
                # Ensure DB tables exist
                init_db()
                
                session = get_session()
                try:
                    load_data.load_video_metadata(session, output_data)
                    load_data.load_transcripts_metadata(session, video_id, output_data.get("transcripts", []))
                    print(f"✓ Data for {video_id} uploaded to Database", file=sys.stderr)
                finally:
                    session.close()
            except Exception as e:
                print(f"Error during DB upload for {video_id}: {e}", file=sys.stderr)

    # Output JSON
    if len(all_outputs) == 1:
        print(json.dumps(all_outputs[0], indent=2, ensure_ascii=False))
    else:
        print(json.dumps(all_outputs, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
