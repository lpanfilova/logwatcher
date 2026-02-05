FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY config.yaml ./config.yaml

WORKDIR /app/src
ENV CONFIG_PATH=/app/config.yaml

CMD ["python", "-u", "agent.py"]