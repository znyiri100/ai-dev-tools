import gradio as gr
import httpx
import json
import os
from youtube_api import search_videos

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

def format_transcript(data):
    transcripts = data.get("transcripts", [])
    if not transcripts:
        return ""
    
    # Priority: is_generated=True
    selected = None
    for t in transcripts:
        if t.get("is_generated") is True and t.get("transcript"):
            selected = t
            break
    
    # Fallback to first with text
    if not selected:
        for t in transcripts:
            if t.get("transcript"):
                selected = t
                break
                
    if selected:
        return selected.get("transcript", "")
    return ""

def extract_study_guide_quiz(data):
    transcripts = data.get("transcripts", [])
    if not transcripts:
        return "", ""
    
    # Priority: is_generated=True
    selected = None
    for t in transcripts:
        if t.get("is_generated") is True:
            selected = t
            break
    
    if not selected and transcripts:
        selected = transcripts[0]
        
    if selected:
        return selected.get("study_guide") or "", selected.get("quiz") or ""
    return "", ""

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
        return "Please enter a video ID", "", "", ""
    try:
        with httpx.Client() as client:
            resp = client.get(f"{API_BASE}/api/v1/db/video/{video_id}")
            if resp.status_code == 200:
                data = resp.json()
                transcript_text = format_transcript(data)
                sg, quiz = extract_study_guide_quiz(data)
                return json.dumps(data, indent=2), transcript_text, sg, quiz
            else:
                return f"Error: {resp.text}", "", "", ""
    except Exception as e:
        return f"Error: {e}", "", "", ""

def generate_study_guide(video_id, data_json):
    if not video_id or not data_json:
        return "No video selected or data missing", "No video selected or data missing"
    try:
        data = json.loads(data_json)
        transcripts = data.get("transcripts", [])
        if not transcripts:
            return "No transcripts available", "No transcripts available"
        
        # Priority: is_generated=True
        selected_t = next((t for t in transcripts if t.get("is_generated") is True), transcripts[0])
        lang_code = selected_t.get("language_code")
        
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(f"{API_BASE}/api/v1/transcript/{video_id}/{lang_code}/generate_study_guide")
            if resp.status_code == 200:
                content = resp.json().get("content", "Success, but no content returned")
                return content, content
            else:
                err = f"Error: {resp.text}"
                return err, err
    except Exception as e:
        err = f"Error: {e}"
        return err, err

def generate_quiz(video_id, data_json):
    if not video_id or not data_json:
        return "No video selected or data missing"
    try:
        data = json.loads(data_json)
        transcripts = data.get("transcripts", [])
        if not transcripts:
            return "No transcripts available for this video"
        
        # Priority: is_generated=True
        selected_t = next((t for t in transcripts if t.get("is_generated") is True), transcripts[0])
        lang_code = selected_t.get("language_code")
        
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(f"{API_BASE}/api/v1/transcript/{video_id}/{lang_code}/generate_quiz")
            if resp.status_code == 200:
                return resp.json().get("content", "Success, but no content returned")
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

css = """
.scrollable-markdown {
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid #ddd;
    padding: 15px;
    border-radius: 8px;
    background-color: #f9f9f9;
}
"""

with gr.Blocks(title="YouTube Transcript Manager", css=css) as app:
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
        
        # Hidden input for storing selected video ID to pass to generation functions
        db_vid_input = gr.State()
        
        with gr.Row():
            # Shows selected video ID, but read-only ish
            out_vid_display = gr.Textbox(label="Selected Video ID", interactive=False)

        with gr.Row():
            out_db_detail = gr.Code(label="DB Record JSON", language="json", lines=15, scale=1)
            out_db_transcript = gr.Textbox(label="Transcript Text", lines=15, scale=1)

        with gr.Row():
            btn_gen_study = gr.Button("Generate Study Guide", variant="primary")
            btn_gen_quiz = gr.Button("Generate Quiz", variant="primary")

        with gr.Row():
            out_study_guide = gr.Markdown(label="Study Guide", elem_classes=["scrollable-markdown"])
        with gr.Row():
            out_quiz = gr.Markdown(label="Quiz", elem_classes=["scrollable-markdown"])
        
        btn_refresh.click(list_db_videos, outputs=db_table)

    def chat_response(message, history, video_id):
        if not video_id:
            return "Please select a video in the Database tab first."
        
        try:
            # We need to know the language code. For now we assume 'en' or fetch it from the video detail.
            with httpx.Client() as client:
                # First get video detail to find language code
                resp = client.get(f"{API_BASE}/api/v1/db/video/{video_id}")
                if resp.status_code != 200:
                    return f"Error fetching video: {resp.text}"
                
                data = resp.json()
                transcripts = data.get("transcripts", [])
                if not transcripts:
                    return "No transcripts available."
                
                selected_t = next((t for t in transcripts if t.get("is_generated") is True), transcripts[0])
                lang_code = selected_t.get("language_code")

                chat_resp = client.post(
                    f"{API_BASE}/api/v1/transcript/{video_id}/{lang_code}/chat",
                    json={"message": message, "history": history},
                    timeout=60.0
                )
                
                if chat_resp.status_code == 200:
                    return chat_resp.json().get("content", "")
                else:
                    return f"Error: {chat_resp.text}"
        except Exception as e:
            return f"Error: {e}"

    with gr.Tab("Study Guide Chat"):
        gr.Markdown("### Chat with your Study Guide Tutor")
        
        with gr.Row():
            with gr.Column(scale=1):
                chat_sg_display = gr.Markdown(label="Study Guide Context", elem_classes=["scrollable-markdown"])
            with gr.Column(scale=2):
                gr.ChatInterface(
                    fn=chat_response,
                    additional_inputs=[db_vid_input],
                    title="Study Guide Tutor",
                    description="I am your friendly research assistant. Ask me anything about the selected study material!"
                )

    # --- Global Event Handlers linking tabs ---
    
    def on_select_video(evt: gr.SelectData):
        if not evt.row_value:
            return "", "", "", "", "", "", ""
        vid = evt.row_value[0]
        json_data, txt, sg, qz = get_db_video_detail(vid)
        # Returns: db_vid_input, out_vid_display, out_db_detail, out_db_transcript, out_study_guide, out_quiz, chat_sg_display
        return vid, vid, json_data, txt, sg, qz, sg

    db_table.select(
        on_select_video, 
        None, 
        [db_vid_input, out_vid_display, out_db_detail, out_db_transcript, out_study_guide, out_quiz, chat_sg_display]
    )
    
    btn_gen_study.click(
        generate_study_guide, 
        [db_vid_input, out_db_detail], 
        [out_study_guide, chat_sg_display]
    )
    
    btn_gen_quiz.click(generate_quiz, [db_vid_input, out_db_detail], out_quiz)

if __name__ == "__main__":
    app.launch()