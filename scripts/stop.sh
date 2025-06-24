#!/bin/bash

# Exit on error
set -e

echo "Stopping BizFindr application..."

# Stop and remove containers, networks, and volumes
docker-compose -f ../docker-compose.yml down -v

echo ""
echo "BizFindr has been stopped."
echo "To start the application again, run: ./scripts/start.sh"
