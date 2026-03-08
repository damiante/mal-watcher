# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mal_watcher/ ./mal_watcher/
COPY main.py .

# Create directory for config files (users will mount these)
RUN mkdir -p /config

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command runs in daemon mode
# Users can override with --manual for one-time execution
ENTRYPOINT ["python", "main.py"]
CMD []
