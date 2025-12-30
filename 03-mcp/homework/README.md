# DataTalks.club AI Developer Tools - MCP Homework (Module 3)

This repository contains the solution for the Module 3 homework on the Model Context Protocol (MCP).

## Project Progress & Answers

### Question 1: Create a New Project
- **Task:** Initialize project with `uv` and install `fastmcp`.
- **Finding:** The first hash in `uv.lock` for `fastmcp-2.14.1-py3-none-any.whl`.
- **Answer:** `sha256:fb3e365cc1d52573ab89caeba9944dd4b056149097be169bce428e011f0a57e5`

### Question 2: FastMCP Transport
- **Task:** Run the basic calculator MCP server and identify the transport.
- **Answer:** `STDIO`

### Question 3: Scrape Web Tool
- **Task:** Create a tool using `jina.ai` to scrape web pages and test on `https://github.com/alexeygrigorev/minsearch`.
- **Result:** The character count for the scraped content.
- **Answer:** `29184` (approx. 29-31k depending on the fetch)

### Question 4: Integrate the Tool
- **Task:** Use the AI assistant/MCP tool to count occurrences of "data" on `https://datatalks.club/`.
- **Result:** Counted 61 occurrences of "data" (case-insensitive).
- **Answer:** `61`

### Question 5: Implement Search
- **Task:** Index FastMCP documentation using `minsearch` and query for "demo".
- **Result:** The first result returned by the search engine.
- **Answer:** `examples/testing_demo/README.md`

## File Structure & Usage

### 1. Main MCP Server (`main.py`)
Contains the `FastMCP` server with the following tools:
- `add`: Basic calculator addition.
- `scrape_web`: Scrapes a URL using Jina Reader.

**Run the server:**
```bash
uv run main.py
```

### 2. Scraper Test (`test.py`)
Tests the `scrape_web` function against the minsearch repo.

**Run the test:**
```bash
uv run test.py
```

### 3. Question 4 Solver (`solve_q4.py`)
Automated script that uses `fetch_page_markdown` to scrape Datatalks.club and counts the word "data".

**Run the solver:**
```bash
uv run solve_q4.py
```

### 4. Search Implementation (`search.py`)
Downloads the FastMCP repository, indexes `.md/.mdx` files using `minsearch`, and performs a search for "demo".

**Run the search:**
```bash
uv run search.py
```

## Dependencies
- `fastmcp`
- `requests`
- `minsearch` (installed via `uv add minsearch`)

## How to Use

### 1. Interactive Development (MCP Inspector)
You can use the built-in MCP Inspector to test your tools via a web interface.

```bash
uv run fastmcp dev main.py
```
This will start a local server and open a debugger in your browser where you can manually run `add`, `scrape_web`, and `search_documentation`.

### 2. Configuration for AI Clients (e.g., Claude Desktop)
To use this server with Claude Desktop or other MCP-compliant clients, add the following to your configuration file (usually `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "homework-3": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/THIS/REPO/homework",
        "run",
        "main.py"
      ]
    }
  }
}
```
*Note: Replace `/ABSOLUTE/PATH/TO/THIS/REPO/homework` with the actual absolute path to your project directory.*

### 3. Configuration for Gemini CLI / Antigravity IDE
If you are using the Gemini CLI or Antigravity IDE, you can register this server in your `~/.gemini/settings.json` file.

Add the following entry to the `mcpServers` object:

```json
"homework-3": {
  "command": "uv",
  "args": [
    "--directory",
    "/home/me/tmp/DataTalks/03-mcp/homework",
    "run",
    "main.py"
  ]
}
```

Your `settings.json` should look something like this:

```json
{
  "mcpServers": {
    "homework-3": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/me/tmp/DataTalks/03-mcp/homework",
        "run",
        "main.py"
      ]
    }
  }
}
```


### 4. Python Client Example (`client.py`)
Demonstrates how to programmatically connect to the local MCP server using the `mcp` Python SDK. It lists available tools and invokes `search_documentation`.

**Run the client:**
```bash
uv run client.py
```
