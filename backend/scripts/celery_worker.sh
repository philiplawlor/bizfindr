#!/bin/bash

# Exit on error
set -e

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
until nc -z redis 6379; do
  sleep 1
done

# Wait for MongoDB to be ready
echo "Waiting for MongoDB to be ready..."
until nc -z mongo 27017; do
  sleep 1
done

# Start the Celery worker
echo "Starting Celery worker..."
celery -A app.core.celery_app.celery_app worker \
    --loglevel=info \
    --hostname=worker@%h \
    --concurrency=4 \
    --prefetch-multiplier=1 \
    --max-tasks-per-child=100 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat \
    -O fair
