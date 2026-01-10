# YouTube Transcript Data Pipeline

This project provides tools to discover, fetch, and store YouTube video transcripts and metadata. It supports both local storage via **DuckDB** and remote storage via **PostgreSQL** (e.g., Supabase) using **SQLAlchemy** for database abstraction.

## Features

- **Database Agnostic:** Seamlessly switch between local DuckDB and remote Postgres.
- **MCP Integration:** Uses the `youtube-transcript` MCP server for robust transcript fetching.
- **SQLAlchemy ORM:** Clean data models and easy migrations.
- **Topic Search:** Find videos by topic and automatically store their metadata.

## Prerequisites

- [Docker](https://www.docker.com/) installed and running.
- [uv](https://github.com/astral-sh/uv) installed for Python dependency management.
- **YouTube Data API Key**: Required for topic search. Set the environment variable `YOUTUBE_API_KEY`.
- **Google API Key**: Required for Generative AI features (Gemini). Set `GOOGLE_API_KEY`.
- **(Optional) Postgres Credentials**: Required for remote storage.

## Setup

1.  **Pull the MCP Docker Image:**
    ```bash
    docker pull mcp/youtube-transcript
    ```

2.  **Install dependencies:**
    ```bash
    uv sync
    ```

3.  **Configure Database (Environment Variables):**
    By default, the project uses a local file named `youtube_data.duckdb`. To use a remote Postgres database, set the following:
    ```bash
    export POSTGRES_HOST="your-host.pooler.supabase.com"
    export POSTGRES_PORT="5432"
    export POSTGRES_DATABASE="your-db-name"
    export POSTGRES_USER="your-user"
    export POSTGRES_PASSWORD="your-password"
    ```

4.  **Configure Proxy (Optional):**
    If you are running this in an environment that requires a proxy (e.g., to avoid YouTube IP blocks), you can configure it using environment variables.

    *Generic Proxy:*
    ```bash
    export HTTP_PROXY="http://user:pass@host:port"
    ```

    *Webshare Proxy:*
    (If using Webshare.io credential rotation)
    ```bash
    export HTTP_PROXY_USER="your-username"
    export HTTP_PROXY_PASS="your-password"
    ```
    *Note: `HTTP_PROXY` takes precedence over Webshare credentials if both are set.*

## Tools & Usage

### 1. Database Management (`database.py` & `load_data.py`)

- `database.py`: Contains SQLAlchemy models and connection logic.
- `load_data.py`: Handles upserting video and transcript metadata.

### 2. List Transcripts & Metadata (`youtube_api.py`)

Discover available transcripts or search by topic.

**Single Video:**
```bash
# Get JSON info for a video
uv run youtube_api.py EMd3H0pNvSE

# Upload metadata to configured DB
uv run youtube_api.py EMd3H0pNvSE --upload
```

**Topic Search:**
```bash
# Search and upload metadata for multiple tutorials
uv run youtube_api.py --topic "python tutorial" --max-results 5 --upload
```

### 3. Fetch Full Transcript (`youtube_mcp.py`)

Fetches full transcript text via MCP and uploads it to the database.

```bash
# Fetch and UPLOAD full transcript
uv run youtube_mcp.py EMd3H0pNvSE --upload
```

### 4. Preview Data (`db_list.py`)

A utility to preview stored videos and transcripts in a tabular format.

```bash
uv run python db_list.py
```

### 5. HTTP API (`api.py`)

A FastAPI server that exposes the project's functionality as a REST API.

**Start the Server:**
```bash
uv run api.py
```

**Documentation:**
Once the server is running, you can access the interactive API documentation at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Redoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

**Key Endpoints:**
- `GET /api/v1/video/{video_id}`: Get video info live from YouTube.
- `POST /api/v1/video/{video_id}/store`: Fetch and store video data in DB.
- `GET /api/v1/db/videos`: List videos stored in DB.

**Run Tests:**
```bash
uv run -m pytest tests/test_api.py
```

## Database Schema

The pipeline manages two primary tables:

- **`videos`**: Stores core metadata (ID, title, author, view count, duration).
- **`transcripts`**: Stores transcript availability and full text content.

## Complete Workflow Example

1.  **Configure Environment:**
    ```bash
    export YOUTUBE_API_KEY="AIza..."
    export GOOGLE_API_KEY="AIza..."
    # (Optional) Export POSTGRES_HOST... for Supabase
    ```

2.  **Initialize & Load Metadata:**
    ```bash
    uv run youtube_api.py --topic "AI engineering" --max-results 3 --upload
    ```

3.  **Fetch Full Transcripts:**
    ```bash
    # Run for a specific video ID found in the search
    uv run youtube_mcp.py VIDEO_ID --upload
    ```

4.  **Verify Results:**
    ```bash
    uv run python db_list.py
    ```
