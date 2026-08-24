FROM python:3.12-slim

# Create dedicated non-root application user
RUN groupadd -g 10001 archmcp && \
    useradd -u 10001 -g archmcp -m -s /bin/bash archmcp

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

# Set file permissions for non-root execution
RUN chown -R archmcp:archmcp /app

# Environment defaults
ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

USER archmcp

EXPOSE 8000

# Health probe check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Run the Enterprise ArchMCP Server
CMD ["python", "-m", "archmcp.main"]
