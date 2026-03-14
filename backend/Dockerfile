FROM python:3.14-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first (better Docker layer caching)
COPY pyproject.toml .python-version ./

# Install dependencies into a venv
RUN uv sync --no-dev

# Copy application code
COPY app/ ./app/

RUN chown -R root:root /app

# Run via uv so it uses the venv automatically
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
