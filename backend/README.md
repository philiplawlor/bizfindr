# BizFindr Backend

This is the backend service for the BizFindr application, built with Flask, Celery, and MongoDB.

## Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Update the environment variables in `.env` as needed.

3. Install dependencies with Poetry:
   ```bash
   poetry install
   ```

## Development

Start the development server:
```bash
poetry run flask run
```

## Testing

Run tests with pytest:
```bash
poetry run pytest
```
