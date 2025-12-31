FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (if needed, e.g. for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml .
# COPY uv.lock . # If you want locked versions

# Install dependencies using pip (simpler for Cloud Run than setting up uv in image, but uv is fine too)
# We'll use pip for compatibility with standard python images, or install uv.
# Let's use pip to read pyproject.toml if possible, or export requirements.
# UV is faster. Let's install uv.
RUN pip install uv

# Install dependencies
# We assume the project file structure. 
# We need to copy the backend code.
COPY . .

# Install dependencies into system python
RUN uv pip install --system -r pyproject.toml

# Expose port (Cloud Run defaults to 8080)
ENV PORT=8080
EXPOSE 8080

# Command to run the application
CMD ["uv", "run", "api.py"]
# Note: api.py uses uvicorn.run(..., port=8000). 
# We need api.py to respect the PORT env var or we change the CMD to run uvicorn directly.
# Better to run uvicorn directly to handle signals and ports properly.
CMD ["uv", "run", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
