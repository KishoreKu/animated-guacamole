FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for MoviePy and Google Cloud libraries
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from backend folder
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project to ensure package structure is preserved
COPY . .

# Cloud Run expects the app to listen on the port defined by $PORT
CMD uvicorn backend.main:app --host 0.0.0.0 --port $PORT
