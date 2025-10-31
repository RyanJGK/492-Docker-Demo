FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rules engine script
COPY rules_engine.py .

# Make script executable
RUN chmod +x rules_engine.py

# Run the rules engine
CMD ["python", "rules_engine.py"]
