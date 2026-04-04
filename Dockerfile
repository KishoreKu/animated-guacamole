FROM python:3.11-slim

WORKDIR /app

# Copy requirements from backend folder
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project to ensure package structure is preserved
COPY . .

# Cloud Run expects the app to listen on the port defined by $PORT
# We use backend.main:app because the package is 'backend'
CMD uvicorn backend.main:app --host 0.0.0.0 --port $PORT
