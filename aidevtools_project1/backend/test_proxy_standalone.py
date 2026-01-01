import os
import sys
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig

def test_proxy(video_id="EMd3H0pNvSE"):
    proxy_url = os.getenv("HTTP_PROXY")
    
    if not proxy_url:
        print("Error: HTTP_PROXY environment variable not set.")
        print("Usage: HTTP_PROXY='http://user:pass@host:port' python test_proxy_standalone.py")
        sys.exit(1)

    print(f"Testing with proxy: {proxy_url}")
    
    try:
        # Configure the proxy
        proxy_config = GenericProxyConfig(http_url=proxy_url, https_url=proxy_url)
        
        # Initialize the API with the proxy config
        api = YouTubeTranscriptApi(proxy_config=proxy_config)
        
        # Attempt to list transcripts
        print(f"Fetching transcripts for {video_id}...")
        transcript_list = api.list(video_id)
        
        for transcript in transcript_list:
            print(f"Found transcript: {transcript.language} ({transcript.language_code})")
            
            # Fetch the actual transcript content
            print("Fetching transcript text...")
            data = transcript.fetch()
            full_text = " ".join([snippet['text'] for snippet in data])
            print(f"Snippet: {full_text[:200]}...")
            break
            
        print("\n✅ Success! The proxy is working with youtube-transcript-api.")

    except Exception as e:
        print(f"\n❌ Failed to fetch transcripts via proxy: {e}")
        sys.exit(1)

if __name__ == "__main__":
    vid = sys.argv[1] if len(sys.argv) > 1 else "EMd3H0pNvSE"
    test_proxy(vid)
