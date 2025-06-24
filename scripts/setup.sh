#!/bin/bash

# Exit on error
set -e

echo "Setting up BizFindr development environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker and try again."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Create .env file from example if it doesn't exist
if [ ! -f "../backend/.env" ]; then
    echo "Creating .env file from .env.example..."
    cp ../backend/.env.example ../backend/.env
    
    # Generate a random API key if not set
    if ! grep -q "^API_KEY=" ../backend/.env; then
        echo "Generating API key..."
        echo "" >> ../backend/.env
        echo "# API Key for authentication" >> ../backend/.env
        echo "API_KEY=$(openssl rand -hex 16)" >> ../backend/.env
    fi
else
    echo ".env file already exists. Skipping creation."
fi

# Build and start the application
echo "Building and starting the application..."
cd ..
docker-compose build --no-cache
docker-compose up -d

# Initialize the database
echo "Initializing the database..."
docker-compose exec backend python scripts/init_db.py

echo ""
echo "Setup complete!"
echo "- Web interface: http://localhost:5000"
echo "- API: http://localhost:5000/api"
echo "- MongoDB: mongodb://localhost:27017/bizfindr"
echo ""
echo "To stop the application, run: ./scripts/stop.sh"
echo "To view logs, run: docker-compose logs -f"
