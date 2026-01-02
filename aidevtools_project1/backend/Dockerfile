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
# Command to run the application
# Cloud Run expects the app to listen on the port defined by the PORT environment variable (default 8080)
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-8080}"]
