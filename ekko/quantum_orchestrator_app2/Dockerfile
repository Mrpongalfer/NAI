# Dockerfile for Quantum Orchestrator
# Version: Simplified - Using pip instead of uv

# Stage 1: Build Environment
FROM python:3.11-slim as builder

# Install system dependencies needed for build (psycopg2 needs libpq-dev)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition files FIRST for caching
COPY pyproject.toml ./
# If you used Poetry and have a poetry.lock file, copy it too:
# COPY poetry.lock ./

# Ensure pip is up-to-date and install dependencies from pyproject.toml
# Using --no-cache-dir is often good practice in Docker
RUN pip install --upgrade pip wheel setuptools
RUN pip install --no-cache-dir .

# Stage 2: Production Environment
FROM python:3.11-slim as production

ARG APP_USER=appuser
ARG APP_GROUP=appgroup
ARG UID=1001
ARG GID=1001

# Install only necessary runtime system dependencies (e.g., libpq5 for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN groupadd -g ${GID} ${APP_GROUP} && \
    useradd -u ${UID} -g ${APP_GROUP} -m -s /bin/bash ${APP_USER}

WORKDIR /app

# Copy installed dependencies from builder stage's site-packages
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
# Copy necessary executables installed by dependencies (if any were placed here)
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code AFTER dependencies are installed
COPY . .

# Ensure the app directory is owned by the app user
RUN chown -R ${APP_USER}:${APP_GROUP} /app

USER ${APP_USER}

# Define default command (using python main.py as requested)
CMD ["python", "main.py"]
