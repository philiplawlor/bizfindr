#!/bin/bash

# Exit on error
set -e

# Set default environment variables
export FLASK_APP=${FLASK_APP:-app}
export FLASK_ENV=${FLASK_ENV:-production}

# Function to check if a service is ready
wait_for_service() {
  local host=$1
  local port=$2
  local name=$3
  
  echo "Waiting for $name to be ready..."
  until nc -z $host $port; do
    echo "$name not ready yet. Retrying in 1 second..."
    sleep 1
  done
  echo "$name is ready!"
}

# Wait for required services
wait_for_service mongo 27017 "MongoDB"
wait_for_service redis 6379 "Redis"

# Initialize the database
echo "Initializing the database..."
python scripts/init_db.py

# Start the Flask application
echo "Starting Flask application..."
if [ "$FLASK_ENV" = "development" ]; then
    # Development mode with debugger and auto-reload
    echo "Running in development mode with auto-reload..."
    flask run --host=0.0.0.0 --port=5000 --debugger --reload
else
    # Production mode with Gunicorn
    echo "Running in production mode with Gunicorn..."
    gunicorn --bind 0.0.0.0:5000 \
             --workers 4 \
             --threads 2 \
             --timeout 120 \
             --worker-class=gthread \
             --log-level=info \
             --access-logfile - \
             --error-logfile - \
             --log-file=- \
             app:app
fi
