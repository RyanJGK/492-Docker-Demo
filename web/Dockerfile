FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck and other utilities
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY templates/ ./templates/

# Expose port
EXPOSE 8080

# Copy and use entrypoint script from mounted scripts volume
# The script will be available at /scripts/docker-entrypoint.sh via volume mount
ENTRYPOINT ["/bin/bash", "/scripts/docker-entrypoint.sh"]

# Run Flask application
CMD ["python", "app.py"]
