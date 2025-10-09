# Dockerfile for PaperScope Streamlit App
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create demo config if not exists
RUN if [ ! -f paperscope/config.py ]; then \
    echo 'API_KEY = "demo_key"' > paperscope/config.py && \
    echo 'MODEL = "gemini-pro"' >> paperscope/config.py && \
    echo 'DB_PATH = "db.json"' >> paperscope/config.py; \
    fi

# Expose Streamlit default port
EXPOSE 8501

# Set environment variables
ENV DEMO_MODE=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run the app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
