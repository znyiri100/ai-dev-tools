# Learnify Frontend
This is the NiceGUI-based frontend for the Learnify application.

## Setup

1. Install dependencies:
    ```bash
    uv sync
    ```

2. Configure Environment:
    Create a `.env` file or set environment variables:
    ```bash
    API_BASE_URL="http://localhost:8000"
    # Optional: Proxy for yt-dlp checks in frontend
    HTTP_PROXY_YT_DLP="http://user:pass@host:port"
    ```

3. Run the application:
    ```bash
    uv run main.py
    ```
