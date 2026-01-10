import os
import sys
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig, WebshareProxyConfig

def test_proxy(video_id="EMd3H0pNvSE"):
    HTTP_PROXY = os.getenv("HTTP_PROXY")
    HTTP_PROXY_USER = os.getenv("HTTP_PROXY_USER")
    HTTP_PROXY_PASS = os.getenv("HTTP_PROXY_PASS")

    if HTTP_PROXY:

        print(f"Testing with GenericProxyConfig: {HTTP_PROXY}")
        
        try:
            # Configure the proxy
            proxy_config = GenericProxyConfig(http_url=HTTP_PROXY, https_url=HTTP_PROXY)
            
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
                full_text = " ".join([snippet.text for snippet in data])
                print(f"Snippet: {full_text[:200]}...")
                break
                
            print("✅ Success! The proxy is working with youtube-transcript-api.")

        except Exception as e:
            print(f"\n❌ Failed to fetch transcripts via proxy: {e}")
            sys.exit(1)
            
    elif HTTP_PROXY_USER and HTTP_PROXY_PASS:
        print("Testing with WebshareProxyConfig user and password")
        
        try:
            # Configure the proxy
            proxy_config = WebshareProxyConfig(proxy_username=HTTP_PROXY_USER, proxy_password=HTTP_PROXY_PASS)
            
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
                full_text = " ".join([snippet.text for snippet in data])
                print(f"Snippet: {full_text[:200]}...")
                break
                
            print("✅ Success! The proxy is working with youtube-transcript-api.")

        except Exception as e:
            print(f"\n❌ Failed to fetch transcripts via proxy: {e}")
            sys.exit(1)
    else:
        print("Testing without Proxy")
        
        try:
            # Initialize the API without proxy
            api = YouTubeTranscriptApi()
            
            # Attempt to list transcripts
            print(f"Fetching transcripts for {video_id}...")
            transcript_list = api.list(video_id)
            
            for transcript in transcript_list:
                print(f"Found transcript: {transcript.language} ({transcript.language_code})")
                
                # Fetch the actual transcript content
                print("Fetching transcript text...")
                data = transcript.fetch()
                full_text = " ".join([snippet.text for snippet in data])
                print(f"Snippet: {full_text[:200]}...")
                break
                
            print("✅ Success! The proxy is working with youtube-transcript-api.")

        except Exception as e:
            print(f"\n❌ Failed to fetch transcripts via proxy: {e}")
            sys.exit(1)

if __name__ == "__main__":
    vid = sys.argv[1] if len(sys.argv) > 1 else "EMd3H0pNvSE"
    test_proxy(vid)
