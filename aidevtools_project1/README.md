# YouTube Transcript Data Pipeline

This project provides tools to discover, fetch, and store YouTube video transcripts and metadata using DuckDB. It leverages the `youtube-transcript` MCP server for fetching full text and Python scripts for data management.

## Prerequisites

- [Docker](https://www.docker.com/) installed and running.
- [uv](https://github.com/astral-sh/uv) installed for Python dependency management.
- **YouTube Data API Key** (Required for topic search): Set the environment variable `YOUTUBE_API_KEY`.

## Setup

1.  **Pull the MCP Docker Image:**
    ```bash
    docker pull mcp/youtube-transcript
    ```

2.  **Install dependencies:**
    ```bash
    uv sync
    ```

3.  **Initialize Database (Optional):**
    The database `youtube_data.duckdb` is automatically created on first run with the `--upload` flag.

## Tools & Usage

### 1. List Transcripts & Metadata (`youtube_api.py`)

Discover available transcripts for a video or search for videos by topic. Can save metadata to DuckDB.

**Single Video:**
```bash
# Get JSON info for a video (supports URL or ID)
uv run youtube_api.py EMd3H0pNvSE

# Include full transcript text
uv run youtube_api.py EMd3H0pNvSE --transcript

# Upload metadata to DuckDB
uv run youtube_api.py EMd3H0pNvSE --upload
```

**Topic Search:**
```bash
# Search and process multiple videos
uv run youtube_api.py --topic "python tutorial" --max-results 3

# Search and upload metadata for all results
uv run youtube_api.py --topic "machine learning" --max-results 5 --upload
```

### 2. Fetch Full Transcript Text (`youtube_mcp.py`)

Fetches the full transcript text (using the MCP server) and can upload it to the database. Supports both full URLs and Video IDs.

```bash
# Show usage instructions
uv run youtube_mcp.py

# Fetch info only (no transcript)
uv run youtube_mcp.py EMd3H0pNvSE --info

# Fetch transcript text
uv run youtube_mcp.py "https://www.youtube.com/watch?v=VIDEO_ID" --transcript

# Fetch and UPLOAD full transcript to DuckDB
uv run youtube_mcp.py EMd3H0pNvSE --upload

# Verbose mode (debug logs)
uv run youtube_mcp.py EMd3H0pNvSE --upload --verbose
```

## Database Schema (`youtube_data.duckdb`)

**Table: `videos`**
- `video_id` (PK)
- `url`
- `title`
- `description`
- `author`
- `view_count`
- `duration` (ISO 8601 format, e.g., PT2M50S)
- `fetched_at`

**Table: `transcripts`**
- `video_id` (FK)
- `language`
- `language_code`
- `is_generated`
- `is_translatable`
- `transcript` (Full text content)

## Complete Workflow Example

1.  **Search for videos and save their metadata:**
    ```bash
    export YOUTUBE_API_KEY="your_api_key"
    uv run youtube_api.py --topic "DuckDB tutorial" --max-results 3 --upload
    ```

2.  **Pick a video ID from the output and download its full transcript:**
    ```bash
    uv run youtube_mcp.py CHY-7K_y8_g --upload
    ```

3.  **Query the data:**
    ```bash
    uv run python3 -c "import duckdb; con=duckdb.connect('youtube_data.duckdb'); con.sql('SELECT title, duration, length(transcript) as char_count FROM videos JOIN transcripts ON videos.video_id = transcripts.video_id').show()"
    ```