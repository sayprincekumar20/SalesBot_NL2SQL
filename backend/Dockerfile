# Use Python 3.11 slim image (smaller and supports modern typing)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install sqlite3 and other system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    curl \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements first (caching advantage)
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Ensure data directory exists with proper permissions
RUN mkdir -p /app/data && chmod 755 /app/data

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI with uvicorn (production style)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
