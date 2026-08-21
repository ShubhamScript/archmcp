FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy application source and data
COPY src/ ./src/
COPY data/ ./data/

# Environment defaults
ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONPATH=/app/src

EXPOSE 8000

# Run the ArchMCP Server
CMD ["python", "-m", "archmcp.main"]
