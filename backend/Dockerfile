# Multi-stage build to reduce image size
FROM python:3.11-slim as builder

WORKDIR /app

# Install only build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching (relative to root)
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage - minimal runtime image
FROM python:3.11-slim

WORKDIR /app

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Create necessary directories first
RUN mkdir -p ./data/raw ./data/processed ./data/chroma_db ./scripts

# Copy only necessary application files (relative to root)
COPY backend/app/ ./app/

# Copy data files (relative to root)
# Copy CSV file directly by name (source of truth - always in git)
# The app will generate interventions.json from CSV at startup if missing
COPY backend/data/raw/GPT_Input_DB*.csv ./data/raw/
# Don't copy processed JSON - let app generate it from CSV at startup
# This avoids Railway build issues with missing files
# chroma_db directory already created above with RUN mkdir -p
# Vector store will be empty but app handles this - it falls back to structured search

# Expose port
EXPOSE 8000

# Health check (uses PORT env var, defaults to 8000)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD sh -c 'python -c "import requests, os; port=os.getenv(\"PORT\", \"8000\"); requests.get(f\"http://localhost:{port}/health\")"'

# Run the application (Railway will override with startCommand from railway.json)
# Default to 8000 if PORT not set, but Railway provides PORT env var
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
