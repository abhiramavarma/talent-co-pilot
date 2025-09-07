FROM python:3.9-slim

# Install system dependencies for ChromaDB
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create ChromaDB data directory
RUN mkdir -p /app/chroma_data

# Copy application code
COPY . .

# Set environment variables
ENV CHROMA_DB_PATH=/app/chroma_data
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
