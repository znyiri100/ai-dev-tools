# YouTube Transcript Manager

This project consists of a FastAPI backend for processing YouTube transcripts and a Flet-based frontend GUI.

## Project Structure

- **`backend/`**: FastAPI server, database logic, and CLI tools.
- **`frontend/`**: Flet-based desktop/web application.

## How to Run

### 1. Start the Backend
```bash
cd backend
uv run api.py
```
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Start the Frontend
```bash
cd frontend
uv run main.py
```

## Features

- Fetch YouTube video metadata and transcripts via API.
- Persist data to DuckDB or PostgreSQL.
- Interactive GUI for searching and viewing stored videos.
- Full OpenAPI specification provided.
