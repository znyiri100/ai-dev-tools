import argparse
import json
import yt_dlp
import shutil
import sys

class YtDlpLogger:
    def debug(self, msg):
        pass
    def warning(self, msg):
        if "Remote component" in msg or "n challenge solving failed" in msg or "Ignoring unsupported" in msg:
            return
        print(f"WARNING: {msg}")
    def error(self, msg):
        print(f"ERROR: {msg}")

def search_videos(topic, limit=5):
    """
    Search for videos on YouTube by topic using yt-dlp.
    
    Args:
        topic (str): The search topic.
        limit (int): Number of results to return.
        
    Returns:
        list: A list of dictionaries containing video info (id, title, link, etc.).
    """
    node_path = shutil.which('node')
    print(f"DEBUG: node_path found: {node_path}")
    ydl_opts = {
        'quiet': False,
        'skip_download': True,
        'force_generic_extractor': False,
        'logger': YtDlpLogger(),
    }
    
    if node_path:
        ydl_opts['js_runtimes'] = {'node': {'args': [node_path]}}
        print(f"DEBUG: Configured js_runtimes with node: {node_path}")
    else:
        print("DEBUG: Node not found, skipping js_runtimes configuration")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ytsearchN:query searches for N results
            search_query = f"ytsearch{limit}:{topic}"
            result = ydl.extract_info(search_query, download=False)
            
            videos = []
            if 'entries' in result:
                for entry in result['entries']:
                    videos.append({
                        'id': entry.get('id'),
                        'title': entry.get('title'),
                        'uploader': entry.get('uploader') or entry.get('channel') or 'Unknown',
                        'description': entry.get('description') or '',
                        'link': entry.get('webpage_url') or f"https://www.youtube.com/watch?v={entry.get('id')}",
                        'duration': entry.get('duration'),
                        'viewCount': entry.get('view_count'),
                        'publishedTime': entry.get('upload_date') # yt-dlp gives upload_date usually
                    })
            return videos
            
    except Exception as e:
        # import traceback
        # traceback.print_exc()
        return [{"error": str(e)}]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search YouTube videos by topic.")
    parser.add_argument("--topic", type=str, required=True, help="Topic to search for")
    parser.add_argument("--limit", type=int, default=5, help="Number of results to return")
    
    args = parser.parse_args()
    
    results = search_videos(args.topic, args.limit)
    print(json.dumps(results, indent=2))
