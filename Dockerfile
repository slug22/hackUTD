# Use Python 3.9 as base image
FROM python:3.9-slim

# Set working directory
WORKDIR /hackUTD

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create data directory for JSON storage
RUN mkdir -p data

# Set environment variables
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Expose port
EXPOSE 8501
EXPOSE 5000

# Create an entrypoint script
RUN echo '#!/bin/bash\n\
python -m streamlit run main.py & \
python backend/app.py\n\
wait' > /app/entrypoint.sh && \
chmod +x /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]