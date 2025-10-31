FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the web application
COPY app.py .
COPY templates/ templates/

# Expose port 8080
EXPOSE 8080

# Run the Flask app
CMD ["python", "app.py"]
