import gradio as gr
import httpx
import json
import os

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

def get_video_info(video_id, include_transcript):
    print(f"DEBUG: get_video_info called with id={video_id}, include_transcript={include_transcript} (type: {type(include_transcript)})")
    if not video_id:
        return "Please enter a video ID", ""
    try:
        with httpx.Client() as client:
            # params = {"include_transcript": str(include_transcript).lower()}
            params = {"include_transcript": "true"} # DEBUG: Force true
            print(f"DEBUG: Calling GET {API_BASE}/api/v1/video/{video_id} with params={params}")
            resp = client.get(
                f"{API_BASE}/api/v1/video/{video_id}", 
                params=params
            )
            print(f"DEBUG: Response Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"DEBUG: Data keys: {data.keys()}")
                transcripts = data.get("transcripts", [])
                print(f"DEBUG: Transcripts count: {len(transcripts)}")
                if transcripts:
                    print(f"DEBUG: First transcript keys: {transcripts[0].keys()}")
                    print(f"DEBUG: First transcript text len: {len(transcripts[0].get('transcript') or '')}")
                
                # Parse transcript for display
                transcript_text = ""
                for t in transcripts:
                    if t.get("transcript"):
                        transcript_text += f"--- {t.get('language')} ({t.get('language_code')}) ---\n"
                        transcript_text += t.get("transcript") + "\n\n"
                
                if not transcript_text and include_transcript:
                    transcript_text = "(No transcript text returned)"
                
                return json.dumps(data, indent=2), transcript_text
            else:
                return f"Error: {resp.status_code} - {resp.text}", ""
    except Exception as e:
        return f"Connection Error: {e}", ""

def store_video_data(video_id, include_transcript):
    if not video_id:
        return "Please enter a video ID"
    video_id = video_id.strip()
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{API_BASE}/api/v1/video/{video_id}/store",
                params={"include_transcript": str(include_transcript).lower()}
            )
            if resp.status_code == 200:
                return json.dumps(resp.json(), indent=2)
            else:
                return f"Error: {resp.status_code} - {resp.text}"
    except Exception as e:
        return f"Connection Error: {e}"

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

# Add a selection event for the dataframe to populate the detail input
def on_select(evt: gr.SelectData):
    return evt.value

with gr.Blocks(title="YouTube Transcript Manager") as app:
    gr.Markdown("# YouTube Transcript Manager")
    
    with gr.Tab("Search & Store"):
        vid_input = gr.Textbox(label="Video ID or URL", value="EMd3H0pNvSE")
        chk_transcript = gr.Checkbox(label="Include Transcript", value=True)
        
        with gr.Row():
            btn_info = gr.Button("Get Info", variant="primary")
            btn_store = gr.Button("Store in DB")
        
        with gr.Row():
            out_info = gr.Code(label="Result JSON", language="json", lines=20)
            out_transcript = gr.Textbox(label="Transcript Text", lines=20, show_copy_button=True)
        
        btn_info.click(get_video_info, [vid_input, chk_transcript], [out_info, out_transcript])
        btn_store.click(store_video_data, [vid_input, chk_transcript], out_info)

    with gr.Tab("Database"):
        btn_refresh = gr.Button("Refresh List")
        db_table = gr.Dataframe(
            headers=["Video ID", "Title", "Fetched At"], 
            label="Stored Videos",
            interactive=False
        )
        
        gr.Markdown("### View Details")
        with gr.Row():
            db_vid_input = gr.Textbox(label="Video ID from DB", scale=4)
            btn_db_detail = gr.Button("Get DB Detail", scale=1)
            
        out_db_detail = gr.Code(label="DB Record JSON", language="json", lines=20)
        
        btn_refresh.click(list_db_videos, outputs=db_table)
        btn_db_detail.click(get_db_video_detail, db_vid_input, out_db_detail)
        
        # When clicking a cell in the table, copy value to input
        # Note: selecting a row is tricky in simple dataframe, usually select returns the cell value.
        # Ideally we want the Video ID (col 0).
        def select_video(evt: gr.SelectData):
            # This copies the clicked cell text
            return evt.value
            
        db_table.select(select_video, None, db_vid_input)

if __name__ == "__main__":
    app.launch()