FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if needed (e.g. for redis client or other libs)
# RUN apt-get update && apt-get install -y ...

# Copy requirements
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Copy source code
# We copy the current directory (llms_host) into /app/llms_host
# But wait, the context will likely be the parent directory or we need to structure it right.
# If we build from 'llms_host' directory, we copy . to .
# But python imports expect 'llms_host' package.
# It's better to run from the root workspace context usually.
# Let's assume we build from the 'llms_host' directory but we need to handle imports.
# If we run `uvicorn llms_host.main:app`, we need `llms_host` to be a package in python path.
# So we should copy the content of llms_host into /app/llms_host.

COPY . /app/llms_host

# Set python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8002

# Command
CMD ["uvicorn", "llms_host.main:app", "--host", "0.0.0.0", "--port", "8002"]
