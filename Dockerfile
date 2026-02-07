# backend/Dockerfile

# Use the official Python image:
FROM python:3.11-slim

# Set the working directory:
WORKDIR /app

# Install system dependencies:
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend Python files to /app root
COPY backend/ ./backend

# Copy frontend directory
COPY frontend ./frontend

# Expose the network port:
EXPOSE 8000

# Health check:
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \ 
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application:
CMD ["uvicorn", "./backend/main:app", "--host", "0.0.0.0", "--port", "8000"]
