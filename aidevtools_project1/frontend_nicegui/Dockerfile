FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (using the standalone installer is robust)
RUN pip install uv

# Copy dependency files
COPY pyproject.toml .
# COPY uv.lock . # Uncomment if you have a lockfile and want reproducible builds

# Install dependencies into system python
# --system installs into the python environment directly since we are in a container
RUN uv pip install --system -r pyproject.toml

# Copy application code
COPY . .

# Expose port (Cloud Run defaults to 8080)
ENV PORT=8080
EXPOSE 8080

# Command to run the application
# We use 'python main.py' because main.py invokes ui.run()
# We assume main.py has been updated to listen on 0.0.0.0 and use $PORT
CMD ["python", "main.py"]
