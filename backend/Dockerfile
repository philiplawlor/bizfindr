# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=2.1.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_NO_DEV=1 \
    FLASK_APP=wsgi:app \
    FLASK_ENV=production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && chmod +x /opt/poetry/bin/poetry \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Copy only requirements to cache them in docker layer
COPY pyproject.toml poetry.lock ./

# Install Python dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Create necessary directories
RUN mkdir -p /app/logs /app/static

# Copy project files (excluding what's in .dockerignore)
COPY . .

# Install dos2unix and convert line endings for shell scripts
RUN apt-get update && apt-get install -y --no-install-recommends dos2unix && \
    find /app/scripts -name "*.sh" -type f -print0 | xargs -0 dos2unix && \
    apt-get remove -y dos2unix && \
    rm -rf /var/lib/apt/lists/*

# Make the startup scripts executable
RUN chmod +x /app/scripts/*.sh

# Expose the port the app runs on
EXPOSE 5000 5555

# Create a simple start script directly in the container
RUN echo '#!/bin/sh\n\n# Exit on error\nset -e\n\n# Set default environment variables\nexport FLASK_APP=${FLASK_APP:-wsgi:app}\nexport FLASK_ENV=${FLASK_ENV:-production}\n\n# Wait for MongoDB\necho "Waiting for MongoDB to be ready..."\nuntil nc -z mongo 27017; do\n  echo "MongoDB not ready yet. Retrying in 1 second..."\n  sleep 1\ndone\n\n# Wait for Redis\necho "Waiting for Redis to be ready..."\nuntil nc -z redis 6379; do\n  echo "Redis not ready yet. Retrying in 1 second..."\n  sleep 1\ndone\n\n# Initialize the database\necho "Initializing the database..."\npython scripts/init_db.py\n\n# Start the Flask application\necho "Starting Flask application..."\nif [ "$FLASK_ENV" = "development" ]; then\n    echo "Running in development mode with auto-reload..."\n    flask run --host=0.0.0.0 --port=5000 --debugger --reload\nelse\n    echo "Running in production mode with Gunicorn..."\n    gunicorn --bind 0.0.0.0:5000 \
             --workers 4 \
             --threads 2 \
             --timeout 120 \
             --worker-class=gthread \
             --log-level=info \
             --access-logfile - \
             --error-logfile - \
             --log-file=- \
             --chdir /app \
             wsgi:app\nfi' > /start.sh && chmod +x /start.sh

# Default command (can be overridden in docker-compose)
CMD ["/start.sh"]
