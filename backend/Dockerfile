FROM python:3.9

WORKDIR /app

# Install sqlite3 and other system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Create data directory and set proper permissions
RUN mkdir -p /app/data && chmod 755 /app/data

EXPOSE 8000

# Use module syntax to run the application
CMD ["python", "-m", "app.main"]