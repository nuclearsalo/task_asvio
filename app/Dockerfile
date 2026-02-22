#Builder
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Create a virtual environment 
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

# Install dependencies
# We install GCC and libpq-dev temporarily just in case psycopg2 needs compiling
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && \
    pip install --no-cache-dir -r requirements.txt

#Runner
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install curl and libpq5
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Copy the built python packages
COPY --from=builder /opt/venv /opt/venv

# " Container must NOT run as root"
# Create a dedicated non-root user and group, and give them ownership of /app
RUN groupadd -r appgroup && useradd -r -g appgroup appuser && \
    chown -R appuser:appgroup /app

# Copy the actual application code
COPY --chown=appuser:appgroup main.py .

# Switch to the non-root user
USER appuser

# Expose the internal port the app runs on
EXPOSE 8000

# Add HEALTHCHECK
# Docker will periodically hit your /health endpoint. If it fails, Docker marks the container as unhealthy.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
