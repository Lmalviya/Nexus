FROM python:3.10-slim

WORKDIR /app

# Install curl for Ollama installation
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy requirements and install Python dependencies
COPY requirement.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirement.txt

# Copy application code
COPY . /app/llms_host

# Set python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8002

# Create startup script that runs Ollama and the app
RUN echo '#!/bin/bash\n\
    # Start Ollama in the background\n\
    ollama serve &\n\
    OLLAMA_PID=$!\n\
    \n\
    # Wait for Ollama to be ready\n\
    echo "Waiting for Ollama to start..."\n\
    sleep 5\n\
    \n\
    # Pull primary model (llama3) - required for chat\n\
    echo "Pulling llama3 model..."\n\
    ollama pull llama3\n\
    \n\
    # Pull llava model in background (for vision tasks)\n\
    echo "Pulling llava model in background..."\n\
    (ollama pull llava &)\n\
    \n\
    echo "Primary model ready. Starting application..."\n\
    \n\
    # Start the FastAPI application\n\
    uvicorn llms_host.main:app --host 0.0.0.0 --port 8002\n\
    ' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]
