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

# Start the Celery beat scheduler
echo "Starting Celery beat scheduler..."
celery -A app.core.celery_app.celery_app beat \
    --loglevel=info \
    --pidfile=/tmp/celerybeat.pid \
    --scheduler=celery.beat:PersistentScheduler \
    --max-interval=300  # Check for new tasks every 5 minutes
