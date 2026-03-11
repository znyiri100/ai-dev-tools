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
