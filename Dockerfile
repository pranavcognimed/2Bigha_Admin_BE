FROM python:3.10-slim AS builder

# Set work directory
WORKDIR /app

# Install system dependencies for psycopg2 and GeoAlchemy
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies only (lighter image)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY . .

# Expose port
EXPOSE 8060

# Start the app (default command, overridden in docker-compose for dev)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8060"]