FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the agent script
COPY agent.py .

# Make script executable
RUN chmod +x agent.py

# Run the agent
CMD ["python", "agent.py"]
