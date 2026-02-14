# NOCbRAIN Agents Dockerfile
# Base image for monitoring and security agents

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    net-tools \
    iputils-ping \
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r nocbrain && useradd -r -g nocbrain nocbrain

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY agents/requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy agent code
COPY agents/ .

# Create log directory
RUN mkdir -p /app/logs && \
    chown -R nocbrain:nocbrain /app

# Switch to non-root user
USER nocbrain

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import psutil; print('Agent healthy')" || exit 1

# Default command (can be overridden)
CMD ["python", "monitoring_agent.py"]
