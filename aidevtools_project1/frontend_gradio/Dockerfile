FROM python:3.11-slim

# Copy uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first
COPY pyproject.toml uv.lock ./

# Install dependencies
ENV UV_COMPILE_BYTECODE=1
RUN uv sync --frozen --no-install-project --no-dev

# Add the created virtual environment to the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy the application code
COPY main.py .
COPY youtube_api.py .

ENV PORT=8080
EXPOSE 8080

# Gradio specific env vars
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT=8080

CMD ["/app/.venv/bin/python", "main.py"]
