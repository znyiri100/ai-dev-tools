from pathlib import Path
from nicegui import run, ui, app
import asyncio
import json
from api_client import ApiClient
from youtube_api import search_videos
import shutil
import sys
import re

ABOUT_TEXT = """
### Welcome to Learnify!

This application helps you master any topic using YouTube videos as source material.

**Workflow:**

1. **Find Source / Generate Lesson**: Search for a topic or paste a video ID to find content.

2. **Pick Lesson**: Select a processed video from your library.

3. **Study / Chat / Quiz**: Use AI-generated study guides, an interactive tutor, and quizzes to deep dive into the material.
"""

class YtDlpLogger:
    def debug(self, msg):
        pass
    def warning(self, msg):
        if "Remote component" in msg or "n challenge solving failed" in msg or "Ignoring unsupported" in msg:
            return
        print(f"WARNING: {msg}")
    def error(self, msg):
        print(f"ERROR: {msg}")

# Initialize Client
client = ApiClient()

def main():
    # --- Sound Effects Script ---
    ui.add_head_html("""
    <script>
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    function playTone(freq, type, duration) {
        if (audioCtx.state === 'suspended') audioCtx.resume();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = type;
        osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.00001, audioCtx.currentTime + duration);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + duration);
    }
    function playChatSound() { playTone(600, 'sine', 0.1); }
    function playCorrectSound() { playTone(800, 'sine', 0.1); setTimeout(() => playTone(1200, 'sine', 0.2), 100); }
    function playIncorrectSound() { playTone(200, 'sawtooth', 0.3); }
    </script>
    """)

    # --- State Variables ---
    state = {
        "search_input": "EMd3H0pNvSE",
        "include_transcript": False,
        "sg_prompt_input": """You are a highly capable research assistant and tutor. Create a detailed study guide designed to review understanding of the transcript. Create a quiz with ten short-answer questions (2-3 sentences each) and include a separate answer key.

Transcript:
{transcript}""",
        "quiz_prompt_input": """Generate a quiz with 5 multiple choice questions based on the transcript.
Return the result strictly as a valid JSON array of objects.
Each object must have the following structure:
{{
    "question": "The question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "The text of the correct option (must match one of the options exactly)",
    "explanation": "Brief explanation of why this is correct"
}}
Return ONLY the JSON array. Do not include any markdown formatting (like ```json ... ```), no preamble, and no postscript.

Transcript:
{transcript}"""
    }

    # DB Tab
    selected_db_video_id = None
    
    quiz_data = []
    current_q_index = 0
    user_score = 0
    
    # Callback handlers (mutable state to avoid global)
    quiz_handlers = {"show_question": None}
    
    # --- UI Components References (for updates) ---
    # Search
    results_table = None
    json_output = None
    transcript_output = None
    desc_output = None
    author_output = None
    url_link = None
    
    # DB
    db_table = None
    db_json_output = None
    db_transcript_output = None
    sg_output = None
    chat_sg_display = None
    quiz_output_text = None
    db_sg_output = None
    db_quiz_output = None
    sg_read_display = None
    chat_history = []
    
    # Quiz
    quiz_container = None
    quiz_question_label = None
    quiz_options_container = None
    quiz_feedback_label = None
    quiz_score_label = None
    quiz_progress_label = None
    btn_submit = None
    btn_next = None

    # --- Functions ---

    async def search_by_topic():
        nonlocal results_table
        if not state['search_input']:
            ui.notify("Please enter a topic", type="warning")
            return
            
        ui.notify("Searching YouTube...", type="info")
        print(f"DEBUG: Starting search for topic: {state['search_input']}")
        
        # Run synchronous yt-dlp search in a separate thread to avoid blocking UI
        results = await run.io_bound(search_videos, state['search_input'], limit=int(state['limit_input']))
        
        print(f"DEBUG: Search results received: {len(results) if results else 0} items")
        
        # Transform for AgGrid
        # AgGrid expects a list of dictionaries
        if results and "error" in results[0]:
            print(f"DEBUG: Search error: {results[0]['error']}")
            ui.notify(f"Error: {results[0]['error']}", type="negative")
            results_table.rows = []
        else:
            if results:
                print(f"DEBUG: First result: {results[0]}")
            else:
                print("DEBUG: No results found.")
            
            # Update Table
            results_table.rows = results
            # Explicit update to ensure UI refresh
            results_table.update()
            
        print("DEBUG: Search complete and table updated")
            
    async def search_by_id():
        nonlocal results_table
        vid = state['search_input']
        if not vid:
            ui.notify("Please enter a Video ID", type="warning")
            return
            
        ui.notify("Fetching ID details...", type="info")
        
        # Use yt-dlp to extract video info (same approach as topic search for reliable view count)
        def extract_video_info(video_id):
            import yt_dlp
            
            # Explicitly get node path to avoid inline evaluation issues
            node_path = shutil.which('node')
            
            ydl_opts = {
                'quiet': False,
                'skip_download': True,
                'force_generic_extractor': False,
                'logger': YtDlpLogger(),
                'js_runtimes': {
                    'node': {'args': [node_path] if node_path else []},
                },
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                return ydl.extract_info(video_url, download=False)
        
        try:
            # Run yt-dlp in a separate thread to avoid blocking UI
            info = await run.io_bound(extract_video_info, vid)
            
            row = {
                'id': info.get('id', vid),
                'title': info.get('title', 'Unknown Title'),
                'uploader': info.get('uploader') or info.get('channel') or 'Unknown',
                'description': info.get('description', ''),
                'duration': info.get('duration'),
                'viewCount': info.get('view_count'),  # yt-dlp reliably extracts view count
                'link': info.get('webpage_url') or f"https://www.youtube.com/watch?v={vid}",
            }
            results_table.rows = [row]
            results_table.update()
        except Exception as e:
            ui.notify(f"Error: {str(e)}", type="negative")


    async def fetch_from_youtube():
        query = state['search_input'].strip()
        if not query:
             ui.notify("Please enter a Video ID or Topic", type="warning")
             return

        # Simple ID detection: 11 chars, alphanumeric/underscore/dash
        # This covers standard YouTube video IDs
        if re.match(r'^[a-zA-Z0-9_-]{11}$', query):
             ui.notify("Detected Video ID", type="info")
             await search_by_id()
        else:
             ui.notify("Detected Topic Search", type="info")
             await search_by_topic()

    async def get_video_info():
        nonlocal json_output, sg_output, quiz_output_text, transcript_output
        vid = state['search_input']
        if not vid:
             return
        
        # 1. Fetch from YouTube API and show in JSON
        yt_resp = await client.get_video(vid, state['include_transcript'])
        if yt_resp and yt_resp.status_code == 200:
            yt_data = yt_resp.json()
            # Show YouTube data in JSON output
            json_output.set_content(f"```json\n{json.dumps(yt_data, indent=2)}\n```")
            
            # Show transcript preview if available
            transcripts = yt_data.get("transcripts", [])
            if transcripts and transcript_output:
                # Get transcript text from first available transcript
                first_transcript = transcripts[0] if isinstance(transcripts[0], dict) else {}
                transcript_text = first_transcript.get("transcript", "")
                if transcript_text:
                    transcript_output.value = transcript_text
                else:
                    transcript_output.value = "No transcript text available"
            elif transcript_output:
                transcript_output.value = ""
        else:
            json_output.set_content("_Could not fetch video from YouTube_")
            if transcript_output:
                transcript_output.value = ""
        
        # 2. Try to fetch from DB for Study Guide and Quiz
        db_resp = await client.get_video_details(vid)
        if db_resp and db_resp.status_code == 200:
            db_data = db_resp.json()
            # Get transcripts to find study_guide and quiz
            transcripts = db_data.get("transcripts", [])
            if transcripts:
                # Find the generated transcript or use first one
                selected = next((t for t in transcripts if t.get("is_generated")), transcripts[0])
                sg_val = selected.get("study_guide") or ""
                qz_val = selected.get("quiz") or ""
                sg_output.value = sg_val
                quiz_output_text.value = qz_val
            else:
                sg_output.value = ""
                quiz_output_text.value = ""
        else:
            # Not in DB - clear SG/Quiz
            sg_output.value = ""
            quiz_output_text.value = ""


    async def store_video_db():
        nonlocal sg_output, quiz_output_text
        vid = state['search_input']
        if not vid:
            ui.notify("Please enter a Video ID first", type="warning")
            return
            
        ui.notify("Storing video...", type="info")
        resp = await client.store_video(vid)
        if resp and resp.status_code == 200:
             ui.notify("Video stored successfully!", type="positive")
             # Update info box
             if json_output:
                json_output.set_content(f"```json\n{json.dumps(resp.json(), indent=2)}\n```")
             
             # Save study guide and quiz if present in textareas
             has_sg = sg_output and sg_output.value and sg_output.value.strip()
             has_quiz = quiz_output_text and quiz_output_text.value and quiz_output_text.value.strip()
             
             if has_sg or has_quiz:
                 # Fetch video details to get language code
                 details_resp = await client.get_video_details(vid)
                 if details_resp and details_resp.status_code == 200:
                     data = details_resp.json()
                     transcripts = data.get("transcripts", [])
                     if transcripts:
                         selected = next((t for t in transcripts if t.get("is_generated") is True), transcripts[0])
                         lang = selected.get("language_code", "en")
                         
                         # Save study guide and/or quiz
                         update_resp = await client.update_transcript_content(
                             vid, 
                             lang,
                             study_guide=sg_output.value if has_sg else None,
                             quiz=quiz_output_text.value if has_quiz else None
                         )
                         
                         if update_resp and update_resp.status_code == 200:
                             ui.notify("Study guide and quiz saved!", type="positive")
                         else:
                             ui.notify("Warning: Failed to save study guide/quiz", type="warning")
             
             await refresh_db_list()
        else:
             err = resp.text if resp else "Connection Error"
             ui.notify(f"Error: {err}", type="negative")

    async def refresh_db_list():
        nonlocal db_table
        ui.notify("Refreshing list...", type="info")
        print("DEBUG: Refreshing database list...")
        resp = await client.list_videos()
        if resp and resp.status_code == 200:
            videos = resp.json()
            if not videos:
                ui.notify("No videos found in database.", type="warning")
                print("DEBUG: No videos returned from API.")
            else:
                ui.notify(f"Loaded {len(videos)} videos.", type="positive")
                print(f"DEBUG: Loaded {len(videos)} videos from API.")
                print(f"DEBUG: First video: {videos[0]}")
            
            # videos is list of dicts: video_id, title, fetched_at, etc.
            if db_table:
                db_table.rows = videos
                db_table.update()
                
                print(f"DEBUG: Loaded {len(videos)} videos into Lessons table.")
        else:
             err = resp.text if resp else "Connection Error"
             print(f"DEBUG: Error refreshing list: {err}")
             ui.notify(f"Error refreshing list: {err}", type="negative")

    async def load_db_video_details(e):
        nonlocal selected_db_video_id, sg_read_display, chat_history
        if not e.selection: return
        row = e.selection[0]
        selected_db_video_id = row['video_id']
        
        ui.notify(f"Loaded {selected_db_video_id}", type="info")
        
        resp = await client.get_video_details(selected_db_video_id)
        if resp and resp.status_code == 200:
            data = resp.json()
            if db_json_output:
                db_json_output.set_content(f"```json\n{json.dumps(data, indent=2)}\n```")
            
            transcripts = data.get("transcripts", [])
            selected = next((t for t in transcripts if t.get("is_generated") is True), transcripts[0] if transcripts else None)
            
            txt = (selected.get("transcript") or "") if selected else ""
            sg = (selected.get("study_guide") or "") if selected else ""
            qz = (selected.get("quiz") or "") if selected else ""
            
            if db_transcript_output: db_transcript_output.value = txt
            if db_sg_output: db_sg_output.set_content(sg)
            # if chat_sg_display: chat_sg_display.set_content(f"**Context Used:**\n\n{sg[:200]}...") # Removed context display
            if sg_read_display: sg_read_display.set_content(sg if sg else "_No study guide generated yet. Generate one in the Lessons tab._")
            
            # Format quiz as JSON code block
            if db_quiz_output:
                if qz:
                    # Try to parse and pretty-print as JSON
                    try:
                        quiz_parsed = json.loads(qz)
                        db_quiz_output.set_content(f"```json\n{json.dumps(quiz_parsed, indent=2)}\n```")
                    except json.JSONDecodeError:
                        # If not valid JSON, show as-is
                        db_quiz_output.set_content(qz)
                else:
                    db_quiz_output.set_content("_No quiz generated yet_")
            
            # Initialize Chat with Intro
            if chat_container and sg:
                chat_container.clear()
                # Reset history when loading a new video's chat
                chat_history = []
                
                with chat_container:
                     ui.spinner('dots')
                
                # Fetch intro
                lang = selected.get("language_code", "en") if selected else "en"
                
                try:
                     # Create placeholder for streaming response
                     with chat_container:
                          with ui.chat_message(name="Tutor", sent=False):
                               response_message = ui.markdown("Thinking...").classes('text-lg')
                     
                     full_response = ""
                     first_chunk = True
                     async for chunk in client.chat_with_guide_stream(selected_db_video_id, lang, "Hello (Introduce yourself and the topic)", []):
                          if first_chunk:
                               response_message.content = ""
                               first_chunk = False
                               ui.run_javascript("playChatSound()")
                          full_response += chunk
                          response_message.content = full_response
                          ui.run_javascript(f'getElement({chat_container.id}).scrollTop = getElement({chat_container.id}).scrollHeight')
                     
                     if not full_response:
                          response_message.content = "Hello! I'm ready to help you study this video."
                     
                     # Add intro to history
                     chat_history.append({"role": "assistant", "content": full_response})
                     ui.run_javascript(f'getElement({chat_container.id}).scrollTop = getElement({chat_container.id}).scrollHeight')
                     
                except Exception as e:
                    chat_container.clear()
                    with chat_container:
                        ui.chat_message(f"Error starting chat: {str(e)}", name="System", sent=False)
            elif chat_container:
                 chat_container.clear()
                 with chat_container:
                      ui.chat_message("Please generate a study guide for this video first.", name="System", sent=False)

            # Setup Interactive Quiz
            if qz:
                setup_quiz(qz)
            else:
                reset_quiz_ui("No quiz generated for this video yet.")

    async def generate_sg_search():
        """Generate study guide for Search & Store tab - only populates UI, doesn't save"""
        nonlocal sg_output, transcript_output
        vid = state['search_input']
        if not vid:
            ui.notify("Please enter a Video ID first", type="warning")
            return
        
        # Get transcript from the transcript preview (already fetched from YouTube)
        transcript_text = transcript_output.value if transcript_output else ""
        
        # If no transcript in preview, try to fetch from YouTube API
        if not transcript_text or transcript_text == "No transcript text available":
            ui.notify("Fetching transcript...", type="info")
            yt_resp = await client.get_video(vid, include_transcript=True)
            if yt_resp and yt_resp.status_code == 200:
                yt_data = yt_resp.json()
                transcripts = yt_data.get("transcripts", [])
                if transcripts:
                    first_transcript = transcripts[0] if isinstance(transcripts[0], dict) else {}
                    transcript_text = first_transcript.get("transcript", "")
                    if transcript_output:
                        transcript_output.value = transcript_text
        
        if not transcript_text or transcript_text == "No transcript text available":
            ui.notify("No transcript available. Make sure 'Include Transcript' is checked and fetch again.", type="warning")
            return
        
        prompt = state.get('sg_prompt_input')
        
        ui.notify("Generating Study Guide...", type="info")
        gen_resp = await client.generate_study_guide_direct(transcript_text, prompt=prompt)
        if gen_resp and gen_resp.status_code == 200:
            content = gen_resp.json().get("content", "")
            if sg_output: 
                sg_output.value = content
            ui.notify("Study Guide Generated! Click 'Save Lesson' to save.", type="positive")
        else:
            err = gen_resp.text if gen_resp else "Connection error"
            ui.notify(f"Generation failed: {err}", type="negative")

    async def generate_qz_search():
        """Generate quiz for Search & Store tab - only populates UI, doesn't save"""
        nonlocal quiz_output_text, transcript_output
        vid = state['search_input']
        if not vid:
            ui.notify("Please enter a Video ID first", type="warning")
            return
        
        # Get transcript from the transcript preview (already fetched from YouTube)
        transcript_text = transcript_output.value if transcript_output else ""
        
        # If no transcript in preview, try to fetch from YouTube API
        if not transcript_text or transcript_text == "No transcript text available":
            ui.notify("Fetching transcript...", type="info")
            yt_resp = await client.get_video(vid, include_transcript=True)
            if yt_resp and yt_resp.status_code == 200:
                yt_data = yt_resp.json()
                transcripts = yt_data.get("transcripts", [])
                if transcripts:
                    first_transcript = transcripts[0] if isinstance(transcripts[0], dict) else {}
                    transcript_text = first_transcript.get("transcript", "")
                    if transcript_output:
                        transcript_output.value = transcript_text
        
        if not transcript_text or transcript_text == "No transcript text available":
            ui.notify("No transcript available. Make sure 'Include Transcript' is checked and fetch again.", type="warning")
            return
        
        prompt = state.get('quiz_prompt_input')
        
        ui.notify("Generating Quiz...", type="info")
        gen_resp = await client.generate_quiz_direct(transcript_text, prompt=prompt)
        if gen_resp and gen_resp.status_code == 200:
            content = gen_resp.json().get("content", "")
            if quiz_output_text: 
                quiz_output_text.value = content
            ui.notify("Quiz Generated! Click 'Save Lesson' to save.", type="positive")
        else:
            err = gen_resp.text if gen_resp else "Connection error"
            ui.notify(f"Generation failed: {err}", type="negative")

    async def generate_sg():
        if not selected_db_video_id:
            ui.notify("Select a video first", type="warning")
            return
        
        # Need lang code. Fetch details again or store it. 
        # Simplified: fetch details to get lang code
        resp = await client.get_video_details(selected_db_video_id)
        if not resp: return
        data = resp.json()
        transcripts = data.get("transcripts", [])
        selected = next((t for t in transcripts if t.get("is_generated") is True), transcripts[0])
        lang = selected.get("language_code", "en") # default en
        
        prompt = state.get('sg_prompt_input')
        
        ui.notify("Generating Study Guide...", type="info")
        gen_resp = await client.generate_study_guide(selected_db_video_id, lang, prompt=prompt)
        if gen_resp and gen_resp.status_code == 200:
            content = gen_resp.json().get("content", "")
            if db_sg_output: db_sg_output.set_content(content) # markdown uses .set_content
            ui.notify("Study Guide Generated!", type="positive")
        else:
            ui.notify("Generation failed", type="negative")

    async def generate_qz():
        if not selected_db_video_id:
            ui.notify("Select a video first", type="warning")
            return
            
        resp = await client.get_video_details(selected_db_video_id)
        if not resp: return
        data = resp.json()
        transcripts = data.get("transcripts", [])
        selected = next((t for t in transcripts if t.get("is_generated") is True), transcripts[0])
        lang = selected.get("language_code", "en") 
        
        prompt = state.get('quiz_prompt_input')
        
        ui.notify("Generating Quiz...", type="info")
        gen_resp = await client.generate_quiz(selected_db_video_id, lang, prompt=prompt)
        if gen_resp and gen_resp.status_code == 200:
            content = gen_resp.json().get("content", "")
            if db_quiz_output: db_quiz_output.set_content(content) # markdown uses .set_content
            setup_quiz(content)
            ui.notify("Quiz Generated!", type="positive")
        else:
            ui.notify("Generation failed", type="negative")

    # --- Quiz Logic ---
    def reset_quiz_ui(msg=""):
        nonlocal quiz_data, current_q_index, user_score
        quiz_data = []
        current_q_index = 0
        user_score = 0
        if quiz_container: quiz_container.visible = False
        if quiz_progress_label: quiz_progress_label.text = msg

    def setup_quiz(quiz_json_text):
        nonlocal quiz_data, current_q_index, user_score
        try:
            # Simple cleanup similar to Gradio
            text = quiz_json_text.strip()
            if text.startswith("```"):
                lines = text.split('\n')
                # remove first and last
                if "json" in lines[0]: lines = lines[1:]
                else: lines = lines[1:]
                if "```" in lines[-1]: lines = lines[:-1]
                text = "\n".join(lines)
            
            data = json.loads(text)
            if isinstance(data, list) and len(data) > 0:
                quiz_data = data
                current_q_index = 0
                user_score = 0
                question_fn = quiz_handlers.get("show_question")
                if question_fn:
                    question_fn(0)
                else:
                    ui.notify("Quiz UI not ready", type="warning")
            else:
                reset_quiz_ui("Quiz format not supported (not a list).")
        except:
             reset_quiz_ui("Could not parse Quiz JSON.")

    def show_question(idx):
        if idx >= len(quiz_data):
            show_results()
            return
            
        q = quiz_data[idx]
        
        if quiz_container: quiz_container.visible = True
        if quiz_progress_label: quiz_progress_label.text = f"Question {idx + 1} / {len(quiz_data)}"
        if quiz_score_label: quiz_score_label.text = f"Score: {user_score}"
        if quiz_question_label: quiz_question_label.set_content(f"**{q.get('question')}**")
        if quiz_feedback_label: 
            quiz_feedback_label.visible = False
            quiz_feedback_label.text = ""
        
        if btn_submit: btn_submit.visible = True
        if btn_next: btn_next.visible = False
        
        # Options
        if quiz_options_container:
            quiz_options_container.clear()
            with quiz_options_container:
                 # Standard Radio
                 opts = q.get('options', [])
                 ui.radio(opts, on_change=None).bind_value_to(quiz_options_container, 'value')

    def submit_answer():
        nonlocal user_score
        # Get selected value
        # There is no easy 'value' property on a container, so we have to track the radio info
        # Let's simple use a variable for radio selection
        # But we create radio dynamically. 
        # A workaround is to access the child element
        # Or better: bind the radio to a state variable class or dict
        pass 
        # ... (Improving this part in the layout section below)

    # --- Chat Logic ---
    # --- Chat Logic ---
    async def chat_submit(e):
        nonlocal chat_history
        msg = e.sender.value
        e.sender.value = "" # clear input
        if not msg: return
        if not selected_db_video_id:
            ui.notify("Select a video first", type="warning")
            return

        # UI Chat Message (User)
        with chat_container:
            with ui.chat_message(name="You", sent=True):
                ui.markdown(msg).classes('text-lg')
            
        # Add to history
        chat_history.append({"role": "user", "content": msg})
            
        # Get response
        # Need lang... again assume fetch or robust state
        resp = await client.get_video_details(selected_db_video_id)
        selected = next((t for t in resp.json().get("transcripts", []) if t.get("is_generated") is True), {})
        lang = selected.get("language_code", "en")
        
        # Pass history to backend (streaming)
        with chat_container:
            with ui.chat_message(name="Tutor", sent=False):
                 response_message = ui.markdown("...").classes('text-lg')
        
        full_reply = ""
        first = True
        async for chunk in client.chat_with_guide_stream(selected_db_video_id, lang, msg, chat_history):
             if first:
                 response_message.content = ""
                 first = False
                 ui.run_javascript("playChatSound()")
             full_reply += chunk
             response_message.content = full_reply
             ui.run_javascript(f'getElement({chat_container.id}).scrollTop = getElement({chat_container.id}).scrollHeight')
             
        # Add bot reply to history
        chat_history.append({"role": "assistant", "content": full_reply})
        ui.run_javascript(f'getElement({chat_container.id}).scrollTop = getElement({chat_container.id}).scrollHeight')

    # --- Layout ---
    ui.colors(primary='#6A1B9A', secondary='#FFD700', accent='#D81B60', positive='#21BA45')
    
    with ui.header().classes(replace='row items-center') as header:
        ui.icon('smart_display', color='white', size='md')
        ui.label('Learnify:').classes('text-h6 text-white')
        ui.label('Find source/Generate lesson -> Pick lesson -> Study/Chat/Quiz').classes('text-h6 text-white')
    
    with ui.tabs().classes('w-full') as tabs:
        search_tab = ui.tab('Find')
        db_tab = ui.tab('Pick')
        sg_tab = ui.tab('Study')
        chat_tab = ui.tab('Chat')
        quiz_tab = ui.tab('Quiz')
        docs_tab = ui.tab('About')

    with ui.tab_panels(tabs, value=search_tab).classes('w-full p-4'):
        
        # --- TAB 1: Search & Store ---
        with ui.tab_panel(search_tab):
            with ui.row().classes('w-full gap-4'):
                # --- Input Area ---
                with ui.column().classes('w-full'):
                    # Unify Search inputs visibly
                    with ui.row().classes('w-full items-center gap-4'):
                        # Merged Input
                        ui.input(label='Find (Topic or Video ID)', placeholder='Enter topic or YouTube ID').bind_value(state, 'search_input').classes('flex-grow')
                        
                        ui.number(label='Limit', value=3).bind_value(state, 'limit_input').classes('w-24')
                        
                        # Fetch Button
                        ui.button('Find', icon='search', on_click=fetch_from_youtube)
                        
                        # Include Transcript checkbox
                        ui.checkbox('Include Transcript').bind_value(state, 'include_transcript')
                        
                    # --- Result Table (Unified) ---
                    columns = [
                        {'name': 'id', 'label': 'ID', 'field': 'id'},
                        {'name': 'title', 'label': 'Title', 'field': 'title', 'classes': 'ellipsis', 'style': 'max-width: 200px;'},
                        {'name': 'uploader', 'label': 'Author', 'field': 'uploader'},
                        {'name': 'description', 'label': 'Description', 'field': 'description', 'classes': 'ellipsis', 'style': 'max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'},
                         {'name': 'duration', 'label': 'Duration', 'field': 'duration'},
                        {'name': 'viewCount', 'label': 'Views', 'field': 'viewCount'},
                    ]
                    
                    async def on_table_select(e):
                        if e.selection:
                            row = e.selection[0]
                            state['search_input'] = row.get('id')
                            # Auto-fetch full details + DB check
                            await get_video_info()

                    results_table = ui.table(columns=columns, rows=[], row_key='id', selection='single', on_select=on_table_select).classes('w-full mt-4')

                    # Add slot for clickable ID
                    results_table.add_slot('body-cell-id', '''
                        <q-td :props="props">
                            <a :href="'https://www.youtube.com/watch?v=' + props.value" target="_blank" style="color: #1976d2; text-decoration: underline; cursor: pointer;">{{ props.value }}</a>
                        </q-td>
                    ''')

                    results_table.add_slot('body-selection', '''
                        <q-td auto-width>
                             <q-icon :name="props.selected ? 'radio_button_checked' : 'radio_button_unchecked'" 
                                     size="sm" 
                                     color="primary"
                                     class="cursor-pointer" 
                                     @click="props.selected = !props.selected" />
                        </q-td>
                    ''')
                    
                    ui.separator().classes('my-4')
                    
                    # Transcript Preview and Details side by side
                    with ui.row().classes('w-full gap-4 flex-nowrap'):
                        # Transcript Preview Column (conditionally visible)
                        transcript_column = ui.column().classes('flex-1 min-w-0')
                        with transcript_column:
                            ui.label("Transcript").classes('text-lg font-bold')
                            transcript_output = ui.textarea(label='', placeholder='Transcript will appear here when video is selected...').props('readonly').classes('w-full h-48')
                        transcript_column.bind_visibility_from(state, 'include_transcript')
                        
                        # Detail View Column
                        with ui.column().classes('flex-1 min-w-0'):
                            ui.label("Selected Video Details").classes('text-lg font-bold')
                            json_output = ui.markdown("").classes('w-full h-48 overflow-auto border p-2 rounded bg-gray-50 text-xs')
                    
                    # Study Guide and Quiz side by side
                    with ui.row().classes('w-full gap-4 mt-4 flex-nowrap'):
                        # Study Guide Column (left)
                        with ui.column().classes('flex-1 min-w-0'):
                             ui.label("Study Guide Generator").classes('text-lg font-bold')
                             ui.textarea(label='Sys Prompt (Optional)', placeholder='Custom instruction...').bind_value(state, 'sg_prompt_input').classes('w-full h-24')
                             ui.button('Generate Study Guide', on_click=generate_sg_search).classes('w-full my-2')
                             sg_output = ui.textarea(label='Content', placeholder='Generated content will appear here...').classes('w-full flex-grow')
                        
                        # Quiz Column (right)
                        with ui.column().classes('flex-1 min-w-0'):
                             ui.label("Quiz Generator").classes('text-lg font-bold')
                             ui.textarea(label='Sys Prompt (Optional)', placeholder='Custom instruction...').bind_value(state, 'quiz_prompt_input').classes('w-full h-24')
                             ui.button('Generate Quiz', on_click=generate_qz_search).classes('w-full my-2')
                             quiz_output_text = ui.textarea(label='Content', placeholder='Generated quiz JSON...').classes('w-full flex-grow')
                    
                    # Save button at the bottom
                    ui.button('Save Lesson', color='secondary', icon='save', on_click=store_video_db).classes('mt-4 w-full')

        # --- TAB 2: Lessons ---
        with ui.tab_panel(db_tab):
            ui.button('Refresh List', icon='refresh', on_click=refresh_db_list)
            
            db_table = ui.table(columns=[
                    {'name': 'video_id', 'label': 'ID', 'field': 'video_id'},
                    {'name': 'title', 'label': 'Title', 'field': 'title', 'classes': 'ellipsis', 'style': 'max-width: 250px;'},
                    {'name': 'author', 'label': 'Author', 'field': 'author'},
                    {'name': 'duration', 'label': 'Duration', 'field': 'duration'},
                    {'name': 'view_count', 'label': 'Views', 'field': 'view_count'},
                    {'name': 'has_study_guide', 'label': 'SG', 'field': 'has_study_guide'},
                    {'name': 'has_quiz', 'label': 'Quiz', 'field': 'has_quiz'},
                    {'name': 'fetched_at', 'label': 'Fetched At', 'field': 'fetched_at'},
                ], rows=[], row_key='video_id', selection='single', on_select=load_db_video_details).classes('w-full mt-2')
            
            db_table.add_slot('body-cell-id', '''
                <q-td :props="props">
                    <a :href="'https://www.youtube.com/watch?v=' + props.value" target="_blank" class="text-blue-600 hover:underline">
                        {{ props.value }}
                    </a>
                </q-td>
            ''')

            db_table.add_slot('body-selection', '''
                <q-td auto-width>
                        <q-icon :name="props.selected ? 'radio_button_checked' : 'radio_button_unchecked'" 
                                size="sm" 
                                color="primary"
                                class="cursor-pointer" 
                                @click="props.selected = !props.selected" />
                </q-td>
            ''')
            
            ui.label("Selected Video Details").classes('text-h6 mt-4')
            
            with ui.row().classes('w-full gap-4'):
                with ui.tabs().classes('w-full') as sub_tabs:
                    st_detail = ui.tab('Details')
                    st_sg = ui.tab('Study Guide')
                    st_qz = ui.tab('Quiz')
                
                with ui.tab_panels(sub_tabs, value=st_detail).classes('w-full border p-2 h-96 overflow-auto'):
                     with ui.tab_panel(st_detail):
                          with ui.row().classes('h-full'):
                               db_json_output = ui.markdown("Select a video").classes('w-1/2 overflow-auto')
                               db_transcript_output = ui.textarea().classes('w-1/2 h-full').props('readonly')
                     
                     with ui.tab_panel(st_sg):
                          #ui.button('Generate Study Guide', on_click=generate_sg).classes('mb-2')
                          db_sg_output = ui.markdown("").classes('w-full')
                     
                     with ui.tab_panel(st_qz):
                          #ui.button('Generate Quiz', on_click=generate_qz).classes('mb-2')
                          db_quiz_output = ui.markdown("").classes('w-full')

        # --- TAB 3: Study Guide (Read-only) ---
        with ui.tab_panel(sg_tab):
            ui.label("Study Guide").classes('text-h5 mb-4')
            ui.markdown("Select a video from the Lessons tab to view its study guide.").classes('text-gray-500 mb-4')
            sg_read_display = ui.markdown("").classes('w-full border rounded p-4 bg-gray-50 min-h-96 overflow-auto')

        # --- TAB 4: Chat ---
        with ui.tab_panel(chat_tab):
             with ui.column().classes('h-[65vh] w-full border rounded shadow-sm p-4 items-stretch'):
                   # Chat history container
                   chat_container = ui.column().classes('w-full flex-grow overflow-auto space-y-4')
                   with chat_container:
                       ui.chat_message("Select a video from the Lessons tab to start chatting.", name="System", sent=False)
                   
                   # Input area
                   with ui.column().classes('w-full mt-auto pt-2 border-t shrink-0'):
                        ui.input(placeholder='Ask a question...').on('keydown.enter', chat_submit).classes('w-full').props('outlined rounded')

        # --- TAB 5: Quiz ---
        with ui.tab_panel(quiz_tab):
            quiz_progress_label = ui.label("Select a video and generate a quiz first.").classes('text-lg')
            quiz_container = ui.card().classes('w-full max-w-2xl mx-auto mt-4 p-4').props('visible=False')
            
            with quiz_container:
                with ui.row().classes('w-full justify-between mb-4'):
                    quiz_score_label = ui.label("Score: 0").classes('font-bold')
                
                quiz_question_label = ui.markdown("Question").classes('text-xl mb-6')
                
                # Handling Radio selection state manually for simplicity
                current_selection = {'value': None}
                
                def on_radio_change(e):
                    current_selection['value'] = e.value
                
                # Options are rebuilt dynamically so we need a container
                quiz_options_container = ui.column().classes('w-full space-y-2 mb-6')
                
                quiz_feedback_label = ui.markdown("").classes('p-4 bg-gray-100 rounded mb-4').props('visible=False')
                
                with ui.row().classes('w-full justify-end'):
                     def on_submit_click():
                         if current_q_index >= len(quiz_data): return
                         sel = current_selection['value'] # using the container value if bound?
                         # Actually checking the radio child
                         # Better: use a dummy ui.radio to get the class type but dynamic creation is tricky for binding.
                         # Let's assume the radio inside quiz_options_container works.
                         
                         # Check internal NiceGUI value retrieval
                         # Ideally we should clear the container and add a fresh radio with on_change
                         pass
                         
                         # ... Re-implementing specific quiz logic cleaner below
                     
                     btn_submit = ui.button('Submit Answer')
                     btn_next = ui.button('Next Question').props('visible=False')
                
                # --- Quick Fix for Quiz Logic Integration ---
                # Since we are inside the 'main' scope, defining the callbacks here creates closure over the state
                
                def render_current_question():
                    if current_q_index >= len(quiz_data):
                        quiz_question_label.set_content("**Quiz Completed!**")
                        quiz_options_container.clear()
                        btn_submit.visible = False
                        btn_next.visible = False
                        quiz_feedback_label.visible = True
                        quiz_feedback_label.set_content(f"Final Score: {user_score} / {len(quiz_data)}")
                        return

                    q = quiz_data[current_q_index]
                    quiz_question_label.set_content(f"**{q.get('question')}**")
                    quiz_progress_label.text = f"Question {current_q_index + 1} / {len(quiz_data)}"
                    
                    quiz_options_container.clear()
                    current_selection['value'] = None
                    with quiz_options_container:
                        ui.radio(q.get('options', []), on_change=lambda e: current_selection.update({'value': e.value}))
                    
                    quiz_feedback_label.visible = False
                    btn_submit.visible = True
                    btn_next.visible = False

                def handle_submit():
                    sel = current_selection['value']
                    if not sel:
                        ui.notify("Select an option!", type="warning")
                        return
                    
                    q = quiz_data[current_q_index]
                    correct = q.get("correct_answer")
                    is_correct = (sel == correct)
                    
                    nonlocal user_score
                    if is_correct: 
                        user_score += 1
                        msg = f"✅ **Correct!**\n\n{q.get('explanation', '')}"
                        ui.run_javascript("playCorrectSound()")
                    else:
                        msg = f"❌ **Incorrect.**\n\nCorrect: **{correct}**\n\n{q.get('explanation', '')}"
                        ui.run_javascript("playIncorrectSound()")
                    
                    quiz_feedback_label.set_content(msg)
                    quiz_feedback_label.visible = True
                    quiz_score_label.text = f"Score: {user_score}"
                    
                    btn_submit.visible = False
                    btn_next.visible = True

                def handle_next():
                    nonlocal current_q_index
                    current_q_index += 1
                    render_current_question()

                # Bind buttons
                btn_submit.on_click(handle_submit)
                btn_next.on_click(handle_next)
                
                # Replace the show_question global function for specific logic
                def show_question_local(idx):
                    nonlocal current_q_index 
                    current_q_index = idx
                    render_current_question()
                    
                # HACK: Hook it back to the outer scope function
                # Hook it back to the outer scope function
                quiz_handlers['show_question'] = show_question_local

        with ui.tab_panel(docs_tab):
            ui.label('System Documentation').classes('text-h4 mb-4')
            try:
                base_path = Path(__file__).resolve().parent.parent / "docs"
                erd_path = base_path / "erd.mmd"
                flow_path = base_path / "flow.mmd"
                prog_path = base_path / "program_flow.md"
                vis_path = base_path / "project_vision.md"
                
                # App Explanation
                ui.markdown(ABOUT_TEXT).classes('text-lg')

                # 3. System Flow Diagram
                ui.label('System Flow').classes('text-h6 font-bold mt-4 mb-2')
                if flow_path.exists():
                    ui.mermaid(flow_path.read_text()).classes('w-full border p-4 bg-gray-50')
                else:
                    ui.label(f'flow.mmd not found').classes('text-red')
                
                # 4. ERD (at bottom)
                ui.label('Data Model (ERD)').classes('text-h6 font-bold mt-6 mb-2')
                if erd_path.exists():
                    ui.mermaid(erd_path.read_text()).classes('w-full border p-4 bg-gray-50')
                else:
                    ui.label(f'erd.mmd not found').classes('text-red')
            except Exception as e:
                ui.label(f"Error loading docs: {e}").classes('text-red')

    # Initial Load
    ui.timer(0.1, refresh_db_list, once=True)

if __name__ in {"__main__", "__mp_main__"}:
    main()
    import os
    port = int(os.environ.get("PORT", 8080))
    # In production (Docker/Cloud Run), we must listen on 0.0.0.0
    # Reload defaults to True for dev, False if PROD is set
    is_prod = os.environ.get("PROD", "False").lower() == "true"
    ui.run(title="Learnify", host="0.0.0.0", port=port, reload=not is_prod)
