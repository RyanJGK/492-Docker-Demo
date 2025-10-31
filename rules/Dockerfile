FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY detect.py .

ENV DATA_DIR=/data \
    OUTPUT_DIR=/shared

CMD ["python", "detect.py"]
