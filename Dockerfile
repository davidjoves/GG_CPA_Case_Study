FROM python:3.12-slim

WORKDIR /app

# Install system deps (if you later need build tools, add them here)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8000"]

