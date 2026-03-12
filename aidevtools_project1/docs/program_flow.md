# Program Flow & Architecture

## Overview

The application is designed as a decoupled system with a **FastAPI backend** handling data processing and business logic, and a **NiceGUI frontend** providing the user interface.

## Components

### 1. Frontend (NiceGUI)
- **Tech Stack**: Python (NiceGUI), HTML/CSS (Tailwind).
- **Functionality**:
  - Provides a tabbed interface for **Find**, **Pick**, **Study**, Chat, and Quizzes.
  - Communicates with the backend via REST API calls.
  - Manages local UI state (selected video, chat history, quiz progress).
  - Handles real-time updates (streaming chat).

### 2. Backend (FastAPI)
- **Tech Stack**: Python (FastAPI), SQLAlchemy, Google Gemini LLM.
- **Functionality**:
  - Exposes REST endpoints for all operations.
  - orchestration of external services.

### 3. Data & Services
- **YouTube Data**: A combination of three libraries handles all YouTube interactions:
  - [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api) — Fetches the list of available transcripts (languages, auto-generated vs. manual) and the full transcript text for a given video ID. This is the **primary library used to retrieve transcript content**.
  - [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) — Extracts rich video metadata (title, author/uploader, view count, duration) and powers topic-based video search from the frontend (`youtube_api.py`).
  - [`google-api-python-client`](https://github.com/googleapis/google-api-python-client) (YouTube Data API v3) — Used in the backend (`youtube_api.py`) for topic-based video search. Requires a `YOUTUBE_API_KEY`.
  - **MCP Docker container** (`mcp/youtube-transcript`) — An alternative transcript-fetching path used by `youtube_mcp.py`. It wraps `youtube-transcript-api` inside a Docker container and communicates via the Model Context Protocol (MCP).
- **Database**: 
  - **SQLite/DuckDB/Postgres**: Stores video metadata and generated content (transcripts, study guides, quizzes).
  - Uses SQLAlchemy ORM for abstraction.
- **LLM (Google Gemini)**:
  - Generates Study Guides from transcripts.
  - Generates Quizzes.
  - Provides an interactive Chat persona ("Tutor").

## Transcript Pipeline — Libraries & Code Flow

### Libraries used

| Library / Service | Installed via | Handles |
|---|---|---|
| [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api) | `pip install youtube-transcript-api` | **Primary transcript library.** Downloads the timed caption file that YouTube stores for every video and exposes each entry as a `FetchedTranscriptSnippet` with `start` (seconds), `duration`, and `text`. |
| [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) | `pip install yt-dlp` | Video **metadata** (title, author, view count, duration) and frontend **topic search** via the `ytsearchN:<query>` extractor syntax. |
| [`google-api-python-client`](https://github.com/googleapis/google-api-python-client) (YouTube Data API v3) | `pip install google-api-python-client` | Backend **topic search** — requires a `YOUTUBE_API_KEY`. |
| MCP Docker container (`mcp/youtube-transcript`) | `docker pull mcp/youtube-transcript` | **Alternative transcript path** via `youtube_mcp.py`. Runs `youtube-transcript-api` inside a container and communicates with the backend over the Model Context Protocol (MCP). |

### Step-by-step code flow (primary path)

```
API endpoint  →  list_transcripts_json(video_id)
                        │
                        ├─ get_video_metadata(video_id)   ← yt-dlp (metadata)
                        │
                        └─ YouTubeTranscriptApi().list(video_id)   ← youtube-transcript-api
                                  │
                                  │  for each transcript (language):
                                  ├─ get_transcript_text(transcript)
                                  │       transcript.fetch()  →  [ {text, start, duration}, … ]
                                  │       join all text fields  →  plain string
                                  │
                                  └─ get_transcript_with_timestamps(transcript)
                                          transcript.fetch()  →  [ {text, start, duration}, … ]
                                          _format_timestamp(start)  →  "M:SS" / "H:MM:SS"
                                          format each line as "[M:SS] text"
```

1. `list_transcripts_json` creates a `YouTubeTranscriptApi` instance (optionally with a proxy config).
2. `api.list(video_id)` returns all available caption tracks for the video (one per language, showing whether each is auto-generated or manual).
3. Calling `transcript.fetch()` on a track downloads the actual timed caption file from YouTube's servers; each snippet carries `start` (float seconds), `duration` (float seconds), and `text` (str).
4. `get_transcript_text` joins all `text` fields into a single plain string.
5. `get_transcript_with_timestamps` additionally reads `start` from each snippet, converts it via `_format_timestamp`, and prefixes every line with `[M:SS]`, matching YouTube's own transcript panel.

### MP4 / local video files

**Learnify currently does not process MP4 or other local video files.**  
All transcripts are retrieved directly from YouTube's servers — no audio download, decoding, or speech-to-text step is involved.

If local video support were added in the future, the typical approach would be:

| Step | Tool |
|---|---|
| Extract audio from MP4 | [`ffmpeg`](https://ffmpeg.org/) or [`moviepy`](https://zulko.github.io/moviepy/) |
| Transcribe audio to text | [OpenAI Whisper](https://github.com/openai/whisper) (`openai-whisper`) or a cloud STT API |

None of these libraries are currently in the project's dependencies.

---

## Key Workflows

### A. Find & Store
1. User enters a topic or Video ID in the **Find** tab.
2. Frontend requests `/api/v1/search` or `/api/v1/video/{id}`.
3. Backend performs the search (YouTube) and returns results.
4. User selects a video to "Store".
5. Backend fetches the full transcript and metadata, saving it to the database (`videos` and `transcripts` tables).

### B. Pick & Content Generation
1. User goes to **Pick** tab to view stored videos.
2. User selects a video.
3. If no Study Guide exists, User clicks "Generate Study Guide".
4. Backend sends the transcript to the LLM with a specific prompt.
5. LLM returns a structured markdown study guide, which is saved to the DB.
6. Similarly for Quizzes.

### C. Interactive Chat
1. User goes to **Chat** tab.
2. The Chat is context-aware, loaded with the study guide of the selected video (from the **Study** tab).
3. User sends a message.
4. Backend constructs a prompt including the Study Guide + Chat History + User Message.
5. Backend streams the LLM response back to the Frontend.
6. Frontend updates the UI in real-time.
