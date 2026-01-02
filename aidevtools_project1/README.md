# Learnify

This project consists of a FastAPI backend for processing YouTube transcripts and multiple frontend GUI options.

## Documentation

- **[Program Flow & Architecture](docs/program_flow.md)**: Detailed explanation of the system components and data flow.
- **[Project Vision](docs/project_vision.md)**: Roadmap and future goals.
- **[Database Schema](docs/erd.svg)**: Entity Relationship Diagram.
- **[System Flow](docs/flow.svg)**: High-level system interaction diagram.

## Project Structure

- **`backend/`**: FastAPI server, database logic, and CLI tools.
- **`frontend_nicegui/`**: **(Recommended)** Main NiceGUI web application.
- **`frontend_flet/`**: Flet-based desktop/web application.
- **`frontend_gradio/`**: Gradio-based web application.
- **`docs/`**: Documentation and diagrams.

## How to Run

### 1. Start the Backend
```bash
cd backend
uv run api.py
```
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Start the Frontend
**Option A: NiceGUI (Recommended)**
```bash
cd frontend_nicegui
uv run main.py
```

**Option B: Flet GUI (Desktop/Web)**
```bash
cd frontend_flet
uv run flet run --web main.py
```

**Option B: Gradio GUI (Web)**
```bash
cd frontend_gradio && uv run main.py
# with hot reload
cd frontend_gradio && uv run gradio main.py
```

## Testing

To run the unit tests for both backend and frontend, use the following command from the project root:

```bash
uv run pytest
```

## Cloud Deployment (Google Cloud Run)

The project includes `Dockerfile`s for both backend and frontend.

### 1. Deploy Backend API
```bash
cd backend
gcloud run deploy youtube-backend --source . --allow-unauthenticated
```
*Make sure to configure `POSTGRES_...` environment variables in the Cloud Run settings.*

### 2. Deploy Gradio Frontend
```bash
cd frontend_gradio
gcloud run deploy youtube-frontend --source . --allow-unauthenticated \
  --set-env-vars API_BASE_URL="[YOUR_BACKEND_URL]"
```

## Troubleshooting & Bypassing IP Blocks

If you receive errors like "YouTube is blocking requests from your IP", you can use a proxy (e.g., Webshare).

### Using a Proxy
Set the `HTTP_PROXY` environment variable before running the backend or CLI scripts:

```bash
export HTTP_PROXY="http://user:pass@proxy-host:port"
# Run backend
cd backend && uv run api.py
```

## Features

- Fetch YouTube video metadata and transcripts via API.
- **Full Transcript Support**: View and store full transcript text.
- Persist data to DuckDB or PostgreSQL.
- Interactive GUI for searching and viewing stored videos.
- Full OpenAPI specification provided.
