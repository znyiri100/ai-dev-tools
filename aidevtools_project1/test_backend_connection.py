import httpx
import sys

API_BASE = "http://localhost:8000"
VIDEO_ID = "EMd3H0pNvSE" # Known good ID

try:
    print(f"Testing GET {API_BASE}/api/v1/video/{VIDEO_ID}...")
    resp = httpx.get(f"{API_BASE}/api/v1/video/{VIDEO_ID}", params={"include_transcript": "true"})
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print("Success! Data keys:", data.keys())
        print("Metadata:", data.get("metadata", {}).get("title"))
        transcripts = data.get("transcripts", [])
        print(f"Transcripts count: {len(transcripts)}")
        
        if transcripts:
            first_t = transcripts[0]
            txt = first_t.get("transcript")
            print(f"Transcript[0] text length: {len(txt) if txt else 'None'}")
            if txt:
                print(f"Preview: {txt[:50]}...")
    else:
        print("Error response:", resp.text)
except Exception as e:
    print(f"Connection failed: {e}")
    print("Is the backend server running? (cd backend && uv run api.py)")
