FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    xvfb \
    git \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/output data/checkpoints data/logs data/credentials
RUN mkdir -p /home/chrome-profile

# Create non-root user
RUN useradd -m -u 1000 kiotviet
RUN chown -R kiotviet:kiotviet /app /home/chrome-profile

USER kiotviet

# Expose port (if needed for monitoring)
EXPOSE 8080

# Default command
CMD ["python", "scripts/kiotviet_run_all.py"]