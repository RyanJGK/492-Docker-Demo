FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent.py .

ENV ALERTS_FILE=/shared/alerts.json \
    TRIAGE_FILE=/shared/triage.json \
    FEEDBACK_FILE=/shared/feedback.json

CMD ["python", "agent.py"]
