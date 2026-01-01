import argparse
import json
import yt_dlp

def search_videos(topic, limit=5):
    """
    Search for videos on YouTube by topic using yt-dlp.
    
    Args:
        topic (str): The search topic.
        limit (int): Number of results to return.
        
    Returns:
        list: A list of dictionaries containing video info (id, title, link, etc.).
    """
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'force_generic_extractor': False,
    }

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
                        'link': entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}",
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
