# YouTube Transcript Manager GUI

A Flet-based desktop/web GUI for the YouTube Transcript API.

## Prerequisites

- The Backend API must be running (`cd backend && uv run api.py`).

## Setup

1.  **Install dependencies:**
    ```bash
    uv sync
    ```

## Usage

Run the application using the Flet CLI (this is the recommended method):
```bash
uv run flet run main.py
```

## Features

- **Search & Store:** Input a YouTube Video ID to fetch metadata and transcripts. Save them to the database.
- **Database:** View list of videos currently stored in the database.

## Troubleshooting

### Linux: Missing Shared Libraries (`libgstapp`, `libmpv`, etc.)

Flet requires several system libraries on Linux. Install them using:

```bash
sudo apt-get update
sudo apt-get install -y libgstreamer-plugins-base1.0-0 libmpv1 libgtk-3-0
```

