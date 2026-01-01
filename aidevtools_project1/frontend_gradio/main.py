import gradio as gr
import httpx
import json
import os
from youtube_api import search_videos

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

def format_transcript(data):
    transcripts = data.get("transcripts", [])
    transcript_text = ""
    for t in transcripts:
        if t.get("transcript"):
            transcript_text += f"--- {t.get('language')} ({t.get('language_code')}) ---\n"
            transcript_text += t.get("transcript") + "\n\n"
    return transcript_text

def process_video(video_id, include_transcript, store_in_db=False):
    print(f"DEBUG: process_video id={video_id}, include_transcript={include_transcript}, store={store_in_db}")
    if not video_id:
        return "Please enter a video ID", ""
    
    video_id = video_id.strip()
    
    try:
        with httpx.Client(timeout=60.0) as client:
            params = {"include_transcript": str(include_transcript).lower()}
            
            if store_in_db:
                # Store (POST)
                print(f"DEBUG: Calling POST {API_BASE}/api/v1/video/{video_id}/store")
                resp = client.post(
                    f"{API_BASE}/api/v1/video/{video_id}/store",
                    params=params
                )
            else:
                # Get Info (GET)
                print(f"DEBUG: Calling GET {API_BASE}/api/v1/video/{video_id}")
                resp = client.get(
                    f"{API_BASE}/api/v1/video/{video_id}", 
                    params=params
                )
            
            print(f"DEBUG: Response Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                transcript_text = format_transcript(data)
                
                if not transcript_text and include_transcript:
                    transcript_text = "(No transcript text returned)"
                
                return json.dumps(data, indent=2), transcript_text
            else:
                return f"Error: {resp.status_code} - {resp.text}", ""
                
    except Exception as e:
        return f"Connection Error: {e}", ""

def search_only(video_id, include_transcript):
    return process_video(video_id, include_transcript, store_in_db=False)

def store_only(video_id, include_transcript):
    # We only return the JSON response to the info box, not transcript box
    json_res, _ = process_video(video_id, include_transcript, store_in_db=True)
    return json_res

def list_db_videos():
    try:
        with httpx.Client() as client:
            resp = client.get(f"{API_BASE}/api/v1/db/videos")
            if resp.status_code == 200:
                data = resp.json()
                # Return list of lists for Dataframe
                return [[v['video_id'], v['title'], v['fetched_at']] for v in data]
            else:
                return [["Error", resp.text, ""]]
    except Exception as e:
        return [["Connection Error", str(e), ""]]

def get_db_video_detail(video_id):
    if not video_id:
        return "Please enter a video ID"
    try:
        with httpx.Client() as client:
            resp = client.get(f"{API_BASE}/api/v1/db/video/{video_id}")
            if resp.status_code == 200:
                return json.dumps(resp.json(), indent=2)
            else:
                return f"Error: {resp.text}"
    except Exception as e:
        return f"Error: {e}"

def search_topic(topic, limit):
    if not topic:
        return []
    results = search_videos(topic, limit=int(limit))
    if results and "error" in results[0]:
         return [[results[0]["error"], "", "", "", ""]]
    
    formatted_results = []
    for r in results:
        link = r.get('link', '')
        # Only the link is markdown for clickability
        md_link = f'<a href="{link}" target="_blank" style="color: blue; text-decoration: underline;">Watch</a>' if link else ""
        formatted_results.append([
            r.get('id'), 
            r.get('title'), 
            r.get('duration'), 
            r.get('viewCount'), 
            md_link
        ])
        
    return formatted_results

with gr.Blocks(title="YouTube Transcript Manager") as app:
    gr.Markdown("# YouTube Transcript Manager")
    
    with gr.Tab("Search & Store"):
        # --- Component Definitions ---
        with gr.Accordion("Topic Search (Find Video IDs)", open=True):
            with gr.Row():
                topic_input = gr.Textbox(label="Topic", placeholder="Python programming...", scale=4)
                limit_input = gr.Number(label="Limit", value=5, precision=0, scale=1)
                btn_topic_search = gr.Button("Search YouTube", variant="primary", scale=1)
            
            topic_results = gr.Dataframe(
                headers=["ID", "Title", "Duration", "Views", "Link"],
                datatype=["str", "str", "str", "str", "html"], # HTML for the Link column
                label="Search Results",
                interactive=False, 
                wrap=True
            )

        gr.Markdown("---")

        with gr.Row():
            vid_input = gr.Textbox(label="Video ID", value="QXE5rEVlu20", scale=4)
            btn_search = gr.Button("Get It", variant="primary", scale=1)
        
        with gr.Row():
            chk_transcript = gr.Checkbox(label="Include Transcript", value=True)
            btn_store = gr.Button("Store in DB", scale=1)
        
        with gr.Row():
            out_info = gr.Code(label="Result JSON", language="json", lines=20)
            out_transcript = gr.Textbox(label="Transcript Text", lines=20, buttons=["copy"])

        # --- Event Handler Definitions ---
        
        btn_topic_search.click(search_topic, [topic_input, limit_input], topic_results)
        topic_input.submit(search_topic, [topic_input, limit_input], topic_results)
        
        def select_topic_video(evt: gr.SelectData):
            if evt.index[1] == 0:  # Check if the click is on the ID column
                return evt.value
            return gr.skip()

        topic_results.select(select_topic_video, None, vid_input)
        
        btn_search.click(search_only, [vid_input, chk_transcript], [out_info, out_transcript])
        vid_input.submit(search_only, [vid_input, chk_transcript], [out_info, out_transcript])
        
        # When storing, we only want to update the JSON output, not the transcript text box
        btn_store.click(store_only, [vid_input, chk_transcript], out_info)

    with gr.Tab("Database"):
        btn_refresh = gr.Button("Refresh List")
        db_table = gr.Dataframe(
            headers=["Video ID", "Title", "Fetched At"], 
            label="Stored Videos",
            interactive=False,
            value=list_db_videos
        )
        
        gr.Markdown("### View Details")
        with gr.Row():
            db_vid_input = gr.Textbox(label="Video ID from DB", scale=4)
            btn_db_detail = gr.Button("Get DB Detail", scale=1)
            
        out_db_detail = gr.Code(label="DB Record JSON", language="json", lines=20)
        
        btn_refresh.click(list_db_videos, outputs=db_table)
        btn_db_detail.click(get_db_video_detail, db_vid_input, out_db_detail)
        
        def select_video(evt: gr.SelectData):
            return evt.value
            
        db_table.select(select_video, None, db_vid_input)

if __name__ == "__main__":
    app.launch()