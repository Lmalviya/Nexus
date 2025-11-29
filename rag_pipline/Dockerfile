FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (cached layer if unchanged)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements FIRST (cached if unchanged)
# This is the key optimization - requirements change less frequently than code
COPY requirement.txt .

# Install dependencies (cached if requirements.txt unchanged)
# Use BuildKit cache mount to cache pip downloads
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirement.txt

# Copy source code LAST (changes frequently, won't invalidate above layers)
COPY . /app/rag_pipline

# Set python path
ENV PYTHONPATH=/app

# Command
CMD ["python", "-m", "rag_pipline.main"]