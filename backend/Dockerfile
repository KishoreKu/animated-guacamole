FROM python:3.11-slim

WORKDIR /app

# Copy the requirements file first for layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set environment variable for Python to find modules
ENV PYTHONPATH=/app

# Cloud Run expects the app to listen on the port defined by $PORT
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
