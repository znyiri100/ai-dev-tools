import asyncio
import sys
import logging
import re
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Default Configuration
DEFAULT_VIDEO_URL = "https://www.youtube.com/watch?v=EMd3H0pNvSE"

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

def print_usage():
    print("Usage: uv run youtube_mcp.py [VIDEO_URL] [OPTIONS]")
    print("\nOptions:")
    print("  --info         Fetch and display video information")
    print("  --transcript   Fetch and display the video transcript")
    print("  --upload       Upload fetched transcript text to DuckDB")
    print("  --verbose      Show internal logs and progress messages")
    print("\nExample:")
    print(f"  uv run youtube_mcp.py {DEFAULT_VIDEO_URL} --info --transcript --upload")

async def main():
    args = sys.argv[1:]
    
    video_url = None
    show_info = False
    show_transcript = False
    upload = False
    verbose = False

    # Extract URL if present
    positional_args = [a for a in args if not a.startswith("--")]
    if positional_args:
        raw_input = positional_args[0]
        # Normalize input: extract ID and reconstruct URL
        video_id = extract_video_id(raw_input)
        video_url = f"https://www.youtube.com/watch?v={video_id}"
    else:
        if any(arg in args for arg in ["--info", "--transcript", "--verbose", "--upload"]):
            video_url = DEFAULT_VIDEO_URL

    if "--info" in args:
        show_info = True
    if "--transcript" in args:
        show_transcript = True
    if "--upload" in args:
        upload = True
    if "--verbose" in args:
        verbose = True

    if not (show_info or show_transcript or upload):
        print_usage()
        return

    # Configure logging
    if verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.ERROR)
        logging.getLogger("mcp").setLevel(logging.ERROR)
    
    server_params = StdioServerParameters(
        command="bash",
        args=["-c", f"docker run -i --rm mcp/youtube-transcript {'' if verbose else '2>/dev/null'}"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Get Video Info
            if show_info:
                if verbose:
                    print(f"\n--- Video Info ---")
                try:
                    info_result = await session.call_tool(
                        "get_video_info",
                        arguments={"url": video_url}
                    )
                    print(info_result.content[0].text) 
                except Exception as e:
                    print(f"Error fetching info: {e}")

            # 2. Get Transcript
            if show_transcript or upload:
                if verbose:
                    print(f"\n--- Transcript ---")
                try:
                    transcript_result = await session.call_tool(
                        "get_transcript",
                        arguments={"url": video_url}
                    )
                    transcript_text = transcript_result.content[0].text
                    
                    if show_transcript:
                        if verbose:
                            print(f"Preview:\n{transcript_text[:300]}...")
                        else:
                            print(transcript_text)
                    
                    if upload:
                        try:
                            import load_to_duckdb
                            video_id = extract_video_id(video_url)
                            con = load_to_duckdb.get_db_connection()
                            
                            # Initialize tables to ensure they exist
                            load_to_duckdb.init_db(con)
                            
                            # We update the 'en' transcript by default. 
                            # Since we don't know if it's generated or not for sure from the tool, 
                            # we'll try to update the manual one first, then the generated one.
                            load_to_duckdb.update_transcript_text(con, video_id, 'en', False, transcript_text)
                            load_to_duckdb.update_transcript_text(con, video_id, 'en', True, transcript_text)
                            con.close()
                            print(f"✓ Transcript text uploaded to DuckDB for {video_id}", file=sys.stderr)
                        except ImportError:
                            print("Error: load_to_duckdb.py not found.", file=sys.stderr)
                        except Exception as db_e:
                            print(f"Error uploading to DB: {db_e}", file=sys.stderr)

                except Exception as e:
                    print(f"Error fetching transcript: {e}")

if __name__ == "__main__":
    asyncio.run(main())
