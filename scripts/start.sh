#!/bin/bash

# Exit on error
set -e

echo "Starting BizFindr application..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f "../backend/.env" ]; then
    echo "Creating .env file from .env.example..."
    cp ../backend/.env.example ../backend/.env
fi

# Start the application using Docker Compose
echo "Starting services with Docker Compose..."
docker-compose -f ../docker-compose.yml up -d --build

echo ""
echo "BizFindr is now running!"
echo "- Web interface: http://localhost:5000"
echo "- API: http://localhost:5000/api"
echo "- MongoDB: mongodb://localhost:27017/bizfindr"
echo ""
echo "To stop the application, run: ./scripts/stop.sh"
echo "To view logs, run: docker-compose logs -f"
