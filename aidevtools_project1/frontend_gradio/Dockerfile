FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
COPY main.py .

RUN uv pip install --system -r pyproject.toml

ENV PORT=8080
EXPOSE 8080

# Gradio specific env vars
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT=8080

CMD ["uv", "run", "main.py"]
