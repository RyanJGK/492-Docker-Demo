FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./
COPY templates ./templates

ENV PORT=8080 \
    TRIAGE_FILE=/shared/triage.json \
    FEEDBACK_FILE=/shared/feedback.json

EXPOSE 8080

CMD ["python", "app.py"]
